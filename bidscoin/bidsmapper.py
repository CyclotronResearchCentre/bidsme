#!/usr/bin/env python
"""
Creates a bidsmap.yaml YAML file in the bidsfolder/code/bidscoin 
that maps the information from all raw source data to the BIDS labels.
Created map can be edited/adjusted manually
"""

import os
import logging
import time
import traceback
import textwrap
import argparse

from tools import info
import tools.tools as tools
from tools.yaml import yaml
import bidsmap
import plugins
import exceptions

import Modules
from bids.BidsSession import BidsSession

logger = logging.getLogger()
logger.name = os.path.splitext(os.path.basename(__file__))[0]
info.setup_logging(logger, 'INFO')

# global maps
bidsmap_new = None
template = None
bidsmap_unk = None


def createmap(recording: Modules.baseModule) -> None:

    logger.info("Processing: sub '{}', ses '{}' ({} files)"
                .format(recording.subId(),
                        recording.sesId(),
                        len(recording.files)))

    recording.index = -1
    while recording.loadNextFile():
        plugins.RunPlugin("RecordingEP", recording)
        # checking in the current map
        modality, r_index, r_obj = bidsmap_new.match_run(recording)
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
            modality, r_index, run = bidsmap_new.add_run(
                    r_obj,
                    recording.Module(),
                    recording.Type()
                    )
            plugins.RunPlugin("SequenceEndEP", None, recording)


def bidsmapper(rawfolder: str, bidsfolder: str,
               bidsmapfile: str, templatefile: str, 
               plugin: str=None,
               options: dict = {}
               ) -> None:
    """
    Main function that processes all the subjects and session 
    in the sourcefolder and that generates a maximally filled-in 
    bidsmap.yaml file in bidsfolder/code/bidscoin.
    Folders in sourcefolder are assumed to contain a single dataset.

    :param rawfolder:       The root folder-name of the sub/ses/data/file 
    tree containing the source data files
    :param bidsfolder:      The name of the BIDS root folder
    :param bidsmapfile:     The name of the bidsmap YAML-file
    :param templatefile:    The name of the bidsmap template YAML-file
    :param plugin:          Path to plugin file to use
    :param options:         A list of parameters passed to plugin
    if an unknown run is encountered
    :return:bidsmapfile:    The name of the mapped bidsmap YAML-file
    """

    # Input checking
    rawfolder = os.path.abspath(rawfolder)
    bidsfolder = os.path.abspath(bidsfolder)
    bidscodefolder = os.path.join(bidsfolder,'code','bidscoin')
    bidsunknown = os.path.join(bidscodefolder, 'unknown.yaml')

    # removing old unknown files
    if os.path.isfile(bidsunknown):
        os.remove(bidsunknown)

    # Get the heuristics for filling the new bidsmap
    global template
    logger.info("loading template bidsmap {}".format(templatefile))
    template = bidsmap.Bidsmap(templatefile)

    global bidsmap_new
    logger.info("loading working bidsmap {}".format(bidsmapfile))
    bidsmap_new = bidsmap.Bidsmap(bidsmapfile)
    if plugin:
        bidsmap_new.plugin_file = plugin
    if options:
        bidsmap_new.plugin_options = options

    global bidsmap_unk
    logger.info("creating bidsmap for unknown modalities")
    bidsmap_unk = {mod:{t.__name__:list() 
                        for t in types}
                   for mod, types in Modules.selector.types_list.items()}

    if bidsmap_new.plugin_file:
        plugins.ImportPlugins(bidsmap_new.plugin_file)
        plugins.InitPlugin(source=rawfolder,
                           destination=bidsfolder,
                           dry=True,
                           **bidsmap_new.plugin_options)

    # Loop over all subjects and sessions and built up the bidsmap entries
    subjects = tools.lsdirs(rawfolder, 'sub-*')
    if not subjects:
        logger.critical('No subjects found in: {}'
                        .format(rawfolder))
        raise ValueError("No subjects found")

    for n, subject in enumerate(subjects,1):
        scan = BidsSession()
        scan.in_path = subject
        scan.subject = os.path.basename(subject)
        plugins.RunPlugin("SubjectEP", scan)
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
                    recording.setBidsSession(scan)
                    plugins.RunPlugin("SequenceEP", recording)
                    createmap(recording)

    # Create the bidsmap YAML-file in bidsfolder/code/bidscoin
    os.makedirs(os.path.join(bidsfolder,'code','bidscoin'), exist_ok=True)
    bidsmapfile = os.path.join(bidsfolder,'code','bidscoin','bidsmap.yaml')

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
        with open(bidsunknown, 'w') as stream:
            yaml.dump(d, stream)


