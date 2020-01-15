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
import shutil
import pandas as pd
import json
import logging
import tempfile

from tools import tools
from tools import plugins
from tools import info
import Modules
import bidsmap as Bidsmap

logger = logging.getLogger()
logger.name = os.path.splitext(os.path.basename(__file__))[0]
tmpDir = None


def coin(session: str, bidsmap: dict,
         bidsfolder: str, personals: dict) -> None:
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

    if not tools.lsdirs(session):
        logger.warning('No run subfolder(s) found in: ' + session)
        return

    # Process all the dicom run subfolders
    for module in tools.lsdirs(session):
        module = os.path.basename(module)
        if module not in Modules.types_list:
            continue

        for runfolder in tools.lsdirs(session, module + "/*"):
            logger.info('Processing: {}'.format(runfolder))
            cls = Modules.select(runfolder, module)
            if cls is None:
                logger.warning("Unable to identify data in folder {}"
                               .format(runfolder))
                continue
            # Get a recording
            recording = cls(rec_path=runfolder)
            seq = os.path.basename(runfolder)
            recording.setSubId()
            recording.setSesId()
            sub = recording.subId()
            ses = recording.sesId()
            logger.debug("Subject: {}; Session: {}".format(sub, ses))
            bidsses = os.path.join(bidsfolder, sub, ses)

            recording.sub_BIDSvalues["participant_id"] = sub

            # plugin entry point for name and json adjustements
            plugins.RunPlugin("SessionEP", recording)

            sub_tsv = os.path.join(tmpDir, 'participants.tsv')
            if os.path.isfile(sub_tsv):
                with open(sub_tsv, "a") as f:
                    f.write(recording.sub_BIDSfields.GetLine(
                        recording.sub_BIDSvalues))
                    f.write('\n')
            else:
                with open(sub_tsv, "w") as f:
                    f.write(recording.sub_BIDSfields.GetHeader())
                    f.write('\n')
                    f.write(recording.sub_BIDSfields.GetLine(
                            recording.sub_BIDSvalues))
                    f.write('\n')
                recording.sub_BIDSfields.DumpDefinitions(
                        tools.change_ext(sub_tsv, "json"))

            recording.index = -1
            while recording.loadNextFile():
                modality, r_index, r_obj = bidsmap.match_run(recording)
                if not modality:
                    e = "{}: No compatible run found"\
                        .format(recording.recIdentity())
                    logger.error(e)
                    raise ValueError(e)
                if modality == Modules.ignoremodality:
                    logger.info('{}: ignored modality'
                                .format(recording.recIdentity()))
                    continue
                recording.setLabels(r_obj)
                recording.generateMeta()

                # plugin entry point
                plugins.RunPlugin("RecordingEP", recording)
                bidsname = recording.getBidsname()

                bidsmodality = os.path.join(bidsses, recording.Modality())
                os.makedirs(bidsmodality, exist_ok=True)

                # Check if file already exists
                if os.path.isfile(os.path.join(bidsmodality,
                                               bidsname + '.json')):
                    e = "{}/{}.json exists at destination"\
                        .format(bidsmodality, bidsname)
                    logger.error(e)
                    raise FileExistsError(e)
                recording.bidsify(bidsfolder)

                recording.rec_BIDSvalues["filename"]\
                    = os.path.join(recording.Modality(), bidsname) + ".nii"
                recording.rec_BIDSvalues["acq_time"]\
                    = recording.acqTime().replace(microsecond=0)

                scans_tsv = os.path.join(bidsses,
                                         '{}_{}_scans.tsv'
                                         .format(sub, ses))
                if os.path.isfile(scans_tsv):
                    with open(scans_tsv, "a") as f:
                        f.write(recording.rec_BIDSfields.GetLine(
                            recording.rec_BIDSvalues))
                        f.write('\n')
                else:
                    with open(scans_tsv, "w") as f:
                        f.write(recording.rec_BIDSfields.GetHeader())
                        f.write('\n')
                        f.write(recording.rec_BIDSfields.GetLine(
                            recording.rec_BIDSvalues))
                        f.write('\n')
                    recording.rec_BIDSfields.DumpDefinitions(
                            tools.change_ext(scans_tsv, "json"))


