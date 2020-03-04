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
import shutil
import pandas
import json
import logging
import time
import traceback

import argparse
import textwrap

from tools import tools
from tools import info
import plugins
import exceptions

import Modules
from bidsmap import Bidsmap
from bids.BidsSession import BidsSession

logger = logging.getLogger()
logger.name = os.path.splitext(os.path.basename(__file__))[0]
info.setup_logging(logger, 'INFO')

bidsfolder = ""
rawfolder = ""


def coin(recording: Modules.baseModule,
         bidsmap: Bidsmap, dry_run: bool) -> None:
    """
    Converts the session dicom-files into BIDS-valid nifti-files
    in the corresponding bidsfolder and extracts personals
    (e.g. Age, Sex) from the dicom header

    :param session:     The full-path name of the subject/session source folder
    :param bidsmap:     The full mapping heuristics from the bidsmap YAML-file
    :param personals:   The dictionary with the personal information
    :param subprefix:   The prefix common for all source subject-folders
    :param sesprefix:   The prefix common for all source session-folders
    :return:            Nothing
    """
    recording.sub_BIDSvalues["participant_id"] = recording.subId()
    out_path = os.path.join(bidsfolder,
                            recording.getBidsPrefix("/"))

    recording.index = -1
    while recording.loadNextFile():
        plugins.RunPlugin("RecordingEP", recording)
        out_path = os.path.join(bidsfolder,
                                recording.getBidsPrefix("/"))
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

        bidsmodality = os.path.join(out_path, recording.Modality())

        # Check if file already exists
        if os.path.isfile(os.path.join(bidsmodality,
                                       bidsname + '.json')):
            e = "{}/{}.json exists at destination"\
                .format(bidsmodality, bidsname)
            logger.error(e)
            raise FileExistsError(e)
        if not dry_run:
            recording.bidsify(bidsfolder)
    if dry_run:
        plugins.RunPlugin("SequenceEndEP", out_path, recording)
    else:
        plugins.RunPlugin("SequenceEndEP", None, recording)


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

    new_sub_file = os.path.join(rawfolder, "participants.tsv")
    df_sub = pandas.read_csv(new_sub_file,
                             sep="\t", header=0,
                             na_values="n/a")
    df_dupl = df_sub.duplicated("participant_id")
    if df_dupl.any():
        logger.critical("Participant list contains one or several duplicated "
                        "entries: {}"
                        .format(", ".join(df_sub[df_dupl]["participant_id"]))
                        )
        raise Exception("Duplicated subjects")

    with open(os.path.join(rawfolder, "participants.json"), "r") as f:
        df_definitions = json.load(f)
    BidsSession.loadSubjectFields(os.path.join(rawfolder, "participants.json"))
    if len(df_definitions) != len(df_sub.columns):
        logger.critical("Participant.tsv contains {} columns, while "
                        "sidecar contain {} definitions"
                        .format(len(df_sub.columns),
                                len(df_definitions)))
        raise Exception("Participants column mismatch")
    for col in df_sub.columns:
        if col not in df_definitions:
            logger.critical("Participant.tsv contains undefined "
                            "column '{}'"
                            .format(col))
    del df_definitions
    old_sub_file = os.path.join(bidsfolder, "participants.tsv")
    old_sub = None
    if os.path.isfile(old_sub_file):
        old_sub = pandas.read_csv(old_sub_file, sep="\t", header=0,
                                  na_values="n/a")

    df_res = df_sub
    if old_sub is not None:
        if not old_sub.columns.equals(df_sub.columns):
            logger.critical("Participant.tsv has differenrt columns "
                            "from destination dataset")
            raise Exception("Participants column mismatch")
        if participants:
            df_sub.drop(df_sub[df_sub["participant_id"].isin(
                               old_sub["participant_id"]) 
                               ].index,
                        inplace=True).reset_index(inplace=True)
        df_res = old_sub.append(df_sub, ignore_index=True).drop_duplicates()
        df_dupl = df_res.duplicated("participant_id")
        if df_dupl.any():
            logger.critical("Joined participant list contains one or "
                            "several duplicated entries: {}"
                            .format(", ".join(
                                    df_sub[df_dupl]["participant_id"])
                                    )
                            )
            raise Exception("Duplicated subjects")

    # Loop over all subjects and sessions
    # and convert them using the bidsmap entries
    n_subjects = len(df_sub["participant_id"])
    for n, subid in enumerate(df_sub["participant_id"], 1):
        subject = os.path.join(rawfolder, subid)
        if not os.path.isdir(subject):
            logger.critical("{}: Not found in {}"
                            .format(subid, rawfolder))
            continue
        scan = BidsSession()
        scan.in_path = subject
        scan.subject = subid
        plugins.RunPlugin("SubjectEP", scan)
        if participants and old_sub:
            if scan.subject in old_sub["participant_id"].values:
                logger.info("{}: In particicpants.tsv. Skipping"
                            .format(scan.subject))
        sessions = tools.lsdirs(subject, 'ses-*')
        if not sessions:
            logger.error("{}: No sessions found in: {}"
                         .format(scan.subject, subject))
            continue

        for session in sessions:
            scan.in_path = session
            scan.unlock_session()
            scan.session = os.path.basename(session)
            plugins.RunPlugin("SessionEP", scan)
            scan.lock()

            for module in Modules.selector.types_list:
                mod_dir = os.path.join(session, module)
                if not os.path.isdir(mod_dir):
                    logger.debug("Module {} not found in {}"
                                 .format(module, session))
                    continue
                logger.info('Parsing: {} (subject {}/{})'
                            .format(mod_dir, n, n_subjects))
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
                    recording.setBidsSession(scan)
                    plugins.RunPlugin("SequenceEP", recording)
                    coin(recording, bidsmap, dry_run)
            # End of session
            plugins.RunPlugin("SessionEndEP", scan)
        # End of subject
        plugins.RunPlugin("SubjectEndEP", scan)

    plugins.RunPlugin("FinaliseEP")

    if not dry_run:
        df_res.to_csv(old_sub_file,
                      sep='\t', na_rep="n/a",
                      index=False, header=True)
        json_file = tools.change_ext(old_sub_file, "json")
        if not os.path.isfile(json_file):
            shutil.copyfile(os.path.join(rawfolder, "participants.json"),
                            json_file)


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
                        "putting dataset at risk.",
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
