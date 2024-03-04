#############################################################################
# bidsify.py is a script that bidsifyes prepared dataset accordingly to
# created identification map
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
import pandas

from bidsme import exceptions
from bidsme import plugins
from bidsme import Modules

from bidsme.tools import paths
from bidsme.tools import tools
from bidsme.bidsmap import Bidsmap
from bidsme.bidsMeta import BidsSession
from bidsme.bidsMeta import BidsTable

logger = logging.getLogger(__name__)


def coin(destination: str,
         recording: Modules.baseModule,
         bidsmap: Bidsmap,
         dry_run: bool) -> None:
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

    recording.sub_BIDSvalues["participant_id"] = recording.subId()

    recording.index = -1
    while recording.loadNextFile():
        if plugins.RunPlugin("RecordingEP", recording) < 0:
            logger.warning("Recording {} discarded by {}"
                           .format(recording.recIdentity(),
                                   "RecordingEP"))
            continue

        recording.getBidsSession().registerFields(True)
        out_path = os.path.join(destination,
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
            outfile = recording.bidsify(destination)
            plugins.RunPlugin("FileEP", outfile, recording)
    if not dry_run:
        plugins.RunPlugin("SequenceEndEP", out_path, recording)
    else:
        plugins.RunPlugin("SequenceEndEP", None, recording)


def bidsify(source: str, destination: str,
            plugin_file: str = "",
            plugin_opt: dict = {},
            sub_list: list = [],
            sub_skip_tsv: bool = False,
            sub_skip_dir: bool = False,
            ses_skip_dir: bool = False,
            part_template: str = "",
            bidsmapfile: str = "bidsmap.yaml",
            dry_run: bool = False
            ) -> None:
    """
    Bidsify prepearde dataset in source and place it in
    destination folder.

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
    part_template: str
        path to template json file, from whitch
        participants.tsv will be modeled. If unset
        the defeault one "source/participants.tsv"
        is used. Setting this variable may break
        workflow
    bidsmapfile: str
        The name of bidsmap file, will be searched for
        in destination/code/bidsmap directory, unless
        path is absolute
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

    # Input checking & defaults
    bidscodefolder = os.path.join(destination, 'code', 'bidsme')

    # Create a code/bidsme subfolder
    os.makedirs(bidscodefolder, exist_ok=True)

    # Check for dataset description file
    dataset_file = os.path.join(destination, 'dataset_description.json')
    if not os.path.isfile(dataset_file):
        logger.warning("Dataset description file 'dataset_description.json' "
                       "not found in '{}'".format(destination))

    # Check for README file
    readme_file = os.path.join(destination, 'README')
    if not os.path.isfile(readme_file):
        logger.warning("Dataset readme file 'README' "
                       "not found in '{}'".format(destination))

    # Get the bidsmap heuristics from the bidsmap YAML-file
    fname = paths.findFile(bidsmapfile,
                           bidscodefolder,
                           paths.local,
                           paths.config
                           )
    if not fname:
        logger.critical('Bidsmap file {} not found.'
                        .format(bidsmapfile))
        raise FileNotFoundError(bidsmapfile)
    else:
        bidsmapfile = fname
    logger.info("loading bidsmap {}".format(bidsmapfile))
    bidsmap = Bidsmap(bidsmapfile)

    ntotal, ntemplate, nunchecked = bidsmap.countRuns()
    logger.debug("Map contains {} runs".format(ntotal))
    if ntemplate != 0:
        logger.warning("Map contains {} template runs"
                       .format(ntemplate))
    if nunchecked != 0:
        logger.critical("Map contains {} unchecked runs"
                        .format(nunchecked))
        raise Exception("Unchecked runs present")

    ###############
    # Plugin setup
    ###############
    plugins.ImportPlugins(plugin_file)
    plugins.InitPlugin(source=source,
                       destination=destination,
                       dry=dry_run,
                       **plugin_opt)

    ###############################
    # Checking participants list
    ###############################
    if not part_template:
        part_template = os.path.join(source, "participants.json")
    else:
        logger.warning("Loading exterior participant template {}"
                       .format(part_template))
    BidsSession.loadSubjectFields(part_template)

    source_sub_file = os.path.join(source, "participants.tsv")
    source_sub_table = BidsTable(source_sub_file,
                                 definitionsFile=part_template,
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

    dest_sub_file = os.path.join(destination, "participants.tsv")
    dest_sub_table = BidsTable(dest_sub_file,
                               index="participant_id",
                               definitionsFile=part_template,
                               duplicatedFile="__duplicated.tsv",
                               checkDefinitions=False)

    # df_sub = pandas.read_csv(new_sub_file,
    # old_sub = None

    ##############################
    # Subjects loop
    ##############################
    n_subjects = len(source_sub_table.df["participant_id"])
    for index, sub_row in source_sub_table.df.iterrows():
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
        # locking subjects here allows renaming in bidsification
        # the files will be stored in appropriate folders
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

            for module in Modules.selector.types_list:
                mod_dir = os.path.join(ses_dir, module)
                if not os.path.isdir(mod_dir):
                    logger.debug("Module {} not found in {}"
                                 .format(module, ses_dir))
                    continue
                for run in tools.lsdirs(mod_dir):
                    scan.in_path = run
                    cls = Modules.select(run, module)
                    if cls is None:
                        logger.error("Failed to identify data in {}"
                                     .format(run))
                        continue
                    recording = cls(rec_path=run)
                    if not recording or len(recording.files) == 0:
                        logger.error("unable to load data in folder {}"
                                     .format(run))
                        continue
                    recording.setBidsSession(scan)
                    try:
                        coin(destination, recording, bidsmap, dry_run)
                    except Exception as err:
                        exceptions.ReportError(err)
                        logger.error("Error processing folder {} in file {}"
                                     .format(run, recording.currentFile(True)))
            plugins.RunPlugin("SessionEndEP", scan)

        scan.in_path = sub_dir
        plugins.RunPlugin("SubjectEndEP", scan)

    ##################################
    # Merging the participants table
    ##################################
    df_processed = BidsSession.exportAsDataFrame()

    try:
        dest_sub_table.append(df_processed)
    except Exception as e:
        logger.critical("Failed to merge participants table for: {}"
                        .format(e))
        logger.info("Saving incompatible table to {}"
                    .format(dest_sub_table.getDuplicatesPath()))
        dest_sub_table.write_data(dest_sub_table.getDuplicatesPath(),
                                  df_processed)
    else:
        dest_sub_table.drop_duplicates()
        df_dupl = dest_sub_table.check_duplicates()
        if df_dupl.any():
            logger.critical("Participant list contains one or several "
                            "duplicated entries: {}"
                            .format(dest_sub_table.getIndexes(df_dupl, True))
                            )

        if not dry_run:
            dest_sub_table.save_table(selection=~df_dupl)
            if df_dupl.any():
                logger.info("Saving the list to be merged manually to {}"
                            .format(dest_sub_table.getDuplicatesPath()))
                dest_sub_table.save_table(selection=df_dupl,
                                          useDuplicates=True)

    plugins.RunPlugin("FinaliseEP")
