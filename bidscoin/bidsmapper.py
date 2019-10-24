#!/usr/bin/env python
"""
Creates a bidsmap.yaml YAML file in the bidsfolder/code/bidscoin that maps the information
from all raw source data to the BIDS labels. You can check and edit the bidsmap file with
the bidseditor (but also with any text-editor) before passing it to the bidscoiner. See the
bidseditor help for more information and useful tips for running the bidsmapper in interactive
mode (which is the default).

N.B.: Institute users may want to use a site-customized template bidsmap (see the
--template option). The bidsmap_dccn template from the Donders Institute can serve as
an example (or may even mostly work for other institutes out of the box).
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
    import bidseditor
    from Modules.MRI.selector import select as MRI_select


LOGGER = logging.getLogger('bidscoin')


def build_bidsmap(recording, bidsmap_new: dict, bidsmap_old: dict, template: dict, gui: object) -> dict:
    """
    All the logic to map recording-attributes (fields/tags) onto bids-labels go into this function

    :param recording:   The instance of recording class 
    :param bidsmap_new: The bidsmap that we are building
    :param bidsmap_old: Full BIDS heuristics data structure, with all options, 
                        BIDS labels and attributes, etc
    :param template:    The bidsmap template with the default heuristics
    :param gui:         If not None, the user will not be asked for help if 
                        an unknown run is encountered
    :return:            The bidsmap with new entries in it
    """

    # Input checks
    if not recording or (not template[recording.type] 
                         and not bidsmap_old[recording.type]):
        LOGGER.info('No {} information found in the bidsmap and template'
                    .format(recording.type))
        return bidsmap_new

    # See if we can find a matching run in the old bidsmap
    run, modality, index = bids.get_matching_run(recording, bidsmap_old)

    # If not, see if we can find a matching run in the template
    if index is None:
        run, modality, _ = bids.get_matching_run(recording, template)

    # See if we have collected the run in our new bidsmap
    if not bids.exist_run(bidsmap_new, recording.type, '', run):

        # Copy the filled-in run over to the new bidsmap
        bidsmap_new = bids.append_run(bidsmap_new, recording.type, modality, run)

        # Communicate with the user if the run was not present in bidsmap_old or in template
        LOGGER.info("New '{}' sample found: {}"
                    .format(modality, recording.files[recording.index]))

        # Launch a GUI to ask the user for help if the new run comes 
        # from the template (i.e. was not yet in the old bidsmap)
        if gui and gui.interactive==2 and index is None:
            # Open the interactive edit window to get the new mapping
            dialog_edit = bidseditor.EditDialog(dicomfile, modality, bidsmap_new, 
                                                template, 
                                                gui.subprefix, gui.sesprefix)
            dialog_edit.exec()

            # Get the result
            if dialog_edit.result() == 1:           # The user has finished the edit
                bidsmap_new = dialog_edit.target_bidsmap
            elif dialog_edit.result() in [0, 2]:    # The user has canceled / aborted the edit
                answer = QMessageBox.question(None, 
                                              'BIDSmapper', 
                                              'Do you want to abort and quit the bidsmapper?',
                                              QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if answer==QMessageBox.No:
                    pass
                if answer==QMessageBox.Yes:
                    LOGGER.info('User has quit the bidsmapper')
                    sys.exit()

            else:
                LOGGER.debug(f'Unexpected result {dialog_edit.result()} from the edit dialog')
    return bidsmap_new


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
            LOGGER.debug(f"Running plug-in: {plugin}.bidsmapper_plugin('{runfolder}', bidsmap_new, bidsmap_old)")
            bidsmap_new = module.bidsmapper_plugin(runfolder, bidsmap_new, bidsmap_old)

    return bidsmap_new


def bidsmapper(rawfolder: str, bidsfolder: str,
               bidsmapfile: str, templatefile: str, 
               subprefix: str='sub-', sesprefix: str='ses-', 
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
    :param subprefix:       The prefix common for all source subject-folders
    :param sesprefix:       The prefix common for all source session-folders
    :param interactive:     If True, the user will be asked for help 
    if an unknown run is encountered
    :return:bidsmapfile:    The name of the mapped bidsmap YAML-file
    """

    # Input checking
    rawfolder  = os.path.abspath(os.path.realpath(os.path.expanduser(rawfolder)))
    bidsfolder = os.path.abspath(os.path.realpath(os.path.expanduser(bidsfolder)))
    bidscodefolder = os.path.join(bidsfolder,'code','bidscoin')

    # Start logging
    bids.setup_logging(os.path.join(bidscodefolder, 'bidsmapper.log'))
    LOGGER.info('')
    LOGGER.info('-------------- START BIDSmapper ------------')

    # Get the heuristics for filling the new bidsmap
    bidsmap_old, _ = bids.load_bidsmap(bidsmapfile,  bidscodefolder)
    template, _    = bids.load_bidsmap(templatefile, bidscodefolder)

    # Create the new bidsmap as a copy / bidsmap skeleton 
    # with no modality entries (i.e. bidsmap with empty lists)
    if bidsmap_old:
        bidsmap_new = copy.deepcopy(bidsmap_old)
    else:
        bidsmap_new = copy.deepcopy(template)
    for logic in ('DICOM', 'PAR', 'P7', 'Nifti_dump', 'FileSystem'):
        if bidsmap_new[logic]:
            for modality in bids.bidsmodalities \
                    + (bids.unknownmodality, bids.ignoremodality):
                if modality in bidsmap_new[logic]:
                    bidsmap_new[logic][modality] = None

    # Start with an empty skeleton if we didn't have an old bidsmap
    if not bidsmap_old:
        bidsmap_old = copy.deepcopy(bidsmap_new)

    # Start the Qt-application
    gui = interactive
    if gui:
        app = QApplication(sys.argv)
        app.setApplicationName('BIDS editor')
        mainwin = bidseditor.MainWindow()
        gui = bidseditor.Ui_MainWindow()
        gui.interactive = interactive
        gui.subprefix = subprefix
        gui.sesprefix = sesprefix

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
    subjects = bids.lsdirs(rawfolder, subprefix + '*')
    if not subjects:
        LOGGER.warning(f'No subjects found in: {os.path.join(rawfolder, subprefix)}*')
        gui = None
    for n, subject in enumerate(subjects,1):

        sessions = bids.lsdirs(subject, sesprefix + '*')
        if not sessions: sessions = [subject]
        for session in sessions:

            LOGGER.info(f'Parsing: {session} (subject {n}/{len(subjects)})')

            for run in bids.lsdirs(session):
                cls = MRI_select(run)
                if cls is not None:
                    t_name = cls.__name__
                    if bidsmap_old[t_name]:
                        recording = cls(run)
                        bidsmap_new = build_bidsmap(recording, bidsmap_new, 
                                                    bidsmap_old, template, 
                                                    gui)

                # Update / append the plugin mapping
                if bidsmap_old['PlugIns']:
                    bidsmap_new = build_pluginmap(run, bidsmap_new, bidsmap_old)

    # Create the bidsmap YAML-file in bidsfolder/code/bidscoin
    os.makedirs(os.path.join(bidsfolder,'code','bidscoin'), exist_ok=True)
    bidsmapfile = os.path.join(bidsfolder,'code','bidscoin','bidsmap.yaml')

    # Save the bidsmap to the bidsmap YAML-file
    bids.save_bidsmap(bidsmapfile, bidsmap_new)

    # (Re)launch the bidseditor UI_MainWindow
    if gui:
        QMessageBox.information(mainwin, 'BIDS mapping workflow',
                                f"The bidsmapper has finished scanning {rawfolder}\n\n"
                                f"Please carefully check all the different BIDS output names "
                                f"and BIDScoin options and (re)edit them to your needs.\n\n"
                                f"You can always redo this step later by re-running the "
                                f"bidsmapper or by just running the bidseditor tool")

        LOGGER.info('Opening the bidseditor')
        gui.setupUi(mainwin, bidsfolder, rawfolder, bidsmapfile, bidsmap_new, copy.deepcopy(bidsmap_new), template, subprefix=subprefix, sesprefix=sesprefix)
        mainwin.show()
        app.exec()

    LOGGER.info('-------------- FINISHED! -------------------')
    LOGGER.info('')

    bids.reporterrors()