def bidscoiner(rawfolder: str, bidsfolder: str,
               subjects: tuple = (), force: bool = False,
               participants: bool = False,
               bidsmapfile: str = 'bidsmap.yaml',
               options: list = []) -> None:
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
    :param options:         A list of parameters passed to plugin
    :return:                Nothing
    """

    # Input checking & defaults
    rawfolder = os.path.abspath(rawfolder)
    bidsfolder = os.path.abspath(bidsfolder)
    bidscodefolder = os.path.join(bidsfolder, 'code', 'bidscoin')

    # Start logging
    info.setup_logging(logger, bidscodefolder, 'INFO')
    logger.info('')
    logger.info('-------------- START BIDScoiner ------------')
    logger.info('bidscoin ver {}'.format(info.version()))
    logger.info('bids ver {}'.format(info.bidsversion()))

    # Creating temporary directory
    global tmpDir
    try:
        tmpDir = tempfile.mkdtemp(
            prefix=os.path.basename(sys.argv[0]) + "_"
            ) + "/"
    except FileNotFoundError:
        logger.warning("TMPDIR: Failed to create temporary directory."
                       "Will try current directory")
        tmpDir = tempfile.mkdtemp(
            prefix=os.path.basename(sys.argv[0]) + "_", dir="."
            ) + "/"
    logger.debug("Temporary directory: {}".format(tmpDir))

    # Create a code/bidscoin subfolder
    os.makedirs(os.path.join(bidsfolder, 'code', 'bidscoin'), exist_ok=True)

    # Create a dataset description file if it does not exist
    dataset_file = os.path.join(bidsfolder, 'dataset_description.json')
    if not os.path.isfile(dataset_file):
        logger.warning("Dataset description file 'dataset_description.json' "
                       "not found in '{}'".format(bidsfolder))

    # Create a README file if it does not exist
    readme_file = os.path.join(bidsfolder, 'README')
    if not os.path.isfile(readme_file):
        logger.warning("Dataset readme file 'README' "
                       "not found in '{}'".format(bidsfolder))

    # Get the bidsmap heuristics from the bidsmap YAML-file
    logger.info("loading bidsmap {}".format(bidsmapfile))
    bidsmap = Bidsmap.bidsmap(bidsmapfile)

    if not bidsmap:
        logger.error('Bidsmap file {} not found.'
                     .format(bidsfolder))
        return
    ntotal, ntemplate, nunchecked = bidsmap.countRuns()
    logger.debug("Map contains {} runs".format(ntotal))
    if ntemplate != 0:
        logger.warning("Map contains {} template runs"
                       .format(ntemplate))
    if nunchecked != 0:
        logger.error("Map contains {} unchecked runs"
                       .format(nunchecked))
        return

    # Load and initialize plugin
    if bidsmap.plugin_file:
        plugins.ImportPlugins(bidsmap.plugin_file)
        bidsmap.plugin_options["rawfolder"] = rawfolder
        bidsmap.plugin_options["bidsfolder"] = bidsfolder
        plugins.InitPlugin(bidsmap.plugin_options)

    # Save options to the .bidsignore file
    bidsignore_items = [item.strip()
                        for item in
                        bidsmap.bidsignore
                        ]
    if len(bidsignore_items) > 0:
        logger.info("Writing {} entries to {}.bidsignore"
                    .format(bidsignore_items, bidsfolder))
        with open(os.path.join(bidsfolder, '.bidsignore'), 'w') as bidsignore:
            for item in bidsignore_items:
                bidsignore.write(item + '\n')

    # Get the list of subjects
    if not subjects:
        subjects = tools.lsdirs(rawfolder)
    if not subjects:
        logger.warning('No subjects found in: {}*'
                       .format(os.path.join(rawfolder)))
        return

    # Loop over all subjects and sessions
    # and convert them using the bidsmap entries
    for n, subject in enumerate(subjects, 1):

        logger.info('-------------------------------------')
        logger.info('Coining subject ({}/{}): {}'
                    .format(n, len(subjects), subject))

        personals = dict()
        sessions = tools.lsdirs(subject)
        if not sessions:
            logger.warning("No session to process")
            continue
        for session in sessions:
            # Update / append the dicom mapping
            coin(session, bidsmap, bidsfolder, personals)

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
            logger.error("One or several subjects have conflicting values."
                         "See {} for details"
                         .format(new_sub_file))
            raise ValueError("Conflicting values in subject descriptions")
        if os.path.isfile(old_sub_file):
            old_sub = pd.read_csv(old_sub_file, sep="\t", header=0,
                                  index_col="participant_id",
                                  na_values="n/a")
            if set(new_sub.columns) != set(old_sub.columns):
                logger.error("Subject table header mismach, "
                             "see {} and {} for details."
                             .format(new_sub_file, old_sub_file))
                raise ValueError("Mismaching header in subject descriptions")
            new_sub = new_sub.append(old_sub)
            new_sub = new_sub.groupby("participant_id")\
                .ffill().drop_duplicates()
            duplicates = new_sub.index.duplicated()
            if duplicates.any():
                logger.error("One or several subjects have conflicting values."
                             "See {} and {} for details"
                             .format(new_sub_file, old_sub_file))
                raise ValueError("Conflicting values in subject descriptions")
        new_sub.to_csv(old_sub_file,
                       sep='\t', na_rep="n/a",
                       index=True, header=True)
        json_file = tools.change_ext(old_sub_file, "json")
        if not os.path.isfile(json_file):
            shutil.copyfile(tools.change_ext(new_sub_file, "json"), json_file)

        shutil.rmtree(tmpDir)

    logger.info('-------------- FINISHED! ------------')
    logger.info('')

    info.reporterrors(logger)


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
    parser.add_argument('-p', '--participant_label',
                        help='Space seperated list of selected sub-# '
                        'names / folders to be processed (the sub- '
                        'prefix can be removed). Otherwise all subjects '
                        'in the sourcefolder will be selected',
                        nargs='+')
    parser.add_argument('-f', '--force', help='If this flag is given '
                        'subjects will be processed, regardless of '
                        'existing folders in the bidsfolder. '
                        'Otherwise existing folders will be skipped',
                        action='store_true')
    parser.add_argument('-s', '--skip_participants',
                        help='If this flag is given those subjects '
                        'that are in particpants.tsv will not be '
                        'processed (also when the --force flag is given). '
                        'Otherwise the participants.tsv table is ignored',
                        action='store_true')
    parser.add_argument('-b', '--bidsmap',
                        help='The bidsmap YAML-file with the study '
                        'heuristics. If the bidsmap filename is relative '
                        '(i.e. no "/" in the name) then it is assumed to '
                        'be located in bidsfolder/code/bidscoin. '
                        'Default: bidsmap.yaml',
                        default='bidsmap.yaml')
    parser.add_argument('-v', '--version',
                        help='Show the BIDS and BIDScoin version',
                        action='version',
                        version=f'BIDS-version:\t\t{info.bidsversion()}'
                        '\nBIDScoin-version:\t{info.version()}')

    options = []
    params = sys.argv[1:]
    if "--" in params:
        pos = params.index("--")
        options = params[pos + 1:]
        params = params[:pos]

    args = parser.parse_args(params)

    if os.path.dirname(args.bidsmap) == "":
        args.bidsmap = os.path.join(args.bidsfolder,
                                    "code/bidscoin",
                                    args.bidsmap)

    bidscoiner(rawfolder=args.sourcefolder,
               bidsfolder=args.bidsfolder,
               subjects=args.participant_label,
               force=args.force,
               participants=args.skip_participants,
               bidsmapfile=args.bidsmap,
               options=options)
