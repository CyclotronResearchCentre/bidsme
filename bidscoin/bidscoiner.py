#!/usr/bin/env python
"""
Converts ("coins") datasets in the sourcefolder to nifti / json / tsv datasets in the
bidsfolder according to the BIDS standard. Check and edit the bidsmap.yaml file to
your needs using the bidseditor.py tool before running this function. You can run
bidscoiner.py after all data is collected, or run / re-run it whenever new data has
been added to the source folder (presuming the scan protocol hasn't changed). If you
delete a (subject/) session folder from the bidsfolder, it will be re-created from the
sourcefolder the next time you run the bidscoiner.

Provenance information, warnings and error messages are stored in the
bidsfolder/code/bidscoin/bidscoiner.log file.
"""

import os
import glob
import re
import pandas as pd
import json
import dateutil.parser
import logging
try:
    from bidscoin import bids
except ImportError:
    import bids         # This should work if bidscoin was not pip-installed
    from Modules.MRI.selector import select as MRI_select

LOGGER = logging.getLogger('bidscoin')


def coin_dicom(session: str, bidsmap: dict, 
               bidsfolder: str, personals: dict, 
               subprefix: str, sesprefix: str) -> None:
    """
    Converts the session dicom-files into BIDS-valid nifti-files 
    in the corresponding bidsfolder and extracts personals 
    (e.g. Age, Sex) from the dicom header

    :param session:     The full-path name of the subject/session source folder
    :param bidsmap:     The full mapping heuristics from the bidsmap YAML-file
    :param bidsfolder:  The full-path name of the BIDS root-folder
    :param personals:   The dictionary with the personal information
    :param subprefix:   The prefix common for all source subject-folders
    :param sesprefix:   The prefix common for all source session-folders
    :return:            Nothing
    """

    if not bids.lsdirs(session):
        LOGGER.warning('No run subfolder(s) found in: ' + session)
        return

    TE = [None, None]

    # Get valid BIDS subject/session identifiers from the (first) dicom-header or from the session source folder

    """
    # Create the BIDS session-folder and a scans.tsv file
    scans_tsv = os.path.join(bidsses,
                             '{}{}_scans.tsv'
                             .format(subid, bids.add_prefix("_",sesid)))
    if os.path.exists(scans_tsv):
        scans_table = pd.read_csv(scans_tsv, sep='\t', index_col='filename')
    else:
        scans_table = pd.DataFrame(columns=['acq_time'], dtype='str')
        scans_table.index.name = 'filename'
    """

    # Process all the dicom run subfolders
    for runfolder in bids.lsdirs(session):
        cls = MRI_select(runfolder)
        if cls is None:
            LOGGER.warning("Unable to identify data in folder {}"
                           .format(runfolder))
            continue
        # Get a dicom-file
        dicomfile = cls(rec_path=runfolder, bidsmap=bidsmap[cls.__name__])
        LOGGER.info("Folder {} is {}"
                    .format(runfolder, dicomfile.type))
        if not dicomfile: 
            raise ValueError("Unable to load folder {}".format(runfolder))
        # run, modality, index = bids.get_matching_run(dicomfile, bidsmap)
        LOGGER.info(f'Processing: {runfolder}')
        run_id = bids.get_matching_run(dicomfile, bidsmap[cls.__name__])

        # Check if we should ignore this run
        if dicomfile.modality == dicomfile.ignoremodality:
            LOGGER.info('Modality {} ignored. Leaving out: {}'
                        .format(dicomfile.modality, runfolder))
            continue

        if dicomfile.modality == dicomfile.unknownmodality:
            LOGGER.warning("Unknown modality. Leaving out: {}"
                           .format(runfolder))
            raise KeyError("Unknown modality")
        run = bidsmap[cls.__name__][dicomfile.modality][run_id]
        dicomfile.Subject = bidsmap[cls.__name__]["subject"]
        dicomfile.Session = bidsmap[cls.__name__]["session"]

        sub = dicomfile.getSubId()
        ses = dicomfile.getSesId()
        LOGGER.debug("Subject: {}; Session: {}".format(sub, ses))
        bidsses = os.path.join(bidsfolder, sub, ses)
        bidsmodality = os.path.join(bidsses, dicomfile.modality)
        LOGGER.debug("Output path: {}".format(bidsses))
        LOGGER.debug("Modality path: {}".format(bidsmodality))
        os.makedirs(bidsmodality, exist_ok=True)

        # Loop over all files in given session
        dicomfile.index = -1
        while dicomfile.loadNextFile():
            dicomfile.update_labels(run)
            # Compose the BIDS filename using the matched run
            bidsname = dicomfile.get_bidsname()
            dicomfile.generateMeta()
            # plugin entry point for name and json adjustements

            # Check if file already exists (-> e.g. when a static runindex is used)
            if os.path.isfile(os.path.join(bidsmodality, bidsname + '.json')):
                LOGGER.warning(os.path.join(bidsmodality, bidsname) + '.* already exists -- check your results carefully!')
            if not dicomfile.convert(bidsmodality, bidsmap["Options"]):
                LOGGER.error("Failed to convert {} using {}"
                             .format(dicomfile.currentFile(),
                                     dicomfile.converter))
                raise ValueError("Convertion error")
            with open(os.path.join(bidsmodality, bidsname + '.json'), 'w') as f:
                js_dict = dicomfile.exportMeta()
                json.dump(js_dict, f, indent=2)
            continue

            # Add a dummy b0 bval- and bvec-file for any file without 
            # a bval/bvec file (e.g. sbref, b0 scans)
            """
            if modality == 'dwi':
                bvecfile = os.path.splitext(jsonfile)[0] + '.bvec'
                bvalfile = os.path.splitext(jsonfile)[0] + '.bval'
                if not os.path.isfile(bvecfile):
                    LOGGER.info('Adding dummy bvec file: ' + bvecfile)
                    with open(bvecfile, 'w') as bvec_fid:
                        bvec_fid.write('0\n0\n0\n')
                if not os.path.isfile(bvalfile):
                    LOGGER.info('Adding dummy bval file: ' + bvalfile)
                    with open(bvalfile, 'w') as bval_fid:
                        bval_fid.write('0\n')
            """

            # Parse the acquisition time from the json file or else from the dicom header (NB: assuming the dicom file represents the first aqcuisition)
            with open(jsonfile, 'r') as json_fid:
                data = json.load(json_fid)
            if 'AcquisitionTime' not in data:
                data['AcquisitionTime'] = bids.get_dicomfield('AcquisitionTime', dicomfile)
            acq_time = dateutil.parser.parse(data['AcquisitionTime'])
            niipath  = glob.glob(os.path.splitext(jsonfile)[0] + '.nii*')[0]    # Find the corresponding nifti file (there should be only one, let's not make assumptions about the .gz extension)
            niipath  = niipath.replace(bidsses+os.sep,'')                       # Use a relative path
            scans_table.loc[niipath, 'acq_time'] = '1900-01-01T' + acq_time.strftime('%H:%M:%S')

    # Write the scans_table to disk
    LOGGER.info('Writing acquisition time data to: ' + scans_tsv)
    scans_table.sort_values(by=['acq_time','filename'], inplace=True)
    scans_table.to_csv(scans_tsv, sep='\t', encoding='utf-8')

    # Search for the IntendedFor images and add them to the json-files. This has been postponed untill all modalities have been processed (i.e. so that all target images are indeed on disk)
    if bidsmap['DICOM']['fmap'] is not None:
        for fieldmap in bidsmap['DICOM']['fmap']:
            bidsname    = bids.get_bidsname(subid, sesid, 'fmap', fieldmap)
            niifiles    = []
            intendedfor = fieldmap['bids']['IntendedFor']

            # Search for the imaging files that match the IntendedFor search criteria
            if intendedfor:
                if intendedfor.startswith('<<') and intendedfor.endswith('>>'):
                    intendedfor = intendedfor[2:-2].split('><')
                elif not isinstance(intendedfor, list):
                    intendedfor = [intendedfor]
                for selector in intendedfor:
                    niifiles.extend([niifile.split(os.sep+subid+os.sep, 1)[1].replace('\\','/')                                                 # The path needs to use forward slashes instead of backward slashes
                                     for niifile in sorted(glob.glob(os.path.join(bidsses, f'**{os.sep}*{selector}*.nii*'))) if selector])      # Search in all runs using a relative path
            else:
                intendedfor = []

            if len(niifiles)<=1:
                niifiles = ''.join(niifiles)                                                                                                    # Only use a list for more than 1 file

            # Save the IntendedFor data in the json-files (account for multiple runs and dcm2niix suffixes inserted into the acquisition label)
            acqlabel = bids.get_bidsvalue(bidsname, 'acq')
            for jsonfile in glob.glob(os.path.join(bidsses, 'fmap', bidsname.replace('_run-1_', '_run-[0-9]*_') + '.json')) + \
                            glob.glob(os.path.join(bidsses, 'fmap', bidsname.replace('_run-1_', '_run-[0-9]*_').replace(acqlabel, acqlabel+'[CE][0-9]*') + '.json')):

                if niifiles:
                    LOGGER.info(f'Adding IntendedFor to: {jsonfile}')
                else:
                    LOGGER.warning(f"Empty 'IntendedFor' fieldmap value in {jsonfile}: the search for {intendedfor} gave no results")
                with open(jsonfile, 'r') as json_fid:
                    data = json.load(json_fid)
                data['IntendedFor'] = niifiles
                with open(jsonfile, 'w') as json_fid:
                    json.dump(data, json_fid, indent=4)

                # Catch magnitude2 and phase2 files produced by dcm2niix (i.e. magnitude1 & magnitude2 both in the same runfolder)
                if jsonfile.endswith('magnitude1.json') or jsonfile.endswith('phase1.json'):
                    jsonfile2 = jsonfile.rsplit('1.json',1)[0] + '2.json'
                    if os.path.isfile(jsonfile2):
                        with open(jsonfile2, 'r') as json_fid:
                            data = json.load(json_fid)
                        if 'IntendedFor' not in data:
                            if niifiles:
                                LOGGER.info(f'Adding IntendedFor to: {jsonfile2}')
                            else:
                                LOGGER.warning(f"Empty 'IntendedFor' fieldmap value in {jsonfile2}: the search for {intendedfor} gave no results")
                            data['IntendedFor'] = niifiles
                            with open(jsonfile2, 'w') as json_fid:
                                json.dump(data, json_fid, indent=4)

    # Collect personal data from the DICOM header: only from the first session (-> BIDS specification)
    dicomfile = bids.get_dicomfile(runfolder)
    personals['participant_id'] = subid
    if sesid:
        if 'session_id' not in personals:
            personals['session_id'] = sesid
        else:
            return
    Age = bids.get_dicomfield('PatientAge', dicomfile)          # A string of characters with one of the following formats: nnnD, nnnW, nnnM, nnnY
    if Age.endswith('D'):
        personals['age'] = str(int(float(Age.rstrip('D'))/365.2524))
    elif Age.endswith('W'):
        personals['age'] = str(int(float(Age.rstrip('W'))/52.1775))
    elif Age.endswith('M'):
        personals['age'] = str(int(float(Age.rstrip('M'))/12))
    elif Age.endswith('Y'):
        personals['age'] = str(int(float(Age.rstrip('Y'))))
    elif Age:
        personals['age'] = Age
    personals['sex']     = bids.get_dicomfield('PatientSex',     dicomfile)
    personals['size']    = bids.get_dicomfield('PatientSize',    dicomfile)
    personals['weight']  = bids.get_dicomfield('PatientWeight',  dicomfile)


