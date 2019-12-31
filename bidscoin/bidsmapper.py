#!/usr/bin/env python
"""
Creates a bidsmap.yaml YAML file in the bidsfolder/code/bidscoin 
that maps the information from all raw source data to the BIDS labels.
You can check and edit the bidsmap file with the bidseditor 
(but also with any text-editor) before passing it to the bidscoiner.
See the bidseditor help for more information.

N.B.: Institute users may want to use a site-customized template bidsmap
(see the --template option). The bidsmap_dccn template from 
the Donders Institute can serve as an example (or may even mostly work 
for other institutes out of the box).
"""

# Global imports (plugin modules may be imported when needed)
import os.path
import textwrap
import copy
import logging
import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
try:
    from bidscoin import bids
    from bidscoin import bidseditor
except ImportError:
    import bids         # This should work if bidscoin was not pip-installed
    # import bidseditor
    from Modules.MRI import selector
    import bidsmap
    from tools import info
    from tools import tools
    from tools.yaml import yaml


logger = logging.getLogger()
logger.name = os.path.splitext(os.path.basename(__file__))[0]


def bidsmapper(rawfolder: str, bidsfolder: str,
               bidsmapfile: str, templatefile: str, 
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
    if an unknown run is encountered
    :return:bidsmapfile:    The name of the mapped bidsmap YAML-file
    """

    # Input checking
    rawfolder = os.path.abspath(rawfolder)
    bidsfolder = os.path.abspath(bidsfolder)
    bidscodefolder = os.path.join(bidsfolder,'code','bidscoin')
    bidsunknown = os.path.join(bidscodefolder, 'unknown.yaml')

    # Start logging
    info.setup_logging(logger, bidscodefolder, 'INFO')
    logger.info('')
    logger.info('-------------- START BIDSmapper ------------')
    logger.info('bidscoin ver {}'.format(info.version()))
    logger.info('bids ver {}'.format(info.bidsversion()))

    # removing old unknown files
    if os.path.isfile(bidsunknown):
        os.remove(bidsunknown)

    # Get the heuristics for filling the new bidsmap
    # bidsmap_old, _ = bids.load_bidsmap(bidsmapfile, bidscodefolder)
    # template, _ = bids.load_bidsmap(templatefile, bidscodefolder)
    logger.info("loading template bidsmap {}".format(templatefile))
    template = bidsmap.bidsmap(templatefile)
    
    logger.info("loading working bidsmap {}".format(bidsmapfile))
    bidsmap_new = bidsmap.bidsmap(bidsmapfile)

    logger.info("creating bidsmap for unknown modalities")
    bidsmap_unk = {mod:{t.__name__:list() 
                        for t in types}
                   for mod, types in selector.types_list.items()}

    # Loop over all subjects and sessions and built up the bidsmap entries
    subjects = tools.lsdirs(rawfolder, 'sub-*')
    if not subjects:
        logger.warning('No subjects found in: {}/sub-*'
                       .format(rawfolder))

    for n, subject in enumerate(subjects,1):
        sessions = tools.lsdirs(subject, 'ses-*')
        if not sessions: sessions = [subject]
        for session in sessions:
            for module in selector.types_list:
                mod_dir = os.path.join(session, module)
                if not os.path.isdir(mod_dir):
                    logger.debug("Module {} not found in {}"
                                 .format(module, session))
                    continue
                logger.info('Parsing: {} (subject {}/{})'
                            .format(mod_dir, n, len(subjects)))

                for run in tools.lsdirs(mod_dir):
                    cls = selector.select(run, module)
                    if cls is None:
                        logger.warning("Failed to identify data in {}"
                                       .format(mod_dir))
                        continue
                    t_name = cls.get_type()
                    recording = cls(rec_path=run)
                    recording.index = -1
                    while recording.loadNextFile():
                        modality, r_index, r_obj = bidsmap_new.match_run(recording)
                        if not modality:
                            logger.warning("No run found in bidsmap. "
                                           "Looking into template")
                            modality, r_index, r_obj = template.match_run(recording,
                                                                          fix=True)
                            if not modality:
                                logger.error("{}: No compatible run found"
                                             .format(os.path.basename(run)))
                                bidsmap_unk[module][t_name]\
                                        .append({"provenance":recording.currentFile(),
                                                 "attributes":recording.attributes})
                                continue
                            r_obj.template = True
                            modality, r_index, run = bidsmap_new.add_run(
                                    r_obj,
                                    recording.Module,
                                    recording.get_type()
                                    )

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

    logger.info('-------------- FINISHED! -------------------')
    logger.info('')

    info.reporterrors(logger)


# Shell usage
if __name__ == "__main__":

    # Parse the input arguments and run bidsmapper(args)
    import argparse
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
                        help='The bidsmap YAML-file with the study heuristics. ' 
                        'If the bidsmap filename is relative (i.e. no "/" in '
                        'the name) then it is assumed to be located in '
                        'bidsfolder/code/bidscoin. Default: bidsmap.yaml',
                        default='bidsmap.yaml')
    parser.add_argument('-t','--template',
                        help='The bidsmap template with the default '
                        'heuristics (this could be provided by your institute).'
                        'If the bidsmap filename is relative (i.e. no "/" '
                        'in the name) then it is assumed to be located in '
                        'bidscoin/heuristics/. '
                        'Default: bidsmap_template.yaml',
                        default='bidsmap_template.yaml')
    parser.add_argument('-v','--version',
                        help='Show the BIDS and BIDScoin version',
                        action='version', 
                        version='BIDS-version:\t\t{}\nBIDScoin-version:\t{}'
                        .format(info.bidsversion(), info.version()))
    args = parser.parse_args()

    if os.path.dirname(args.bidsmap) == "":
        args.bidsmap = os.path.join(args.bidsfolder, 
                                    "code/bidscoin",
                                    args.bidsmap)
    if os.path.dirname(args.template) == "":
        args.template = os.path.join(os.path.dirname(__file__),
                                     "../heuristics",
                                     args.template)
    bidsmapper(rawfolder=args.sourcefolder,
               bidsfolder=args.bidsfolder,
               bidsmapfile=args.bidsmap,
               templatefile=args.template)