# Shell usage
if __name__ == "__main__":
    # Parse the input arguments and run bidsmapper(args)
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

    parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=textwrap.dedent(__doc__),
            epilog='examples:\n'
            '  bidsmapper.py /project/foo/raw /project/foo/bids\n'
            '  bidsmapper.py /project/foo/raw /project/foo/bids '
            '-t bidsmap_dccn\n ')
    parser.add_argument('sourcefolder',
                        help='The source folder containing the raw data '
                        'in sub-#/ses-#/run format (or specify --subprefix '
                        'and --sesprefix for different prefixes)')
    parser.add_argument('bidsfolder',
                        help='The destination folder with the (future) bids '
                        'data and the bidsfolder/code/bidscoin/bidsmap.yaml '
                        'output file')
    parser.add_argument('-b','--bidsmap',
                        help='The bidsmap YAML-file with the study '
                        'heuristics. If the bidsmap filename is relative '
                        '(i.e. no "/" in the name) then it is assumed to '
                        'be located in bidsfolder/code/bidscoin. '
                        'Default: bidsmap.yaml',
                        default='bidsmap.yaml')
    parser.add_argument('-t','--template',
                        help='The bidsmap template with the default '
                        'heuristics (this could be provided by your '
                        'institute). If the bidsmap filename is relative '
                        '(i.e. no "/" in the name) then it is assumed '
                        'to be located in bidscoin/heuristics/. '
                        'Default: bidsmap_template.yaml',
                        default='bidsmap_template.yaml')
    parser.add_argument('-p','--plugin',
                        help='Path to plugin file intended to be used with '
                        'bidsification. This needed only for creation of '
                        'new file')
    parser.add_argument('-o',
                        metavar="OptName=OptValue",
                        dest="plugin_opt",
                        help="Options passed to plugin in form "
                        "-o OptName=OptValue, several options can be passed",
                        action=appPluginOpt,
                        default={},
                        nargs="+"
                        )
    parser.add_argument('-v','--version',
                        help='Show the BIDS and BIDScoin version',
                        action='version', 
                        version='BIDS-version:\t\t{}\nBIDScoin-version:\t{}'
                        .format(info.bidsversion(), info.version()))
    args = parser.parse_args()

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
    if os.path.dirname(args.template) == "":
        args.template = os.path.join(os.path.dirname(__file__),
                                     "../heuristics",
                                     args.template)
    if args.plugin:
        if not os.path.isfile(args.plugin):
            logger.critical("Plugin file {} not found"
                            .format(args.plugin))
            raise FileNotFoundError("Plugin file {} not found"
                                    .format(args.plugin))

    info.addFileLogger(logger, os.path.join(os.path.join(args.bidsfolder,
                                                         "code/bidscoin",
                                                         "log")))

    code = 0
    # Start logging
    logger.info('')
    logger.info('-------------- START BIDSmapper ------------')
    logger.info('bidscoin ver {}'.format(info.version()))
    logger.info('bids ver {}'.format(info.bidsversion()))

    try:
        bidsmapper(rawfolder=args.sourcefolder,
                   bidsfolder=args.bidsfolder,
                   bidsmapfile=args.bidsmap,
                   templatefile=args.template,
                   plugin=args.plugin,
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
