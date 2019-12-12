#!/usr/bin/env python
"""
Creates a bidsmap.yaml YAML file in the bidsfolder/code/bidscoin 
that maps the information from all raw source data to the BIDS labels.
You can check and edit the bidsmap file with the bidseditor 
(but also with any text-editor) before passing it to the bidscoiner.
See the bidseditor help for more information and useful tips for running 
the bidsmapper in interactive mode (which is the default).

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
    from tools import tools


logger = logging.getLogger('bidscoin')


def build_pluginmap(runfolder: str, bidsmap_new: dict, bidsmap_old: dict) -> dict:
    """
    Call the plugin to map info onto bids labels

    :param runfolder:   The full-path name of the source folder
    :param bidsmap_new: The bidsmap that we are building
    :param bidsmap_old: Full BIDS heuristics data structure, with all options, BIDS labels and attributes, etc
    :return:            The bidsmap with new entries in it
    """

    # Input checks
    if not runfolder or not bidsmap_new['PlugIns']:
        return bidsmap_new

    for plugin in bidsmap_new['PlugIns']:

        # Load and run the plugin-module
        module = bids.import_plugin(plugin)
        if 'bidsmapper_plugin' in dir(module):
            logger.debug(f"Running plug-in: {plugin}.bidsmapper_plugin('{runfolder}', bidsmap_new, bidsmap_old)")
            bidsmap_new = module.bidsmapper_plugin(runfolder, bidsmap_new, bidsmap_old)

    return bidsmap_new


def bidsmapper(rawfolder: str, bidsfolder: str,
               bidsmapfile: str, templatefile: str, 
               interactive: bool=True) -> None:
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
    :param interactive:     If True, the user will be asked for help 
    if an unknown run is encountered
    :return:bidsmapfile:    The name of the mapped bidsmap YAML-file
    """

    # Input checking
    rawfolder = os.path.abspath(rawfolder)
    bidsfolder = os.path.abspath(bidsfolder)
    bidscodefolder = os.path.join(bidsfolder,'code','bidscoin')

    # Start logging
    bids.setup_logging(os.path.join(bidscodefolder, 'bidsmapper.log'), True)
    logger.info('')
    logger.info('-------------- START BIDSmapper ------------')

    # Get the heuristics for filling the new bidsmap
    # bidsmap_old, _ = bids.load_bidsmap(bidsmapfile, bidscodefolder)
    # template, _ = bids.load_bidsmap(templatefile, bidscodefolder)
    bidsmap_new = bidsmap.bidsmap(bidsmapfile)
    template = bidsmap.bidsmap(templatefile)

    # Start the Qt-application
    gui = interactive
    if gui:
        app = QApplication(sys.argv)
        app.setApplicationName('BIDS editor')
        mainwin = bidseditor.MainWindow()
        gui = bidseditor.Ui_MainWindow()
        gui.interactive = interactive

        if gui.interactive == 2:
            QMessageBox.information(
                    mainwin, 'BIDS mapping workflow',
                    f"The bidsmapper will now scan {bidsfolder} and whenever "
                    f"it detects a new type of scan it will ask you to identify it.\n\n"
                    f"It is important that you choose the correct BIDS modality "
                    f"(e.g. 'anat', 'dwi' or 'func') and suffix (e.g. 'bold' or 'sbref').\n\n"
                    f"At the end you will be shown an overview of all the "
                    f"different scan types and BIDScoin options (as in the "
                    f"bidseditor) that you can then (re)edit to your needs")

    # Loop over all subjects and sessions and built up the bidsmap entries
    subjects = tools.lsdirs(rawfolder, 'sub-*')
    if not subjects:
        logger.warning('No subjects found in: {}/sub-*'
                       .format(rawfolder))
        gui = None

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
                    modality, r_index, r_obj = bidsmap_new.match_run(recording)
                    if not modality:
                        logger.debug("No run found in bidsmap. "
                                    "Looking into template")
                        modality, r_index, r_obj = template.match_run(recording)
                        if not modality:
                            logger.error("{}: No compatible run found"
                                         .format(os.path.basename(run)))
                            continue
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

    # (Re)launch the bidseditor UI_MainWindow
    if gui:
        QMessageBox.information(mainwin, 'BIDS mapping workflow',
                                f"The bidsmapper has finished scanning {rawfolder}\n\n"
                                f"Please carefully check all the different BIDS output names "
                                f"and BIDScoin options and (re)edit them to your needs.\n\n"
                                f"You can always redo this step later by re-running the "
                                f"bidsmapper or by just running the bidseditor tool")

        logger.info('Opening the bidseditor')
        gui.setupUi(mainwin, bidsfolder, rawfolder, bidsmapfile, bidsmap_new, copy.deepcopy(bidsmap_new), template, subprefix=subprefix, sesprefix=sesprefix)
        mainwin.show()
        app.exec()

    logger.info('-------------- FINISHED! -------------------')
    logger.info('')

    bids.reporterrors()


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
                        'bidsfolder/code/bidscoin. '
                        'Default: bidsmap_template.yaml',
                        default='bidsmap_template.yaml')
    parser.add_argument('-i','--interactive',
                        help='{0}: The sourcefolder is scanned for different '
                        'kinds of scans without any user interaction. '
                        '{1}: The sourcefolder is scanned for different kinds '
                        'of scans and, when finished, the resulting bidsmap is '
                        'opened using the bidseditor. '
                        '{2}: As {1}, except that already during scanning '
                        'the user is asked for help if a new and unknown '
                        'run is encountered. This option is most useful when '
                        're-running the bidsmapper (e.g. when the scan '
                        'protocol was changed since last running the bidsmapper). '
                        'Default: 1',
                        type=int, choices=[0,1,2], default=1)
    parser.add_argument('-v','--version',
                        help='Show the BIDS and BIDScoin version',
                        action='version', 
                        version='BIDS-version:\t\t{}\nBIDScoin-version:\t{}'
                        .format(bids.bidsversion(), bids.version()))
    args = parser.parse_args()

    bidsmapper(rawfolder=args.sourcefolder,
               bidsfolder=args.bidsfolder,
               bidsmapfile=args.bidsmap,
               templatefile=args.template,
               interactive=args.interactive)
