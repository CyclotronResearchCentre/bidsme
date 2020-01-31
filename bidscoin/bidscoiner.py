#!/usr/bin/env python
"""
Converts ("coins") datasets in the sourcefolder to datasets
in the bidsfolder according to the BIDS standard, based on
bidsmap.yaml file created by bidsmapper. 
You can run bidscoiner.py after all data is collected, 
or run / re-run it whenever new data has been added
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
import logging
import time
import traceback
import tempfile

import argparse
import textwrap

from tools import tools
from tools import info
import plugins
import exceptions

import Modules
from bidsmap import Bidsmap

logger = logging.getLogger()
logger.name = os.path.splitext(os.path.basename(__file__))[0]
info.setup_logging(logger, 'INFO')
tmpDir = None

bidsfolder = ""
rawfolder = ""


def coin(scan: dict, recording: Modules.baseModule,
         bidsmap: Bidsmap, dry_run: bool) -> None:
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
    recording.sub_BIDSvalues["participant_id"] = scan["subject"]
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
        plugins.RunPlugin("RecordingEP", recording)
        # checking in the current map
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

        bidsname = recording.getBidsname()

        bidsmodality = os.path.join(scan["out_path"], recording.Modality())

        # Check if file already exists
        if os.path.isfile(os.path.join(bidsmodality,
                                       bidsname + '.json')):
            e = "{}/{}.json exists at destination"\
                .format(bidsmodality, bidsname)
            logger.error(e)
            raise FileExistsError(e)
        if not dry_run:
            os.makedirs(bidsmodality, exist_ok=True)
            recording.bidsify(bidsfolder)


def bidscoiner(force: bool = False,
               subject_list: list = [],
               participants: bool = False,
               bidsmapfile: str = 'bidsmap.yaml',
               dry_run=True,
               options: dict = {}) -> None:
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
    bidscodefolder = os.path.join(bidsfolder, 'code', 'bidscoin')

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
    os.makedirs(bidscodefolder, exist_ok=True)

    # Check for dataset description file
    dataset_file = os.path.join(bidsfolder, 'dataset_description.json')
    if not os.path.isfile(dataset_file):
        logger.warning("Dataset description file 'dataset_description.json' "
                       "not found in '{}'".format(bidsfolder))

    # Check for README file
    readme_file = os.path.join(bidsfolder, 'README')
    if not os.path.isfile(readme_file):
        logger.warning("Dataset readme file 'README' "
                       "not found in '{}'".format(bidsfolder))

    # Get the bidsmap heuristics from the bidsmap YAML-file
    logger.info("loading bidsmap {}".format(bidsmapfile))
    bidsmap = Bidsmap(bidsmapfile)

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
        plugins.InitPlugin(source=rawfolder,
                           destination=bidsfolder,
                           dry=dry_run,
                           **bidsmap.plugin_options)

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

    scan = {"subject": "", "session": "", "in_path": "", "out_path": ""}

    if subject_list:
        subjects = []
        for sub in subject_list:
            sub_dir = os.path.join(rawfolder, sub)
            if os.path.isdir(sub_dir):
                subjects.append(sub_dir)
            else:
                logger.warning("Subject {} not found in {}"
                               .format(sub, rawfolder))
    else:
        subjects = tools.lsdirs(rawfolder, 'sub-*')
    if not subjects:
        logger.critical('No subjects found in: {}'
                        .format(rawfolder))
        raise ValueError("No subjects found")

    old_sub_file = os.path.join(bidsfolder, "participants.tsv")
    old_sub = None
    if os.path.isfile(old_sub_file):
        old_sub = pd.read_csv(old_sub_file, sep="\t", header=0,
                              index_col="participant_id",
                              na_values="n/a")

    # Loop over all subjects and sessions
    # and convert them using the bidsmap entries
    for n, subject in enumerate(subjects, 1):
        scan["subject"] = os.path.basename(subject)
        plugins.RunPlugin("SubjectEP", scan)
        if participants and old_sub:
            if scan["subject"] in old_sub.index:
                logger.info("{}: In particicpants.tsv. Skipping"
                            .format(scan["subject"]))
        sessions = tools.lsdirs(subject, 'ses-*')
        if not sessions:
            logger.error("{}: No sessions found in: {}"
                         .format(scan["subject"], subject))
            continue

        for session in sessions:
            scan["session"] = os.path.basename(session)
            plugins.RunPlugin("SessionEP", scan)

            for module in Modules.selector.types_list:
                mod_dir = os.path.join(session, module)
                if not os.path.isdir(mod_dir):
                    logger.debug("Module {} not found in {}"
                                 .format(module, session))
                    continue
                logger.info('Parsing: {} (subject {}/{})'
                            .format(mod_dir, n, len(subjects)))
                for run in tools.lsdirs(mod_dir):
                    cls = Modules.selector.select(run, module)
                    if cls is None:
                        logger.error("Failed to identify data in {}"
                                     .format(mod_dir))
                        continue
                    recording = cls(rec_path=run)
                    if not recording or len(recording.files) == 0:
                        logger.error("unable to load data in folder {}"
                                     .format(run))
                    recording.setSubId(scan["subject"])
                    recording.setSesId(scan["session"])
                    if recording.subId() == "":
                        logger.error("Empty subject id not permitted")
                        continue
                    plugins.RunPlugin("SequenceEP", recording)
                    coin(scan, recording, bidsmap, dry_run)
                    plugins.RunPlugin("SequenceEndEP", recording)

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
    if old_sub:
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
    if not dry_run:
        new_sub.to_csv(old_sub_file,
                       sep='\t', na_rep="n/a",
                       index=True, header=True)
        json_file = tools.change_ext(old_sub_file, "json")
        if not os.path.isfile(json_file):
            shutil.copyfile(tools.change_ext(new_sub_file, "json"), json_file)
    shutil.rmtree(tmpDir)


# Shell usage
if __name__ == "__main__":

    class appPluginOpt(argparse.Action):
        def __call__(self, parser, args, values, option_string=None):
            if getattr(args, self.dest) is None:
                setattr(args, self.dest, dict())
            for v in values:
                key, value = v.split("=", maxsplit=1)
                getattr(args, self.dest)[key] = value

    class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter,
                          argparse.RawDescriptionHelpFormatter):
        pass

    # Parse the input arguments and run bidscoiner(args)
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
    parser.add_argument("-d", "--dry_run",
                        help="Run bidscoiner without writing anything "
                        "on the disk. Useful to detect errors without "
                        "putting dataset at risk. Default: False",
                        action="store_true")
    parser.add_argument('-v', '--version',
                        help='Show the BIDS and BIDScoin version',
                        action='version',
                        version=f'BIDS-version:\t\t{info.bidsversion()}'
                        '\nBIDScoin-version:\t{info.version()}')
    parser.add_argument('-o',
                        metavar="OptName=OptValue",
                        dest="plugin_opt",
                        help="Options passed to plugin in form "
                        "-o OptName=OptValue, several options can be passed",
                        action=appPluginOpt,
                        default={},
                        nargs="+"
                        )
    args = parser.parse_args()

    # checking paths
    # checking paths
    if not os.path.isdir(args.sourcefolder):
        logger.critical("Source directory {} don't exists"
                        .format(args.sourcefolder))
        raise NotADirectoryError(args.sourcefolder)
    if not os.path.isdir(args.bidsfolder):
        logger.critical("Bids directory {} don't exists"
                        .format(args.bidsfolder))
        raise NotADirectoryError(args.bidsfolder)

    if os.path.dirname(args.bidsmap) == "":
        args.bidsmap = os.path.join(args.bidsfolder,
                                    "code/bidscoin",
                                    args.bidsmap)
    info.addFileLogger(logger, os.path.join(os.path.join(args.bidsfolder,
                                                         "code/bidscoin",
                                                         "log")))

    code = 0
    # Start logging
    logger.info('')
    logger.info('-------------- START BIDScoiner ------------')
    logger.info('bidscoin ver {}'.format(info.version()))
    logger.info('bids ver {}'.format(info.bidsversion()))
    logger.info('-------------------------------------')

    rawfolder = os.path.abspath(args.sourcefolder)
    bidsfolder = os.path.abspath(args.bidsfolder)
    try:
        bidscoiner(
                   dry_run=args.dry_run,
                   participants=args.skip_participants,
                   bidsmapfile=args.bidsmap,
                   options=args.plugin_opt)
    except Exception as err:
        if isinstance(err, exceptions.CoinException):
            code = err.base + err.code
        else:
            code = 1
        exc_type, exc_value, exc_traceback = os.sys.exc_info()
        tr = traceback.extract_tb(exc_traceback)
        for l in tr:
            logger.error("{}({}) in {}: "
                         .format(l[0], l[1], l[2]))
        logger.error("{}:{}: {}".format(code, exc_type.__name__, exc_value))
        logger.info("Command: {}".format(os.sys.argv))

    logger.info('-------------- FINISHED! -------------------')
    errors = info.reporterrors(logger)
    logger.info("Took {} seconds".format(time.process_time()))
    logger.info('--------------------------------------------')
    if code == 0 and errors > 0:
        logger.warning("Several errors detected but exit code is 0")
        code = 1
    os.sys.exit(code)
