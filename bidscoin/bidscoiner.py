#!/usr/bin/env python
"""
Converts ("coins") datasets in the rawfolder to nifti / json / tsv datasets in the
bidsfolder according to the BIDS standard. Check and edit the bidsmap.yaml file to
your needs before running this function. Provenance, warnings and error messages are
stored in the ../bidsfolder/code/bidscoiner.log file
"""

import os
import glob
import pandas as pd
import subprocess
import json
try:
    from bidscoin import bids
except ImportError:
    import bids         # This should work if bidscoin was not pip-installed


def coin_dicom(session, bidsmap, bidsfolder, personals):
    """
    Converts the session dicom-files into BIDS-valid nifti-files in the corresponding bidsfolder and
    extracts personals (e.g. Age, Sex) from the dicom header

    :param str session:    The full-path name of the subject/session source folder
    :param dict bidsmap:   The full mapping heuristics from the bidsmap YAML-file
    :param str bidsfolder: The full-path name of the BIDS root-folder
    :param dict personals: The dictionary with the personal information
    :return:               Nothing
    :rtype: NoneType
    """

    global logfile
    TE = [None, None]

    # Get a valid BIDS subject identifier from the (first) dicom-header or from the session source folder
    if bidsmap['DICOM']['participant_label'] and bidsmap['DICOM']['participant_label'].startswith('<<') and bidsmap['DICOM']['participant_label'].endswith('>>'):
        subid = 'sub-' + bids.get_dicomfield(bidsmap['DICOM']['participant_label'][2:-2], bids.get_dicomfile(bids.lsdirs(session)[0]))
    elif bidsmap['DICOM']['participant_label']:
        subid = 'sub-' + bidsmap['DICOM']['participant_label']
    else:
        subid = 'sub-' + session.rsplit(os.sep+'sub-',1)[1].split(os.sep+'ses-',1)[0]
    if subid == 'sub-':
        bids.printlog('Error: No valid subject identifier found for: ' + session, logfile)
        return

    # Get a BIDS session identifier from the (first) dicom-header or from the session source folder
    if bidsmap['DICOM']['session_label'] and bidsmap['DICOM']['session_label'].startswith('<<') and bidsmap['DICOM']['session_label'].endswith('>>'):
        sesid = 'ses-' + bids.get_dicomfield(bidsmap['DICOM']['session_label'][2:-2], bids.get_dicomfile(bids.lsdirs(session)[0]))
    elif bidsmap['DICOM']['session_label']:
        sesid = 'ses-' + bidsmap['DICOM']['session_label']
    elif os.sep+'ses-' in session:
        sesid = 'ses-' + session.rsplit(os.sep+'ses-')[1]
    else:
        sesid = ''

    # Create the BIDS session-folder
    bidsses = os.path.join(bidsfolder, subid, sesid)         # NB: This gives a trailing '/' if ses=='', but that should be ok
    os.makedirs(bidsses, exist_ok=True)

    # Process all the dicom series subfolders
    for series in bids.lsdirs(session):

        bids.printlog('Processing dicom-folder: ' + series, logfile)

        # Get the cleaned-up bids labels from a dicom-file and bidsmap
        dicomfile = bids.get_dicomfile(series)
        result    = bids.get_matching_dicomseries(dicomfile, bidsmap)
        series_   = result['series']
        modality  = result['modality']

        # Create the BIDS session/modality folder
        bidsmodality = os.path.join(bidsses, modality)
        os.makedirs(bidsmodality, exist_ok=True)

        # Compose the BIDS filename using the bids labels and run-index
        runindex = series_['run_index']
        if runindex.startswith('<<') and runindex.endswith('>>'):
            bidsname = bids.get_bidsname(subid, sesid, modality, series_, runindex[2:-2])
            bidsname = bids.increment_runindex(bidsmodality, bidsname)
        else:
            bidsname = bids.get_bidsname(subid, sesid, modality, series_, runindex)

        # Convert the dicom-files in the series folder to nifti's in the BIDS-folder
        command = '{path}dcm2niix {args} -f "{filename}" -o "{outfolder}" "{infolder}"'.format(
            path      = bidsmap['Options']['dcm2niix']['path'],
            args      = bidsmap['Options']['dcm2niix']['args'],
            filename  = bidsname,
            outfolder = bidsmodality,
            infolder  = series)
        bids.printlog('$ ' + command, logfile)
        process = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)         # TODO: investigate shell=False and capture_output=True
        bids.printlog(process.stdout.decode('utf-8'), logfile)
        if process.returncode != 0:
            errormsg = 'Error: Failed to process {} (errorcode {})'.format(series, process.returncode)
            bids.printlog(errormsg, logfile)
            continue

        # Replace uncropped output image with the cropped one
        if '-x y' in bidsmap['Options']['dcm2niix']['args']:
            for filename in sorted(glob.glob(os.path.join(bidsmodality, bidsname + '*_Crop_*'))):
                basepath, ext1 = os.path.splitext(filename)
                basepath, ext2 = os.path.splitext(basepath)                                                    # Account for .nii.gz files
                basepath       = basepath.rsplit('_Crop_',1)[0]
                newfilename    = basepath + ext2 + ext1
                bids.printlog('Found dcm2niix _Crop_ suffix, replacing original file\n{} ->\n{}'.format(filename, newfilename), logfile)
                os.replace(filename, newfilename)

        # Rename all files ending with _c%d, _e%d and _ph: These are produced by dcm2niix for multi-coil data, multi-echo data and phase data, respectively
        jsonfiles = []                                                                                          # Collect the associated json-files (for updating them later)
        for suffix in ('_c', '_e', '_ph'):
            for filename in sorted(glob.glob(os.path.join(bidsmodality, bidsname + suffix + '*'))):
                basepath, ext1  = os.path.splitext(filename)
                basepath, ext2  = os.path.splitext(basepath)                                                    # Account for .nii.gz files
                basepath, index = basepath.rsplit(suffix,1)
                index           = index.zfill(2)                                                                # Zero padd as specified in the BIDS-standard (assuming two digits is sufficient)

                # This is a special hack: dcm2niix does not add a _c suffix for the first coil -> add it when we encounter a *_c2 file
                if suffix=='_c' and int(index)==2:
                    filename_c1    = basepath + ext2 + ext1
                    newbasepath_c1 = bids.set_bidslabel(basepath, 'dummy', suffix.upper() + '1'.zfill(len(index)))  # --> append to acq-label, may need to be elaborated for future BIDS standards, supporting multi-coil data
                    newfilename_c1 = newbasepath_c1 + ext2 + ext1
                    if os.path.isfile(filename_c1) and not os.path.isfile(newfilename_c1):
                        bids.printlog('Found no dcm2niix {} suffix for coil #1, renaming\n{} ->\n{}'.format(suffix, filename_c1, newfilename_c1), logfile)
                        os.rename(filename_c1, newfilename_c1)
                        if ext1 == '.json':
                            jsonfiles.append(newbasepath_c1 + '.json')

                # Hack the basepath
                if suffix=='_e' and bids.set_bidslabel(basepath, 'echo') and index:
                    basepath = bids.set_bidslabel(basepath, 'echo', index)

                elif suffix=='_e' and basepath.rsplit('_',1)[1] in ['magnitude1','magnitude2'] and index:       # i.e. modality == 'fmap'
                    basepath = basepath[0:-1] + index                                                           # basepath: *_magnitude1_e[index] -> *_magnitude[index]
                    # Read the echo times that need to be added to the json-file (see below)
                    if os.path.splitext(filename)[1] == '.json':
                        with open(filename, 'r') as json_fid:
                            data = json.load(json_fid)
                        TE[int(index)-1] = data['EchoTime']
                        bids.printlog('Reading EchoTime{} = {} from: {}'.format(index,data['EchoTime'],filename), logfile)
                elif suffix=='_e' and basepath.rsplit('_',1)[1]=='phasediff' and index:                         # i.e. modality == 'fmap'
                    pass

                elif suffix=='_ph' and basepath.rsplit('_',1)[1] in ['phase1','phase2'] and index:              # i.e. modality == 'fmap' (TODO: untested)
                    basepath = basepath[0:-1] + index                                                           # basepath: *_phase1_e[index] -> *_phase[index]
                    bids.printlog('WARNING: Untested dcm2niix "_ph"-filetype: ' + basepath, logfile)

                else:
                    basepath = bids.set_bidslabel(basepath, 'dummy', suffix.upper() + index)                    # --> append to acq-label, may need to be elaborated for future BIDS standards, supporting multi-coil data

                # Save the file with a new name
                if runindex.startswith('<<') and runindex.endswith('>>'):
                    newbidsname = bids.increment_runindex(bidsmodality, os.path.basename(basepath), ext2 + ext1)  # Update the runindex now that the acq-label has changed
                else:
                    newbidsname = os.path.basename(basepath)
                newfilename = os.path.join(bidsmodality, newbidsname + ext2 + ext1)
                bids.printlog('Found dcm2niix {} suffix, renaming\n{} ->\n{}'.format(suffix, filename, newfilename), logfile)
                os.rename(filename, newfilename)
                if ext1 == '.json':
                    jsonfiles.append(os.path.join(bidsmodality, newbidsname + '.json'))

        # Loop over and adapt all the newly produced json files (every nifti file comes with a json file)
        if not jsonfiles:
            jsonfiles = [os.path.join(bidsmodality, bidsname + '.json')]

        for jsonfile in jsonfiles:

            # Add a dummy b0 bval- and bvec-file for any file without a bval/bvec file (e.g. sbref, b0 scans)
            if modality == 'dwi':
                bvecfile = os.path.splitext(jsonfile)[0] + '.bvec'
                bvalfile = os.path.splitext(jsonfile)[0] + '.bval'
                if not os.path.isfile(bvecfile):
                    with open(bvecfile, 'w') as bvec_fid:
                        bids.printlog('Adding dummy bvec file: ' + bvecfile, logfile)
                        bvec_fid.write('0\n0\n0\n')
                if not os.path.isfile(bvalfile):
                    with open(bvalfile, 'w') as bval_fid:
                        bids.printlog('Adding dummy bval file: ' + bvalfile, logfile)
                        bval_fid.write('0\n')

            # Add the TaskName to the func json-file
            elif modality == 'func':
                with open(jsonfile, 'r') as json_fid:
                    data = json.load(json_fid)
                if not 'TaskName' in data:
                    bids.printlog('Adding TaskName to: ' + jsonfile, logfile)
                    with open(jsonfile, 'w') as json_fid:
                        data['TaskName'] = series_['task_label']
                        json.dump(data, json_fid, indent=4)

            # Add the EchoTime(s) used to create the difference image to the fmap json-file. NB: This assumes the magnitude series have already been parsed (i.e. their nifti's had an _e suffix) -- This is normally the case for Siemens (phase-series being saved after the magnitude series
            elif modality == 'fmap':
                if series_['suffix'] == 'phasediff':
                    bids.printlog('Adding EchoTime1 and EchoTime2 to: ' + jsonfile, logfile)
                    with open(jsonfile, 'r') as json_fid:
                        data = json.load(json_fid)
                    data['EchoTime1'] = TE[0]
                    data['EchoTime2'] = TE[1]
                    with open(jsonfile, 'w') as json_fid:
                        json.dump(data, json_fid, indent=4)
                    if TE[0]>TE[1]:
                        bids.printlog('WARNING: EchoTime1 > EchoTime2 in: ' + jsonfile, logfile)

    # Search for the IntendedFor images and add them to the json-files. This has been postponed untill all modalities have been processed (i.e. so that all target images are indeed on disk)
    if bidsmap['DICOM']['fmap'] is not None:
        for fieldmap in bidsmap['DICOM']['fmap']:
            if 'IntendedFor' in fieldmap and fieldmap['IntendedFor']:
                jsonfile = os.path.join(bidsses, 'fmap', bids.get_bidsname(subid, sesid, 'fmap', fieldmap, '1') + '.json')       # TODO: Assumes that there is only 1 fieldmap acquired for each bidsmap entry / series
                if not os.path.isfile(jsonfile):
                    continue
                intendedfor = fieldmap['IntendedFor']
                if intendedfor.startswith('<<') and intendedfor.endswith('>>'):
                    intendedfor = intendedfor[2:-2].split('><')
                else:
                    intendedfor = [intendedfor]
                with open(jsonfile, 'r') as json_fid:
                    data = json.load(json_fid)
                niifiles = [niifile.split(os.sep+subid+os.sep, 1)[1] for niifile in sorted(glob.glob(os.path.join(bidsses, '**'+os.sep+'*' + '*'.join(intendedfor) + '*.nii*')))]     # Use a relative path
                data['IntendedFor'] = niifiles
                bids.printlog('Adding IntendedFor to: ' + jsonfile, logfile)
                with open(jsonfile, 'w') as json_fid:
                    json.dump(data, json_fid, indent=4)

                # Catch magnitude2 files produced by dcm2niix
                if jsonfile.endswith('magnitude1.json'):
                    jsonfile2 = jsonfile.rsplit('1.json',1)[0] + '2.json'
                    if os.path.isfile(jsonfile2):
                        with open(jsonfile2, 'r') as json_fid:
                            data = json.load(json_fid)
                        data['IntendedFor'] = niifiles
                        bids.printlog('Adding IntendedFor to: ' + jsonfile2, logfile)
                        with open(jsonfile2, 'w') as json_fid:
                            json.dump(data, json_fid, indent=4)

    # Collect personal data from the DICOM header
    dicomfile                   = bids.get_dicomfile(series)
    personals['participant_id'] = subid
    if sesid:
        personals['session_id'] = sesid                                                     # TODO: Check if this can be in the participants.tsv file according to BIDS
    personals['age']            = bids.get_dicomfield('PatientAge',    dicomfile)
    personals['sex']            = bids.get_dicomfield('PatientSex',    dicomfile)
    personals['size']           = bids.get_dicomfield('PatientSize',   dicomfile)
    personals['weight']         = bids.get_dicomfield('PatientWeight', dicomfile)


