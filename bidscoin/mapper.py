#!/usr/bin/env python
"""
Creates a bidsmap.yaml YAML file in the bidsfolder/code/bidscoin 
that maps the information from all raw source data to the BIDS labels.
Created map can be edited/adjusted manually
"""

import os
import logging
import pandas

from tools import paths
import tools.tools as tools
from tools.yaml import yaml
import bidsmap
import plugins

import Modules
from bids.BidsSession import BidsSession

logger = logging.getLogger(__name__)


def createmap(recording: Modules.baseModule,
              bidsmap,
              template,
              bidsmap_unk) -> None:

    if plugins.RunPlugin("SequenceEP", recording) < 0:
        logger.warning("Sequence {} discarded by {}"
                       .format(recording.recIdentity(False), 
                               "SequenceEP"))
        return

    logger.info("Processing: sub '{}', ses '{}', {} ({} files)"
                .format(recording.subId(),
                        recording.sesId(),
                        recording.recIdentity(),
                        len(recording.files)))

    recording.index = -1
    while recording.loadNextFile():
        if plugins.RunPlugin("RecordingEP", recording) < 0:
            logger.warning("Recording {} discarded by {}"
                           .format(recording.recIdentity(), 
                                   "RecordingEP"))
            continue
        # checking in the current map
        modality, r_index, r_obj = bidsmap.match_run(recording)
        if not modality:
            logger.warning("{}/{}: No run found in bidsmap. "
                           "Looking into template"
                           .format(recording.Module(),
                                   recording.recIdentity()))
            # checking in the template map
            modality, r_index, r_obj = template.match_run(recording, fix=True)
            if not modality:
                logger.error("{}/{}: No compatible run found"
                             .format(recording.Module(),
                                     recording.recIdentity()))
                bidsmap_unk[recording.Module()][recording.Type()].append({
                    "provenance":recording.currentFile(),
                    "attributes":recording.attributes})
                continue
            r_obj.template = True
            modality, r_index, run = bidsmap.add_run(
                    r_obj,
                    recording.Module(),
                    recording.Type()
                    )
            plugins.RunPlugin("SequenceEndEP", None, recording)