# Shell usage
if __name__ == "__main__":

    # Parse the input arguments and run bidsmapper(args)
    import argparse
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=textwrap.dedent(__doc__),
                                     epilog='examples:\n'
                                            '  bidsmapper.py /project/foo/raw /project/foo/bids\n'
                                            '  bidsmapper.py /project/foo/raw /project/foo/bids -t bidsmap_dccn\n ')
    parser.add_argument('sourcefolder',       help='The source folder containing the raw data in sub-#/ses-#/run format (or specify --subprefix and --sesprefix for different prefixes)')
    parser.add_argument('bidsfolder',         help='The destination folder with the (future) bids data and the bidsfolder/code/bidscoin/bidsmap.yaml output file')
    parser.add_argument('-b','--bidsmap',     help='The bidsmap YAML-file with the study heuristics. If the bidsmap filename is relative (i.e. no "/" in the name) then it is assumed to be located in bidsfolder/code/bidscoin. Default: bidsmap.yaml', default='bidsmap.yaml')
    parser.add_argument('-t','--template',    help='The bidsmap template with the default heuristics (this could be provided by your institute). If the bidsmap filename is relative (i.e. no "/" in the name) then it is assumed to be located in bidsfolder/code/bidscoin. Default: bidsmap_template.yaml', default='bidsmap_template.yaml')
    parser.add_argument('-n','--subprefix',   help="The prefix common for all the source subject-folders. Default: 'sub-'", default='sub-')
    parser.add_argument('-m','--sesprefix',   help="The prefix common for all the source session-folders. Default: 'ses-'", default='ses-')
    parser.add_argument('-i','--interactive', help='{0}: The sourcefolder is scanned for different kinds of scans without any user interaction. {1}: The sourcefolder is scanned for different kinds of scans and, when finished, the resulting bidsmap is opened using the bidseditor. {2}: As {1}, except that already during scanning the user is asked for help if a new and unknown run is encountered. This option is most useful when re-running the bidsmapper (e.g. when the scan protocol was changed since last running the bidsmapper). Default: 1', type=int, choices=[0,1,2], default=1)
    parser.add_argument('-v','--version',     help='Show the BIDS and BIDScoin version', action='version', version=f'BIDS-version:\t\t{bids.bidsversion()}\nBIDScoin-version:\t{bids.version()}')
    args = parser.parse_args()

    bidsmapper(rawfolder    = args.sourcefolder,
               bidsfolder   = args.bidsfolder,
               bidsmapfile  = args.bidsmap,
               templatefile = args.template,
               subprefix    = args.subprefix,
               sesprefix    = args.sesprefix,
               interactive  = args.interactive)
