#############################################################################
# prepare.py is a script that prepares source dataset for bidsification
# it identifies the subjects, sessions and series that each recording
# in the source dataset belongs and sort them accordingly
#############################################################################
# Copyright (c) 2018-2020, University of Liège
# Author: Nikita Beliy
# Owner: Liege University https://www.uliege.be
# Credits: [Marcel Zwiers]
# Maintainer: Nikita Beliy
# Email: Nikita.Beliy@uliege.be
# Status: developpement
#############################################################################
# This file is part of BIDSme
# BIDSme is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# eegBidsCreator is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with BIDSme.  If not, see <https://www.gnu.org/licenses/>.
############################################################################

import os
import logging
import glob
import pandas

from tools import tools
import plugins

import Modules
from bids import BidsSession


logger = logging.getLogger(__name__)


def sortsession(outfolder: str,
                session: BidsSession,
                recording: object,
                dry_run: bool) -> None:

    recording.setBidsSession(session)

    if plugins.RunPlugin("SequenceEP", recording) < 0:
        logger.warning("Sequence {} discarded by {}"
                       .format(recording.recIdentity(False),
                               "SequenceEP"))
        return

    logger.info("Processing: sub '{}', ses '{}' ({} files)"
                .format(recording.subId(),
                        recording.sesId(),
                        len(recording.files)))

    recording.index = -1
    while recording.loadNextFile():
        if session.subject is None:
            recording.getBidsSession().unlock_subject()
            recording.getBidsSession().subject = None
        if session.session is None:
            recording.getBidsSession().unlock_session()
            recording.getBidsSession().session = None

        if plugins.RunPlugin("RecordingEP", recording) < 0:
            logger.warning("Recording {} discarded by {}"
                           .format(recording.recIdentity(),
                                   "RecordingEP"))
            continue

        if session.subject is None:
            recording.setSubId()
        if session.session is None:
            recording.setSesId()

        recording.getBidsSession().registerFields(True)
        serie = os.path.join(
                outfolder,
                recording.getBidsSession().getPath(True),
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

    ###############
    # Plugin setup
    ###############
    if plugin_file:
        plugins.ImportPlugins(plugin_file)
        plugins.InitPlugin(source=source,
                           destination=destination,
                           dry=dry_run,
                           **plugin_opt)

    ###############################
    # Checking participants list
    ###############################
    new_sub_json = os.path.join(destination, "participants.json")
    if not part_template:
        if os.path.isfile(new_sub_json):
            part_template = new_sub_json
    BidsSession.loadSubjectFields(part_template)

    old_sub_file = os.path.join(destination, "participants.tsv")
    old_sub = None
    if os.path.isfile(old_sub_file):
        old_sub = pandas.read_csv(old_sub_file, sep="\t", header=0,
                                  na_values="n/a")
        if not BidsSession.checkDefinitions(old_sub):
            raise Exception("Destination participant.tsv incompatible "
                            "with given columns definitions")
    dupl_file = os.path.join(destination, "__duplicated.tsv")
    if os.path.isfile(dupl_file):
        logger.critical("Found unmerged file with duplicated subjects")
        raise FileExistsError(dupl_file)

    ###############
    # Subject loop
    ###############
    sub_prefix_dir, sub_prefix = os.path.split(sub_prefix)
    ses_prefix_dir, ses_prefix = os.path.split(ses_prefix)

    if not sub_no_dir:
        sub_dirs = tools.lsdirs(
                os.path.join(source, sub_prefix_dir),
                sub_prefix + '*')
    else:
        sub_dirs = [source]
    if not sub_dirs:
        logger.warning("No subject folders found")

    if not data_dirs:
        data_dirs = {}

    for sub_dir in sub_dirs:
        scan = BidsSession()
        scan.in_path = sub_dir
        # get name of subject from folder name
        if not sub_no_dir:
            scan.subject = os.path.basename(sub_dir)
            scan.subject = scan.subject[len(sub_prefix):]
        if plugins.RunPlugin("SubjectEP", scan) < 0:
            logger.warning("Subject {} discarded by {}"
                           .format(scan.subject, "SubjectEP"))
            continue
        scan.lock_subject()

        if scan.subject is not None:
            if tools.skipEntity(scan.subject, sub_list,
                                old_sub if sub_skip_tsv else None,
                                destination if sub_skip_dir else ""):
                logger.info("Skipping subject '{}'"
                            .format(scan.subject))
                continue

        if not ses_no_dir:
            ses_dirs = tools.lsdirs(
                    os.path.join(sub_dir, ses_prefix_dir),
                    ses_prefix + '*')
        else:
            ses_dirs = [sub_dir]
        if not ses_dirs:
            logger.warning("No session folders found")

        for ses_dir in ses_dirs:
            scan.in_path = ses_dir
            logger.info("Scanning folder {}".format(ses_dir))
            if not ses_no_dir:
                scan.unlock_session()
                scan.session = os.path.basename(ses_dir)
                scan.session = scan.session[len(ses_prefix):]
            if plugins.RunPlugin("SessionEP", scan) < 0:
                logger.warning("Session {} discarded by {}"
                               .format(scan.session, "SessionEP"))
                continue

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

            if not data_dirs:
                data_dirs[""] = ""
            for rec_dirs, rec_type in data_dirs.items():
                rec_dirs = [f for f in
                            glob.glob(os.path.join(ses_dir,
                                                   rec_dirs)
                                      )
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
                    cls = Modules.select(rec_dir, rec_type)
                    if cls is None:
                        logger.warning("Unable to identify data in folder {}"
                                       .format(rec_dir))
                        continue
                    recording = cls(rec_path=rec_dir)
                    if not recording or len(recording.files) == 0:
                        logger.warning("unable to load data in folder {}"
                                       .format(rec_dir))
                    sortsession(destination, scan, recording, dry_run)
            plugins.RunPlugin("SessionEndEP", scan)

        scan.in_path = sub_dir
        plugins.RunPlugin("SubjectEndEP", scan)

    df_processed = BidsSession.exportAsDataFrame()

    if old_sub is not None:
        df_res = pandas.concat([old_sub, df_processed],
                               sort=False,
                               ignore_index=True)
    else:
        df_res = df_processed
    df_res = df_res[BidsSession.getSubjectColumns()].drop_duplicates()

    df_dupl = df_res.duplicated("participant_id")
    if df_dupl.any():
        logger.critical("Participant list contains one or several duplicated "
                        "entries: {}"
                        .format(", ".join(df_res[df_dupl]["participant_id"]))
                        )

    if not dry_run:
        df_res[~df_dupl].to_csv(old_sub_file,
                                sep='\t', na_rep="n/a",
                                index=False, header=True)
        if df_dupl.any():
            logger.info("Saving the list to be merged manually to {}"
                        .format(dupl_file))
            df_res[df_dupl].to_csv(dupl_file,
                                   sep='\t', na_rep="n/a",
                                   index=False, header=True)

        new_sub_json = os.path.join(destination, "participants.json")
        if not os.path.isfile(new_sub_json):
            BidsSession.exportDefinitions(new_sub_json)

    plugins.RunPlugin("FinaliseEP")