def mapper(source: str, destination: str,
           plugin_file: str = "",
           plugin_opt: dict = {},
           sub_list: list = [],
           sub_skip_tsv: bool = False,
           sub_skip_dir: bool = False,
           ses_skip_dir: bool = False,
           bidsmapfile: str = "bidsmap.yaml",
           map_template: str = "bidsmap_template.yaml", 
           dry_run: bool = False
           ) -> None:
    """
    Generates bidsmap.yaml from prepeared dataset and 
    map template.

    Only subjects in source/participants.tsv are treated,
    this list can be narrowed using sub_list, sub_skip_tsv
    and sub_skip_dir options

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
    bidsmapfile: str
        The name of bidsmap file, will be searched for
        in destination/code/bidsmap directory, unless 
        path is absolute
    map_template: str
        The name of template map. The file is searched 
        in heuristics folder
    dry_run: bool
        if set to True, no disk writing operations
        will be performed
    """

    logger.info("------------ Generating bidsmap ------------")
    logger.info("Current directory: {}".format(os.getcwd()))
    logger.info("Source directory: {}".format(source))
    logger.info("Destination directory: {}".format(destination))

    # Input checking
    if not os.path.isdir(source):
        logger.critical("Source directory {} don't exists"
                        .format(source))
        raise NotADirectoryError(source)
    if not os.path.isdir(destination):
        logger.critical("Destination directory {} don't exists"
                        .format(destination))
        raise NotADirectoryError(destination)

    bidscodefolder = os.path.join(destination,'code','bidscoin')
    os.makedirs(bidscodefolder, exist_ok=True)

    bidsunknown = os.path.join(bidscodefolder, 'unknown.yaml')

    # removing old unknown files
    if os.path.isfile(bidsunknown):
        os.remove(bidsunknown)

    # Get the heuristics for filling the new bidsmap
    logger.info("loading template bidsmap {}".format(map_template))
    fname = paths.findFile(map_template,
                           paths.local,
                           paths.config,
                           paths.heuristics)
    if not fname:
        logger.warning("Unable to find template map {}"
                       .format(map_template))
    template = bidsmap.Bidsmap(fname)
    fname = paths.findFile(bidsmapfile,
                           paths.local,
                           paths.config,
                           bidscodefolder)
    if not fname:
        bidsmapfile = os.path.join(bidscodefolder, bidsmapfile)
    else:
        bidsmapfile = fname
    logger.info("loading working bidsmap {}".format(bidsmapfile))

    bidsmap_new = bidsmap.Bidsmap(bidsmapfile)

    if plugin_file:
        logger.warning("Using plugin from configuration file")
    elif bidsmap_new.plugin_file:
        plugin_file = bidsmap_new.plugin_file
        plugin_opt = bidsmap_new.plugin_options

    if plugin_file:
        plugins.ImportPlugins(plugin_file)
        plugins.InitPlugin(source=source,
                           destination=destination,
                           dry=True,
                           **plugin_opt)

    logger.info("creating bidsmap for unknown modalities")
    bidsmap_unk = {mod:{t.__name__:list() 
                        for t in types}
                   for mod, types in Modules.selector.types_list.items()}

    ###############################
    # Checking participants list
    ###############################
    new_sub_file = os.path.join(source, "participants.tsv")
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

    new_sub_json = os.path.join(source, "participants.json")
    if not tools.checkTsvDefinitions(df_sub, new_sub_json):
        raise Exception("Incompatible sidecar json")

    BidsSession.loadSubjectFields(new_sub_json)
    old_sub_file = os.path.join(destination, "participants.tsv")
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
        old_sub = old_sub["participant_id"]

    ##############################
    # Subjects loop
    ##############################
    n_subjects = len(df_sub["participant_id"])
    for sub_no, sub_id in enumerate(df_sub["participant_id"],1):
        sub_dir = os.path.join(source, sub_id)
        if not os.path.isdir(sub_dir):
            logger.error("{}: Not found in {}"
                         .format(sub_id, source))
            continue

        scan = BidsSession()
        scan.in_path = sub_dir
        scan.subject = sub_id
        if plugins.RunPlugin("SubjectEP", scan) < 0:
            logger.warning("Subject {} discarded by {}"
                           .format(scan.subject, "SubjectEP"))
            continue
        scan.lock_subject()
        if not scan.isSubValid():
            logger.error("{}: Subject id '{}' is not valid"
                         .format(sub_id, scan.subject))
            continue

        if tools.skipEntity(scan.subject, sub_list,
                            old_sub if sub_skip_tsv else None,
                            destination if sub_skip_dir else ""):
            logger.info("Skipping subject '{}'"
                        .format(scan.subject))
            continue

        ses_dirs = tools.lsdirs(sub_dir, 'ses-*')
        if not ses_dirs:
            logger.error("{}: No sessions found in: {}"
                         .format(scan.subject, sub_dir))
            continue

        for ses_dir in ses_dirs:
            scan.in_path = ses_dir
            logger.info("{} ({}/{}): Scanning folder {}"
                        .format(scan.subject,
                                sub_no,
                                n_subjects,
                                ses_dir))
            scan.unlock_session()
            scan.session = os.path.basename(ses_dir)
            if plugins.RunPlugin("SessionEP", scan) < 0:
                logger.warning("Session {} discarded by {}"
                               .format(scan.session, "SessionEP"))
                continue
            scan.lock()

            if ses_skip_dir and tools.skipEntity(scan.session,
                                                 [], None,
                                                 os.path.join(destination,
                                                              scan.subject)):
                logger.info("Skipping session '{}'"
                            .format(scan.session))
                continue

            for module in Modules.selector.types_list:
                mod_dir = os.path.join(ses_dir, module)
                if not os.path.isdir(mod_dir):
                    logger.debug("Module {} not found in {}"
                                 .format(module, ses_dir))
                    continue
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
                    createmap(recording, bidsmap_new, template, bidsmap_unk)

    # Create the bidsmap YAML-file in bidsfolder/code/bidscoin
    if not dry_run:
        bidsmapfile = os.path.join(bidscodefolder, 'bidsmap.yaml')

        # Save the bidsmap to the bidsmap YAML-file
        bidsmap_new.save(bidsmapfile, empty_attributes=False)

    # Scanning unknowing and exporting them to yaml file
    d = dict()
    for mod in bidsmap_unk:
        for t in bidsmap_unk[mod]:
            if bidsmap_unk[mod][t]:
                if mod not in d:
                    d[mod] = dict()
                d[mod][t] = bidsmap_unk[mod][t]
    if len(d) > 0:
        logger.error("Was unable to identify several recordings. "
                     "See {} for details".format(bidsunknown))
        if not dry_run:
            with open(bidsunknown, 'w') as stream:
                yaml.dump(d, stream)