def coin_par(session: str, bidsmap: dict, bidsfolder: str, personals: dict) -> None:
    """

    :param session:     The full-path name of the subject/session source folder
    :param bidsmap:     The full mapping heuristics from the bidsmap YAML-file
    :param bidsfolder:  The full-path name of the BIDS root-folder
    :param personals:   The dictionary with the personal information
    :return:            Nothing
    """

    pass


def coin_p7(session: str, bidsmap: dict, bidsfolder: str, personals: dict) -> None:
    """

    :param session:     The full-path name of the subject/session source folder
    :param bidsmap:     The full mapping heuristics from the bidsmap YAML-file
    :param bidsfolder:  The full-path name of the BIDS root-folder
    :param personals:   The dictionary with the personal information
    :return:            Nothing
    """

    pass


def coin_nifti(session: str, bidsmap: dict, bidsfolder: str, personals: dict) -> None:
    """

    :param session:     The full-path name of the subject/session source folder
    :param bidsmap:     The full mapping heuristics from the bidsmap YAML-file
    :param bidsfolder:  The full-path name of the BIDS root-folder
    :param personals:   The dictionary with the personal information
    :return:            Nothing
    """

    pass


def coin_filesystem(session: str, bidsmap: dict, bidsfolder: str, personals: dict) -> None:
    """

    :param session:     The full-path name of the subject/session source folder
    :param bidsmap:     The full mapping heuristics from the bidsmap YAML-file
    :param bidsfolder:  The full-path name of the BIDS root-folder
    :param personals:   The dictionary with the personal information
    :return:            Nothing
    """

    pass