def coin_par(session, bidsmap, bidsfolder, personals):
    """

    :param str session:    The full-path name of the subject/session source folder
    :param dict bidsmap:   The full mapping heuristics from the bidsmap YAML-file
    :param str bidsfolder: The full-path name of the BIDS root-folder
    :param dict personals: The dictionary with the personal information
    :return:               Nothing
    :rtype: NoneType
    """

    global logfile
    bids.printlog('coin_par is WIP!!!', logfile)


def coin_p7(session, bidsmap, bidsfolder, personals):
    """

    :param str session:    The full-path name of the subject/session source folder
    :param dict bidsmap:   The full mapping heuristics from the bidsmap YAML-file
    :param str bidsfolder: The full-path name of the BIDS root-folder
    :param dict personals: The dictionary with the personal information
    :return:               Nothing
    :rtype: NoneType
    """

    global logfile
    bids.printlog('coin_p7 is WIP!!!', logfile)


def coin_nifti(session, bidsmap, bidsfolder, personals):
    """

    :param str session:    The full-path name of the subject/session source folder
    :param dict bidsmap:   The full mapping heuristics from the bidsmap YAML-file
    :param str bidsfolder: The full-path name of the BIDS root-folder
    :param dict personals: The dictionary with the personal information
    :return:               Nothing
    :rtype: NoneType
    """

    global logfile
    bids.printlog('coin_nifti is WIP!!!', logfile)


