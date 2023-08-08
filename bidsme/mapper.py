###############################################################################
# mapper.py is a script that tries to identify each recordings in the prepared
# dataset using template map, and creates a local bidsmap
###############################################################################
# Copyright (c) 2018-2020, University of Liège
# Author: Nikita Beliy
# Owner: Liege University https://www.uliege.be
# Credits: [Marcel Zwiers]
# Maintainer: Nikita Beliy
# Email: Nikita.Beliy@uliege.be
# Status: developpement
###############################################################################
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
###############################################################################

import os
import logging
import pandas
import glob

from bidsme import bidsmap
from bidsme import plugins
from bidsme import Modules

from bidsme.tools import paths
from bidsme.tools import info
from bidsme.tools import tools

from bidsme.bidsMeta import BidsSession
from bidsme.bidsMeta import BidsTable

logger = logging.getLogger(__name__)


def createmap(destination,
              recording: Modules.baseModule,
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

    first_name = None

    recording.index = -1
    while recording.loadNextFile():
        if plugins.RunPlugin("RecordingEP", recording) < 0:
            logger.warning("Recording {} discarded by {}"
                           .format(recording.recIdentity(),
                                   "RecordingEP"))
            continue
        # checking in the current map
        modality, r_index, run = bidsmap.match_run(recording)
        if not modality:
            logger.warning("{}/{}: No run found in bidsmap. "
                           "Looking into template"
                           .format(recording.Module(),
                                   recording.recIdentity()))
            # checking in the template map
            modality, r_index, run = template.match_run(recording, fix=True)
            if not modality:
                logger.error("{}/{}: No compatible run found"
                             .format(recording.Module(),
                                     recording.recIdentity()))
                bidsmap_unk.add_run(
                        run,
                        recording.Module(),
                        recording.Type()
                        )
                continue
            run.template = True
            run.checked = False
            modality, r_index, run = bidsmap.add_run(
                    run,
                    recording.Module(),
                    recording.Type()
                    )

        if modality != "__ignore__":
            bidsified_name = "{}/{}".format(modality, recording.getBidsname())
            logger.debug("{}/{}: {}".format(recording.Module(),
                                            recording.recIdentity(),
                                            bidsified_name))
        else:
            bidsified_name = None

        if first_name is None:
            first_name = bidsified_name
        elif modality != "__ignore__":
            if first_name == bidsified_name:
                logger.error("{}/{}: Bidsified name same "
                             "as first file of recording: {}"
                             .format(recording.Module(),
                                     recording.recIdentity(),
                                     bidsified_name))

        if not run.checked:
            if not run.entity:
                run.genEntities(recording.bidsmodalities.get(run.model, []))
            recording.fillMissingJSON(run)
        elif "IntendedFor" in recording.metaAuxiliary:
            sub_path = os.path.join(destination, recording.subId())
            out_path = os.path.join(destination,
                                    recording.getBidsSession().getPath())
            bidsname = recording.getBidsname()
            bidsmodality = os.path.join(out_path, recording.Modality())

            if os.path.isfile(os.path.join(bidsmodality,
                                           bidsname + '.json')):
                # checking the IntendedFor validity
                intended = recording.metaAuxiliary["IntendedFor"]
                for i in intended:
                    dest = os.path.join(sub_path, i.value)
                    if not glob.glob(dest):
                        logger.error("{}/{}({}): IntendedFor value {} "
                                     "not found"
                                     .format(modality, r_index,
                                             run.example, i.value))

    plugins.RunPlugin("SequenceEndEP", None, recording)
    return first_name


def mapper(source: str, destination: str,
           plugin_file: str = "",
           plugin_opt: dict = {},
           sub_list: list = [],
           sub_skip_tsv: bool = False,
           sub_skip_dir: bool = False,
           ses_skip_dir: bool = False,
           process_all: bool = False,
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

    bidscodefolder = os.path.join(destination, 'code', 'bidsme')
    os.makedirs(bidscodefolder, exist_ok=True)

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
                           bidscodefolder,
                           paths.local,
                           paths.config
                           )
    if not fname:
        bidsmapfile = os.path.join(bidscodefolder, bidsmapfile)
    else:
        bidsmapfile = fname
    logger.info("loading working bidsmap {}".format(bidsmapfile))
    bidsmap_new = bidsmap.Bidsmap(bidsmapfile)

    logger.debug("Creating bidsmap for unknown modalities")
    # removing old unknown files
    bidsunknown = os.path.join(bidscodefolder, 'unknown.yaml')
    if os.path.isfile(bidsunknown):
        os.remove(bidsunknown)
    bidsmap_unk = bidsmap.Bidsmap(bidsunknown)

    ###############
    # Plugin setup
    ###############
    if plugin_file:
        plugins.ImportPlugins(plugin_file)
        plugins.InitPlugin(source=source,
                           destination=destination,
                           dry=True,
                           **plugin_opt)

    ###############################
    # Checking participants list
    ###############################

    source_sub_file = os.path.join(source, "participants.tsv")
    source_sub_table = BidsTable(source_sub_file,
                                 index="participant_id",
                                 duplicatedFile="__duplicated.tsv",
                                 checkDefinitions=True)
    source_sub_table.drop_duplicates()
    df_dupl = source_sub_table.check_duplicates()
    if df_dupl.any():
        logger.critical("Participant list contains one or several "
                        "duplicated entries: {}"
                        .format(source_sub_table.getIndexes(df_dupl, True)))
        raise Exception("Duplicated subjects")
    BidsSession.loadSubjectFields(source_sub_table.getDefinitionsPath())

    dest_sub_file = os.path.join(destination, "participants.tsv")
    dest_json_file = os.path.join(paths.templates, "participants.json")
    dest_sub_table = BidsTable(dest_sub_file,
                               index="participant_id",
                               definitionsFile=dest_json_file,
                               duplicatedFile="__duplicated.tsv",
                               checkDefinitions=False)

    ##############################
    # Subjects loop
    ##############################
    n_subjects = len(source_sub_table.df["participant_id"])
    for index, sub_row in source_sub_table.df.iterrows():
        skip_subject = False

        sub_no = index + 1
        sub_id = sub_row["participant_id"]
        sub_dir = os.path.join(source, sub_id)
        if not os.path.isdir(sub_dir):
            logger.error("{}: Not found in {}"
                         .format(sub_id, source))
            continue

        scan = BidsSession()
        scan.in_path = sub_dir
        scan.subject = sub_id

        #################################################
        # Cloning df_sub row values in scans sub_values
        #################################################
        for column in source_sub_table.df.columns:
            if pandas.isna(sub_row[column]):
                scan.sub_values[column] = None
            else:
                scan.sub_values[column] = sub_row[column]

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
                            dest_sub_table.getIndexes()
                            if sub_skip_tsv else None,
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

            bidsified_list = []

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
                    err_count = info.counthandler.level2count.copy()
                    try:
                        first_name = createmap(destination, recording,
                                               bidsmap_new, template,
                                               bidsmap_unk)
                        if first_name in bidsified_list:
                            logger.error("Matches example of "
                                         "already processed run {}"
                                         .format(first_name))
                        elif first_name is not None:
                            bidsified_list.append(first_name)
                    except Exception as err:
                        logger.error("Error processing folder {} "
                                     "in file {}: {}"
                                     .format(run, recording.currentFile(True),
                                             err))
                    err_count = info.msg_count(err_count)
                    if err_count:
                        logger.info("Recording generated several "
                                    "errors/warnings")
                        skip_subject = True and (not process_all)
                        break
                if skip_subject:
                    break
            if skip_subject:
                break
        if skip_subject:
            break

    if not dry_run:
        # Save the bidsmap to the bidsmap YAML-file
        bidsmap_new.save(bidsmapfile, empty_attributes=False)

    # Sanity checks for map
    prov_duplicates, example_duplicates = bidsmap_new.checkSanity()
    dupl_counter = 0
    logger.info("Sanity check:")
    for dupl, count in prov_duplicates.items():
        if count > 1:
            logger.warning("{} matches {} runs"
                           .format(dupl, count))
            dupl_counter += 1
    if dupl_counter == 0:
        logger.info("Passed: No files matching several runs")
    else:
        logger.error("Failed: {} files matching several runs"
                     .format(dupl_counter))
    dupl_counter = 0
    for dupl, count in example_duplicates.items():
        if count > 1:
            logger.warning("{} created by {} runs"
                           .format(dupl, count))
            dupl_counter += 1
    if dupl_counter == 0:
        logger.info("Passed: No examples matching several runs")
    else:
        logger.error("Failed: {} examples matching several runs"
                     .format(dupl_counter))

    ntotal, ntemplate, nunchecked = bidsmap_new.countRuns()
    logger.info("Map contains {} runs".format(ntotal))
    if ntemplate != 0:
        logger.warning("Map contains {} template runs"
                       .format(ntemplate))
    if nunchecked != 0:
        logger.warning("Map contains {} unchecked runs"
                       .format(nunchecked))

    # Scanning unknowing and exporting them to yaml file
    unkn_recordings = bidsmap_unk.countRuns()[0]
    if unkn_recordings > 0:
        logger.error("Was unable to identify {} recordings. "
                     "See {} for details"
                     .format(unkn_recordings, bidsunknown))
        if not dry_run:
            bidsmap_unk.save(bidsunknown)
