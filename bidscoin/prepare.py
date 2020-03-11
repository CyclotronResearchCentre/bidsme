#!/usr/bin/env python
"""
Sorts and data files into local sub-direcories
destination/sub-xxx/ses-xxx/zzz-seriename/<data-file>

Plugins allow to modify subjects and session names
and preform various operations on data files.
"""
import os
import logging
import glob
import pandas

import tools.tools as tools
import plugins

from Modules import select
from bids import BidsSession


logger = logging.getLogger(__name__)


def sortsession(outfolder: str,
                recording: object,
                dry_run: bool) -> None:

    plugins.RunPlugin("SequenceEP", recording)

    logger.info("Processing: sub '{}', ses '{}' ({} files)"
                .format(recording.subId(),
                        recording.sesId(),
                        len(recording.files)))

    if not dry_run:
        os.makedirs(outfolder, exist_ok=True)

    recording.index = -1
    while recording.loadNextFile():
        plugins.RunPlugin("RecordingEP", recording)
        recording.getBidsSession().registerFields(True)
        serie = os.path.join(
                outfolder,
                "{}/{}".format(recording.Module(),
                               recording.recIdentity(index=False)))
        if not dry_run:
            os.makedirs(serie, exist_ok=True)
            outfile = recording.copyRawFile(serie)
            plugins.RunPlugin("FileEP", outfile, recording)
    plugins.RunPlugin("SequenceEndEP", outfolder, recording)