def coin_plugin(session: str, bidsmap: dict, bidsfolder: str, personals: dict) -> None:
    """
    Run the plugin coiner to cast the run into the bids folder

    :param session:     The full-path name of the subject/session source folder
    :param bidsmap:     The full mapping heuristics from the bidsmap YAML-file
    :param bidsfolder:  The full-path name of the BIDS root-folder
    :param personals:   The dictionary with the personal information
    :return:            Nothing
    """

    # Input checks
    if not bidsmap['PlugIns']:
        return

    for plugin in bidsmap['PlugIns']:

        # Load and run the plugin-module
        module = bids.import_plugin(plugin)
        if 'bidscoiner_plugin' in dir(module):
            LOGGER.debug(f'Running: {plugin}.bidscoiner_plugin({session}, bidsmap, {bidsfolder}, personals)')
            module.bidscoiner_plugin(session, bidsmap, bidsfolder, personals)


def bidscoiner(rawfolder: str, bidsfolder: str, 
               subjects: tuple=(), force: bool=False, 
               participants: bool=False, 
               bidsmapfile: str='bidsmap.yaml', 
               subprefix: str='sub-', sesprefix: str='ses-') -> None:
    """
    Main function that processes all the subjects and session 
    in the sourcefolder and uses the bidsmap.yaml file in 
    bidsfolder/code/bidscoin to cast the data into the BIDS folder.

    :param rawfolder:       The root folder-name of the sub/ses/data/file 
                            tree containing the source data files
    :param bidsfolder:      The name of the BIDS root folder
    :param subjects:        List of selected subjects / participants 
                            (i.e. sub-# names / folders) to be processed 
                            (the sub- prefix can be removed). 
                            Otherwise all subjects in the sourcefolder 
                            will be selected
    :param force:           If True, subjects will be processed, regardless 
                            of existing folders in the bidsfolder. 
                            Otherwise existing folders will be skipped
    :param participants:    If True, subjects in particpants.tsv will 
                            not be processed (this could be used e.g. 
                            to protect these subjects from being reprocessed),
                            also when force=True
    :param bidsmapfile:     The name of the bidsmap YAML-file. If the bidsmap 
                            pathname is relative (i.e. no "/" in the name) 
                            then it is assumed to be located 
                            in bidsfolder/code/bidscoin
    :param subprefix:       The prefix common for all source subject-folders
    :param sesprefix:       The prefix common for all source session-folders
    :return:                Nothing
    """

    # Input checking & defaults
    rawfolder  = os.path.abspath(os.path.realpath(os.path.expanduser(rawfolder)))
    bidsfolder = os.path.abspath(os.path.realpath(os.path.expanduser(bidsfolder)))

    # Start logging
    bids.setup_logging(os.path.join(bidsfolder, 'code', 'bidscoin', 'bidscoiner.log'))
    LOGGER.info('')
    LOGGER.info(f'-------------- START BIDScoiner {bids.version()}: '
                'BIDS {bids.bidsversion()} ------------')
    LOGGER.info(f'>>> bidscoiner sourcefolder={rawfolder} '
                'bidsfolder={bidsfolder} subjects={subjects} '
                'force={force}'
                f' participants={participants} bidsmap={bidsmapfile} '
                'subprefix={subprefix} sesprefix={sesprefix}')

    # Create a code/bidscoin subfolder
    os.makedirs(os.path.join(bidsfolder,'code','bidscoin'), exist_ok=True)

    # Create a dataset description file if it does not exist
    dataset_file = os.path.join(bidsfolder, 'dataset_description.json')
    if not os.path.isfile(dataset_file):
        LOGGER.warning("Dataset description file 'dataset_description.json' "
                       "not found in '{}'".format(bidsfolder))

    # Create a README file if it does not exist
    readme_file = os.path.join(bidsfolder, 'README')
    if not os.path.isfile(readme_file):
        LOGGER.warning("Dataset readme file 'README' "
                       "not found in '{}'".format(bidsfolder))

    # Get the bidsmap heuristics from the bidsmap YAML-file
    bidsmap, _ = bids.load_bidsmap(bidsmapfile, 
                                   os.path.join(bidsfolder, 
                                                'code', 
                                                'bidscoin'))
    if not bidsmap:
        LOGGER.error(f'No bidsmap file found in {bidsfolder}. '
                     'Please run the bidsmapper first and / or '
                     'use the correct bidsfolder')
        return

    # Save options to the .bidsignore file
    bidsignore_items = [item.strip() 
                        for item in 
                        bidsmap['Options']['bidscoin']['bidsignore'].split(';')]
    LOGGER.info("Writing {} entries to {}.bidsignore"
                .format(bidsignore_items, bidsfolder))
    with open(os.path.join(bidsfolder,'.bidsignore'), 'w') as bidsignore:
        for item in bidsignore_items:
            bidsignore.write(item + '\n')

    # Get the table & dictionary of the subjects that have been processed
    participants_tsv  = os.path.join(bidsfolder, 'participants.tsv')
    participants_json = os.path.splitext(participants_tsv)[0] + '.json'
    if os.path.exists(participants_tsv):
        participants_table = pd.read_csv(participants_tsv, sep='\t')
        participants_table.set_index(['participant_id'],
                                     verify_integrity=True, 
                                     inplace=True)
    else:
        participants_table = pd.DataFrame()
        participants_table.index.name = 'participant_id'
    if os.path.exists(participants_json):
        with open(participants_json, 'r') as json_fid:
            participants_dict = json.load(json_fid)
    else:
        participants_dict = dict()

    # Get the list of subjects
    if not subjects:
        subjects = bids.lsdirs(rawfolder, subprefix + '*')
        if not subjects:
            LOGGER.warning('No subjects found in: {}*'
                           .format(os.path.join(rawfolder, subprefix)))
    else:
        # Make sure there is a "sub-" prefix
        subjects = [subprefix + re.sub(f'^{subprefix}', '', subject) 
                    for subject in subjects]
        subjects = [os.path.join(rawfolder,subject) 
                    for subject in subjects 
                    if os.path.isdir(os.path.join(rawfolder,subject))]

    # Loop over all subjects and sessions and convert them using the bidsmap entries
    for n, subject in enumerate(subjects, 1):

        if participants and subject in list(participants_table.index):
            LOGGER.info(f'Skipping subject: {subject} ({n}/{len(subjects)})')
            continue

        LOGGER.info('-------------------------------------')
        LOGGER.info(f'Coining subject ({n}/{len(subjects)}): {subject}')

        personals = dict()
        sessions = bids.lsdirs(subject, sesprefix + '*')
        if not sessions:
            sessions = [subject]
        for session in sessions:
            # Update / append the dicom mapping
            coin_dicom(session, bidsmap, bidsfolder, personals, subprefix, sesprefix)

            # Update / append the plugin mapping
            if bidsmap['PlugIns']:
                coin_plugin(session, bidsmap, bidsfolder, personals)

        # Store the collected personals in the participant_table
        for key in personals:

            # participant_id is the index of the participants_table
            assert 'participant_id' in personals
            if key == 'participant_id':
                continue

            # TODO: Check that only values that are consistent over sessions go in the participants.tsv file, otherwise put them in a sessions.tsv file

            if key not in participants_dict:
                participants_dict[key]  = dict(LongName     = 'Long (unabbreviated) name of the column',
                                               Description  = 'Description of the the column',
                                               Levels       = dict(Key='Value (This is for categorical variables: a dictionary of possible values (keys) and their descriptions (values))'),
                                               Units        = 'Measurement units. [<prefix symbol>]<unit symbol> format following the SI standard is RECOMMENDED',
                                               TermURL      = 'URL pointing to a formal definition of this type of data in an ontology available on the web')
            participants_table.loc[personals['participant_id'], key] = personals[key]

    # Write the collected data to the participant files
    LOGGER.info('Writing subject data to: ' + participants_tsv)
    participants_table.replace('','n/a').to_csv(participants_tsv, sep='\t', encoding='utf-8', na_rep='n/a')

    LOGGER.info('Writing subject data dictionary to: ' + participants_json)
    with open(participants_json, 'w') as json_fid:
        json.dump(participants_dict, json_fid, indent=4)

    LOGGER.info('-------------- FINISHED! ------------')
    LOGGER.info('')

    bids.reporterrors()