def coin_filesystem(session, bidsmap, bidsfolder, personals):
    """

    :param str session:    The full-path name of the subject/session source folder
    :param dict bidsmap:   The full mapping heuristics from the bidsmap YAML-file
    :param str bidsfolder: The full-path name of the BIDS root-folder
    :param dict personals: The dictionary with the personal information
    :return:               Nothing
    :rtype: NoneType
    """

    global logfile
    bids.printlog('coin_filesystem is WIP!!!', logfile)


def coin_plugin(session, bidsmap, bidsfolder, personals):
    """
    Run the plugin coiner to cast the series into the bids folder

    :param str session:    The full-path name of the subject/session source folder
    :param dict bidsmap:   The full mapping heuristics from the bidsmap YAML-file
    :param str bidsfolder: The full-path name of the BIDS root-folder
    :param dict personals: The dictionary with the personal information
    :return:               Nothing
    :rtype: NoneType
    """

    from importlib import import_module
    global logfile

    # Import and run the plugins
    for pluginfunction in bidsmap['PlugIn']:
        plugin = import_module(os.path.join(__file__,'plugins', pluginfunction))
        # TODO: check first if the plug-in function exist
        plugin.bidscoin(session, bidsmap, bidsfolder, personals)


def bidscoiner(rawfolder, bidsfolder, subjects=(), force=False, participants=False, bidsmapfile='code'+os.sep+'bidsmap.yaml'):
    """
    Main function that processes all the subjects and session in the rawfolder and uses the
    bidsmap.yaml file in bidsfolder/code to cast the data into the BIDS folder.

    :param str rawfolder:     The root folder-name of the sub/ses/data/file tree containing the source data files
    :param str bidsfolder:    The name of the BIDS root folder
    :param list subjects:     List of selected subjects / participants (i.e. sub-# names / folders) to be processed (the sub- prefix can be removed). Otherwise all subjects in the rawfolder will be selected
    :param bool force:        If True, subjects will be processed, regardless of existing folders in the bidsfolder. Otherwise existing folders will be skipped
    :param bool participants: If True, subjects in particpants.tsv will not be processed (this could be used e.g. to protect these subjects from being reprocessed), also when force=True
    :param str bidsmapfile:   The name of the bidsmap YAML-file. If the bidsmap pathname is relative (i.e. no "/" in the name) then it is assumed to be located in bidsfolder/code/
    :return:                  Nothing
    :rtype: NoneType
    """

    # Input checking
    rawfolder  = os.path.abspath(os.path.expanduser(rawfolder))
    bidsfolder = os.path.abspath(os.path.expanduser(bidsfolder))
    os.makedirs(os.path.join(bidsfolder,'code'), exist_ok=True)
    if not os.path.isfile(os.path.join(bidsfolder,'.bidsignore')):
        with open(os.path.join(bidsfolder,'.bidsignore'), 'w') as bidsignore:
            bidsignore.write(bids.unknownmodality + os.sep)

    # Start logging
    global logfile
    logfile = os.path.join(bidsfolder, 'code', 'bidscoiner.log')
    bids.printlog('------------ START BIDScoiner {ver}: BIDS {bidsver} ------------\n>>> bidscoiner rawfolder={arg1} bidsfolder={arg2} subjects={arg3} force={arg4} participants={arg5} bidsmap={arg6}'.format(
        ver=bids.version(), bidsver=bids.bidsversion(), arg1=rawfolder, arg2=bidsfolder, arg3=subjects, arg4=force, arg5=participants, arg6=bidsmapfile), logfile)

    # Create a dataset description file if it does not exist
    dataset_file = os.path.join(bidsfolder, 'dataset_description.json')
    if not os.path.isfile(dataset_file):
        dataset_description = {"Name":                  "REQUIRED. Name of the dataset",
                               "BIDSVersion":           bids.bidsversion(),
                               "License":               "RECOMMENDED. What license is this dataset distributed under?. The use of license name abbreviations is suggested for specifying a license",
                               "Authors":               ["OPTIONAL. List of individuals who contributed to the creation/curation of the dataset"],
                               "Acknowledgements":      "OPTIONAL. List of individuals who contributed to the creation/curation of the dataset",
                               "HowToAcknowledge":      "OPTIONAL. Instructions how researchers using this dataset should acknowledge the original authors. This field can also be used to define a publication that should be cited in publications that use the dataset",
                               "Funding":               ["OPTIONAL. List of sources of funding (grant numbers)"],
                               "ReferencesAndLinks":    ["OPTIONAL. List of references to publication that contain information on the dataset, or links"],
                               "DatasetDOI":            "OPTIONAL. The Document Object Identifier of the dataset (not the corresponding paper)"}
        bids.printlog('Creating dataset description file: ' + dataset_file, logfile)
        with open(dataset_file, 'w') as fid:
            json.dump(dataset_description, fid, indent=4)

    # Create a README file if it does not exist
    readme_file = os.path.join(bidsfolder, 'README')
    if not os.path.isfile(readme_file):
        bids.printlog('Creating README file: ' + readme_file, logfile)
        with open(readme_file, 'w') as fid:
            fid.write('A free form text ( README ) describing the dataset in more details that SHOULD be provided')

    # Get the bidsmap heuristics from the bidsmap YAML-file
    bidsmap = bids.get_heuristics(bidsmapfile, os.path.join(bidsfolder,'code'), logfile=logfile)

    # Get the table with subjects that have been processed
    participants_file = os.path.join(bidsfolder, 'participants.tsv')
    if os.path.exists(participants_file):
        participants_table = pd.read_table(participants_file)
    else:
        participants_table = pd.DataFrame(columns = ['participant_id'])

    # Get the list of subjects
    if not subjects:
        subjects = bids.lsdirs(rawfolder, 'sub-*')
    else:
        subjects = ['sub-' + subject.lstrip('sub-') for subject in subjects]        # Make sure there is a "sub-" prefix
        subjects = [os.path.join(rawfolder,subject) for subject in subjects if os.path.isdir(os.path.join(rawfolder,subject))]

    # Loop over all subjects and sessions and convert them using the bidsmap entries
    for subject in subjects:

        if participants and subject in list(participants_table.participant_id): continue

        personals = dict()
        sessions  = bids.lsdirs(subject, 'ses-*')
        if not sessions:
            sessions = subject
        for session in sessions:

            # Check if we should skip the session-folder
            if not force and os.path.isdir(session.replace(rawfolder, bidsfolder)):
                continue

            # Update / append the dicom mapping
            if bidsmap['DICOM']:
                coin_dicom(session, bidsmap, bidsfolder, personals)

            # Update / append the PAR/REC mapping
            if bidsmap['PAR']:
                coin_par(session, bidsmap, bidsfolder, personals)

            # Update / append the P7 mapping
            if bidsmap['P7']:
                coin_p7(session, bidsmap, bidsfolder, personals)

            # Update / append the nifti mapping
            if bidsmap['Nifti']:
                coin_nifti(session, bidsmap, bidsfolder, personals)

            # Update / append the file-system mapping
            if bidsmap['FileSystem']:
                coin_filesystem(session, bidsmap, bidsfolder, personals)

            # Update / append the plugin mapping
            if bidsmap['PlugIn']:
                coin_plugin(session, bidsmap, bidsfolder, personals)

        # Write the collected personals to the participants_file
        if personals:
            for key in personals:
                if key not in participants_table.columns:
                    participants_table[key] = None
            participants_table = participants_table.append(personals, ignore_index=True, verify_integrity=True)
            bids.printlog('Writing subject data to: ' + participants_file, logfile)
            participants_table.to_csv(participants_file, sep='\t', encoding='utf-8', na_rep='n/a', index=False)

    bids.printlog('------------ FINISHED! ------------', logfile)