def prepare(source: str, destination: str,
            plugin_file: str = "",
            plugin_opt: dict = {},
            sub_list: list = [],
            sub_skip_tsv: bool = False,
            sub_skip_dir: bool = False,
            ses_skip_dir: bool = False,
            part_template: str = "",
            sub_prefix: str = "",
            ses_prefix: str = "",
            sub_no_dir: bool = False,
            ses_no_dir: bool = False,
            data_dirs: dict = {},
            dry_run: bool = False
            ) -> None:
    """
    Prepare data from surce folder and place it in
    sestination folder.

    Source folder is expected to have structure
    source/[subId/][sesId/][data/]file.
    Absence of subId and sesId levels must be communicated
    via sub_no_dir and ses_no_dir options. List of data
    folders must be given in data_dirs.

    Prepeared data will have structure
    destination/sub-<subId>/ses-<sesId>/<type>/<sequence>/file

    A list of treated subjects will be created/updated
    in destination/participants.tsv file

    Parameters
    ----------
    source: str
        folder containing source dataset
    destination: str
        folder for prepeared dataset
    plugin_file: str
        path to the plugin file to use
    plugin_opt: dict
        named options passed to plugin
    sub_list: list
        list of subject to process. Subjects
        are checked after plugin and must
        start with 'sub-', as in destination
        folder
    sub_skip_tsv: bool
        if set to True, subjects found in
        destination/participants.tsv will be
        ignored
    sub_skip_dir: bool
        if set to true, subjects with already
        created directories will be ignored
        Can conflict with sub_no_dir
    ses_skip_dir: bool
        if set to True, sessions with already
        created directories will be ignored
        Can conflict with ses_no_dir
    part_template: str
        path to template json file, from whitch
        participants.tsv will be modeled. Must be
        formated as usual BIDS sidecar json file
        for tsv files
    sub_prefix: str
        prefix for subject folders in source dataset.
        If set, subject folders without prefix will
        be ignored, and will be stripped from subject
        Ids: sub001 -> 001 if sub_prefix==sub
        Option has no effect if sub_no_dir==True
    ses_prefix: str
        prefix for session folders in source dataset.
        If set, session folders without prefix will
        be ignored, and will be stripped from session
        Ids: sesTest -> Test if ses_prefix==ses
        Option has no effect if ses_no_dir==True
    sub_no_dir: bool
        if set to True, source dataset will not be
        expected to have subject folders.
    ses_no_dir: bool
        if set to True, source dataset will not be
        expected to have session folders.
    data_dirs: dict
        dictionary containing list of folders with
        recording data as key and data type as value.
        If folder contain several types of data,
        then value must be set to empty string
    dry_run: bool
        if set to True, no disk writing operations
        will be performed
    """

    logger.info("-------------- Prepearing data -------------")
    logger.info("Source directory: {}".format(source))
    logger.info("Destination directory: {}".format(destination))

    # Input checking
    # source = os.path.abspath(source)
    if not os.path.isdir(source):
        logger.critical("Source directory {} don't exists"
                        .format(source))
        raise NotADirectoryError(source)
    if not os.path.isdir(destination):
        logger.critical("Destination directory {} don't exists"
                        .format(destination))
        raise NotADirectoryError(destination)

    if sub_no_dir and sub_skip_dir:
        logger.warning("Both sub_no_dir and sub_skip_dir are set. "
                       "Subjects will not be skipped "
                       "unless subId defined in plugin")
    if ses_no_dir and ses_skip_dir:
        logger.warning("Both ses_no_dir and ses_skip_dir are set. "
                       "Sessions will not be skipped "
                       "unless sesId defined in plugin")

    df_participants = None
    if sub_skip_tsv:
        tsv = os.path.join(destination, "participants.tsv")
        if os.path.isfile(tsv):
            df_participants = pandas.read_csv(tsv,
                                              sep="\t", header=0,
                                              na_values="n/a",
                                              usecols=["participant_id"],
                                              comment="#")
            df_participants = df_participants["participant_id"].values

    plugins.ImportPlugins(plugin_file)
    plugins.InitPlugin(source=source,
                       destination=destination,
                       dry=dry_run,
                       **plugin_opt)

    BidsSession.loadSubjectFields(part_template)

    sub_prefix_dir, sub_prefix = os.path.split(sub_prefix)
    ses_prefix_dir, ses_prefix = os.path.split(ses_prefix)

    if not sub_no_dir:
        sub_dirs = tools.lsdirs(
                os.path.join(source, sub_prefix_dir),
                sub_prefix + '*')
    else:
        sub_dirs = [source]

    if not data_dirs:
        data_dirs = {}

    for sub_dir in sub_dirs:
        scan = BidsSession()
        scan.in_path = sub_dir
        # get name of subject from folder name
        if not sub_no_dir:
            scan.subject = os.path.basename(sub_dir)
            scan.subject = scan.subject[len(sub_prefix):]
        plugins.RunPlugin("SubjectEP", scan)
        scan.lock_subject()

        if scan.subject is not None:
            skip = False
            if sub_list:
                if scan.subject not in sub_list:
                    logger.debug("{} not in list".format(scan.subject))
                    skip = True
            if df_participants is not None:
                if scan.subject in df_participants:
                    logger.debug("{} in tsv".format(scan.subject))
                    skip = True
            if sub_skip_dir:
                if os.path.isdir(os.path.join(destination,
                                              scan.subject)):
                    logger.debug("{} dir exists".format(scan.subject))
                    skip = True

            if skip:
                logger.info("Skipping subject '{}'"
                            .format(scan.subject))
                continue

        if not ses_no_dir:
            ses_dirs = tools.lsdirs(
                    os.path.join(sub_dir, ses_prefix_dir),
                    ses_prefix + '*')
        else:
            ses_dirs = [sub_dir]

        for ses_dir in ses_dirs:
            scan.in_path = ses_dir
            logger.info("Scanning folder {}".format(ses_dir))
            if not ses_no_dir:
                scan.unlock_session()
                scan.session = os.path.basename(ses_dir)
                scan.session = scan.session[len(ses_prefix):]
            plugins.RunPlugin("SessionEP", scan)
            scan.lock()

            if scan.session is not None:
                skip = False
                if ses_skip_dir:
                    if os.path.isdir(os.path.join(destination,
                                                  scan.session)):
                        logger.debug("{} dir exists".format(scan.session))
                        skip = True
                if skip:
                    logger.info("Skipping session '{}'"
                                .format(scan.session))
                    continue

            for rec_dirs, rec_type in data_dirs.items():
                rec_dirs = [f for f in
                            glob.glob(os.path.join(ses_dir,
                                                   rec_dirs)
                                      + "/")
                            ]
                for rec_dir in rec_dirs:
                    if not os.path.isdir(rec_dir):
                        logger.warning("Sub: '{}', Ses: '{}': "
                                       "'{}' don't exists "
                                       "or not a folder"
                                       .format(scan.subject,
                                               scan.session,
                                               rec_dir))
                        continue
                    cls = select(rec_dir, rec_type)
                    if cls is None:
                        logger.warning("Unable to identify data in folder {}"
                                       .format(rec_dir))
                        continue
                    recording = cls(rec_path=rec_dir)
                    if not recording or len(recording.files) == 0:
                        logger.warning("unable to load data in folder {}"
                                       .format(rec_dir))
                    recording.setBidsSession(scan)
                    scan = recording.getBidsSession()
                    out_path = os.path.join(destination,
                                            scan.getPath(True))
                    sortsession(out_path, recording, dry_run)
            plugins.RunPlugin("SessionEndEP", scan)
    if not dry_run:
        BidsSession.exportParticipants(destination)

    plugins.RunPlugin("FinaliseEP")