# Shell usage
if __name__ == "__main__":

    # Parse the input arguments and run bidscoiner(args)
    import argparse
    import textwrap
    parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=textwrap.dedent(__doc__),
            epilog='examples:\n'
            '  bidscoiner.py /project/foo/raw /project/foo/bids\n'
            '  bidscoiner.py -f /project/foo/raw /project/foo/bids'
            ' -p sub-009 sub-030\n ')
    parser.add_argument('sourcefolder',
                        help='The source folder containing the raw '
                        'data in sub-#/[ses-#]/run format '
                        '(or specify --subprefix and --sesprefix '
                        'for different prefixes)')
    parser.add_argument('bidsfolder',
                        help='The destination / output folder with '
                        'the bids data')
    parser.add_argument('-p','--participant_label',
                        help='Space seperated list of selected sub-# '
                        'names / folders to be processed (the sub- '
                        'prefix can be removed). Otherwise all subjects '
                        'in the sourcefolder will be selected', 
                        nargs='+')
    parser.add_argument('-f','--force',help='If this flag is given '
                        'subjects will be processed, regardless of '
                        'existing folders in the bidsfolder. '
                        'Otherwise existing folders will be skipped', 
                        action='store_true')
    parser.add_argument('-s','--skip_participants',
                        help='If this flag is given those subjects '
                        'that are in particpants.tsv will not be '
                        'processed (also when the --force flag is given). '
                        'Otherwise the participants.tsv table is ignored',
                        action='store_true')
    parser.add_argument('-b','--bidsmap',
                        help='The bidsmap YAML-file with the study '
                        'heuristics. If the bidsmap filename is relative '
                        '(i.e. no "/" in the name) then it is assumed to '
                        'be located in bidsfolder/code/bidscoin. '
                        'Default: bidsmap.yaml',
                        default='bidsmap.yaml')
    parser.add_argument('-n','--subprefix',
                        help="The prefix common for all the source "
                        "subject-folders. Default: 'sub-'", 
                        default='sub-')
    parser.add_argument('-m','--sesprefix',
                        help='The prefix common for all the source '
                        'session-folders. Default: "ses-"',
                        default='ses-')
    parser.add_argument('-v','--version',
                        help='Show the BIDS and BIDScoin version', 
                        action='version', 
                        version=f'BIDS-version:\t\t{bids.bidsversion()}'
                        '\nBIDScoin-version:\t{bids.version()}')
    args = parser.parse_args()

    bidscoiner(rawfolder = args.sourcefolder,
               bidsfolder = args.bidsfolder,
               subjects = args.participant_label,
               force = args.force,
               participants = args.skip_participants,
               bidsmapfile = args.bidsmap,
               subprefix = args.subprefix,
               sesprefix = args.sesprefix)
