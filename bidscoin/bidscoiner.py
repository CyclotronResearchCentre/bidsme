#!/usr/bin/env python
"""
Converts ("coins") datasets in the sourcefolder to nifti/json/tsv datasets 
in the bidsfolder according to the BIDS standard. Check and edit 
the bidsmap.yaml file to your needs using the bidseditor.py tool 
before running this function. You can run bidscoiner.py after all data 
is collected, or run / re-run it whenever new data has been added 
to the source folder (presuming the scan protocol hasn't changed). 
If you delete a (subject/) session folder from the bidsfolder, 
it will be re-created from the sourcefolder the next time you run 
the bidscoiner.

Provenance information, warnings and error messages are stored in the
bidsfolder/code/bidscoin/bidscoiner.log file.
"""

import os
import sys
import re
import shutil
import pandas as pd
import json
import logging
import tempfile

try:
    from bidscoin import bids
except ImportError:
    import bids         # This should work if bidscoin was not pip-installed
    from tools import tools
    from tools import plugins
    from Modules.MRI.selector import select as MRI_select

LOGGER = logging.getLogger('bidscoin')
tmpDir = None


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
            LOGGER.error("Unknown modality. Leaving out: {}"
                         .format(runfolder))
            raise KeyError("Unknown modality")

        if dicomfile.modality == "":
            LOGGER.error("Empty modality. Leaving out: {}"
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

        dicomfile.sub_BIDSvalues["participant_id"] = sub

        # plugin entry point for name and json adjustements
        plugins.RunPlugin("SessionEP", dicomfile)

        sub_tsv = os.path.join(tmpDir,
                               'participants.tsv'
                               )
        if os.path.isfile(sub_tsv):
            with open(sub_tsv, "a") as f:
                f.write(dicomfile.sub_BIDSfields.GetLine(
                    dicomfile.sub_BIDSvalues))
                f.write('\n')
        else:
            with open(sub_tsv, "w") as f:
                f.write(dicomfile.sub_BIDSfields.GetHeader())
                f.write('\n')
                f.write(dicomfile.sub_BIDSfields.GetLine(
                    dicomfile.sub_BIDSvalues))
                f.write('\n')
            dicomfile.sub_BIDSfields.DumpDefinitions(
                    tools.change_ext(sub_tsv,"json"))

        # Loop over all files in given session
        dicomfile.index = -1
        while dicomfile.loadNextFile():
            dicomfile.update_labels(run)
            # Compose the BIDS filename using the matched run
            bidsname = dicomfile.get_bidsname()
            dicomfile.generateMeta()

            # Check if file already exists 
            if os.path.isfile(os.path.join(bidsmodality, bidsname + '.json')):
                LOGGER.warning(os.path.join(bidsmodality, bidsname)
                               + '.* already exists -- check your '
                               'results carefully!')
            if not dicomfile.convert(bidsmodality, bidsmap["Options"]):
                LOGGER.error("Failed to convert {} using {}"
                             .format(dicomfile.currentFile(),
                                     dicomfile.converter))
                raise ValueError("Convertion error")
            with open(os.path.join(bidsmodality, bidsname + '.json'), 'w')\
                    as f:
                js_dict = dicomfile.exportMeta()
                json.dump(js_dict, f, indent=2)

            dicomfile.rec_BIDSvalues["filename"]\
                = os.path.join(dicomfile.modality, bidsname) + ".nii"
            dicomfile.rec_BIDSvalues["acq_time"]\
                = dicomfile.acq_time().replace(microsecond=0)

            # plugin entry point
            plugins.RunPlugin("RecordingEP", dicomfile)

            scans_tsv = os.path.join(bidsses,
                                     '{}_{}_scans.tsv'
                                     .format(sub, ses))
            if os.path.isfile(scans_tsv):
                with open(scans_tsv, "a") as f:
                    f.write(dicomfile.rec_BIDSfields.GetLine(
                        dicomfile.rec_BIDSvalues))
                    f.write('\n')
            else:
                with open(scans_tsv, "w") as f:
                    f.write(dicomfile.rec_BIDSfields.GetHeader())
                    f.write('\n')
                    f.write(dicomfile.rec_BIDSfields.GetLine(
                        dicomfile.rec_BIDSvalues))
                    f.write('\n')
                dicomfile.rec_BIDSfields.DumpDefinitions(
                        tools.change_ext(scans_tsv,"json"))


def bidscoiner(rawfolder: str, bidsfolder: str, 
               subjects: tuple=(), force: bool=False, 
               participants: bool=False, 
               bidsmapfile: str='bidsmap.yaml', 
               subprefix: str='sub-', sesprefix: str='ses-',
               options: list=[]) -> None:
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
    :param options:         A list of parameters passed to plugin
    :return:                Nothing
    """

    # Input checking & defaults
    rawfolder = os.path.abspath(os.path.realpath(rawfolder))
    bidsfolder = os.path.abspath(os.path.realpath(bidsfolder))

    # Start logging
    bids.setup_logging(os.path.join(bidsfolder,
                                    'code', 
                                    'bidscoin', 'bidscoiner.log'))
    LOGGER.info('')
    LOGGER.info(f'-------------- START BIDScoiner {bids.version()}: '
                'BIDS {bids.bidsversion()} ------------')
    LOGGER.info(f'>>> bidscoiner sourcefolder={rawfolder} '
                'bidsfolder={bidsfolder} subjects={subjects} '
                'force={force}'
                f' participants={participants} bidsmap={bidsmapfile} '
                'subprefix={subprefix} sesprefix={sesprefix}')

    # Creating temporary directory
    global tmpDir
    try:
        tmpDir = tempfile.mkdtemp(
            prefix=os.path.basename(sys.argv[0]) + "_"
            ) + "/"
    except FileNotFoundError:
        LOGGER.warning("TMPDIR: Failed to create temporary directory."
                       "Will try current directory")
        tmpDir = tempfile.mkdtemp(
            prefix=os.path.basename(sys.argv[0]) + "_",dir="."
            ) + "/"
    LOGGER.debug("Temporary directory: {}".format(tmpDir))

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

    # Load and initialize plugin
    if bidsmap["PlugIns"]:
        if "path" in bidsmap["PlugIns"]:
            plugins.ImportPlugins(bidsmap["PlugIns"]["path"])
            params = dict()
            if "parameters" in bidsmap["PlugIns"]:
                params = bidsmap["PlugIns"]["parameters"]
            params["rawfolder"] = rawfolder
            params["bidsfolder"] = rawfolder
            plugins.InitPlugin(options, params)

    # Save options to the .bidsignore file
    bidsignore_items = [item.strip() 
                        for item in 
                        bidsmap['Options']['bidscoin']['bidsignore'].split(';')
                        ]
    LOGGER.info("Writing {} entries to {}.bidsignore"
                .format(bidsignore_items, bidsfolder))
    with open(os.path.join(bidsfolder,'.bidsignore'), 'w') as bidsignore:
        for item in bidsignore_items:
            bidsignore.write(item + '\n')

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

    # Loop over all subjects and sessions
    # and convert them using the bidsmap entries
    for n, subject in enumerate(subjects, 1):

        LOGGER.info('-------------------------------------')
        LOGGER.info(f'Coining subject ({n}/{len(subjects)}): {subject}')

        personals = dict()
        sessions = bids.lsdirs(subject, sesprefix + '*')
        if not sessions:
            sessions = [subject]
        for session in sessions:
            # Update / append the dicom mapping
            coin_dicom(session, bidsmap, bidsfolder, personals,
                       subprefix, sesprefix)

    # Synchronizing subject list
    new_sub_file = os.path.join(tmpDir, "participants.tsv")
    old_sub_file = os.path.join(bidsfolder, "participants.tsv")
    if os.path.isfile(new_sub_file):
        new_sub = pd.read_csv(new_sub_file, sep="\t", header=0,
                              index_col="participant_id",
                              na_values="n/a")
        new_sub = new_sub.groupby("participant_id").ffill().drop_duplicates()
        duplicates = new_sub.index.duplicated(keep=False)
        if duplicates.any():
            LOGGER.error("One or several subjects have conflicting values."
                         "See {} for details"
                         .format(new_sub_file))
            raise ValueError("Conflicting values in subject descriptions")
        if os.path.isfile(old_sub_file):
            old_sub = pd.read_csv(old_sub_file, sep="\t", header=0,
                                  index_col="participant_id",
                                  na_values="n/a")
            if new_sub.columns != old_sub.columns:
                LOGGER.error("Subject table header mismach, "
                             "see {} and {} for details."
                             .format(new_sub_file, old_sub_file))
                raise ValueError("Mismaching header in subject descriptions")
            new_sub.append(old_sub)
            new_sub.groupby("participant_id").ffill().drop_duplicates()
            duplicates = new_sub.duplicated("participant_id", keep=False)
            if duplicates.any():
                LOGGER.error("One or several subjects have conflicting values."
                             "See {} and {} for details"
                             .format(new_sub_file, old_sub_file))
                raise ValueError("Conflicting values in subject descriptions")
        new_sub.to_csv(old_sub_file,
                       sep='\t',na_rep="n/a",
                       index=True, header=True) 
        json_file = tools.change_ext(old_sub_file, "json")
        if not os.path.isfile(json_file):
            shutil.copyfile(tools.change_ext(new_sub_file, "json"),json_file)

        shutil.rmtree(tmpDir)

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

    options = []
    params = sys.argv[1:]
    if "--" in params:
        pos = params.index("--")
        options = params[pos + 1:]
        params = params[:pos]

    args = parser.parse_args(params)

    bidscoiner(rawfolder=args.sourcefolder,
               bidsfolder=args.bidsfolder,
               subjects=args.participant_label,
               force=args.force,
               participants=args.skip_participants,
               bidsmapfile=args.bidsmap,
               subprefix=args.subprefix,
               sesprefix=args.sesprefix,
               options=options)