# Shell usage
if __name__ == "__main__":

    # Parse the input arguments and run bidscoiner(args)
    import argparse
    import textwrap
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=textwrap.dedent(__doc__),
                                     epilog='examples:\n'
                                            '  bidscoiner.py /project/raw /project/bids\n'
                                            '  bidscoiner.py -f /project/raw /project/bids -p sub-009 sub-030\n ')
    parser.add_argument('sourcefolder',             help='The source folder containing the raw data in sub-#/ses-#/series format')
    parser.add_argument('bidsfolder',               help='The destination folder with the bids data structure')
    parser.add_argument('-p','--participant_label', help='Space seperated list of selected sub-# names / folders to be processed (the sub- prefix can be removed). Otherwise all subjects in the sourcefolder will be selected', nargs='+')
    parser.add_argument('-f','--force',             help='If this flag is given subjects will be processed, regardless of existing folders in the bidsfolder. Otherwise existing folders will be skipped', action='store_true')
    parser.add_argument('-s','--skip_participants', help='If this flag is given those subjects that are in particpants.tsv will not be processed (also when the --force flag is given). Otherwise the participants.tsv table is ignored', action='store_true')
    parser.add_argument('-b','--bidsmap',           help='The bidsmap YAML-file with the study heuristics. If the bidsmap filename is relative (i.e. no "/" in the name) then it is assumed to be located in bidsfolder/code/. Default: bidsmap.yaml', default='bidsmap.yaml')
    args = parser.parse_args()

    bidscoiner(rawfolder=args.sourcefolder, bidsfolder=args.bidsfolder, subjects=args.participant_label, force=args.force, participants=args.skip_participants, bidsmapfile=args.bidsmap)
