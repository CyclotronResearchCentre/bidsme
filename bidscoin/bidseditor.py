#!/usr/bin/env python
"""
This tool launches a graphical user interface for editing the bidsmap.yaml 
file that is e.g. produced by the bidsmapper or by this bidseditor itself. 
The user can fill in or change the BIDS labels for entries that are 
unidentified or sub-optimal, such that meaningful BIDS output names will be 
generated from these labels. The saved bidsmap.yaml output file can be used 
for converting the source data to BIDS using the bidscoiner.
"""

import os
import sys
import argparse
import textwrap
import logging
import copy
import webbrowser
from functools import partial


from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileSystemModel,
                             QFileDialog, QDialogButtonBox, QTreeView, 
                             QHBoxLayout, QVBoxLayout, QLabel, QDialog, 
                             QMessageBox, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QGroupBox, QTextBrowser,
                             QAbstractItemView, QPushButton, QComboBox, 
                             QDesktopWidget, QAction)

from PyQt5.QtWidgets import QTableView
from PyQt5.QtWidgets import QProgressDialog

try:
    from bidscoin import bids
except ImportError:
    # This should work if bidscoin was not pip-installed
    import bids
    from Modules.MRI.selector import select_by_name as MRI_select_by_name
    from Modules.MRI.selector import select as MRI_select
    from gui.tab_bidsmap_model import tab_bidsmap_model
    from gui.tab_session_model import tab_session_model
    from constants import ROW_HEIGHT, ICON_FILENAME
    from constants import MAIN_HELP_URL, HELP_URL_DEFAULT, HELP_URLS
    from constants import OPTIONS_TOOLTIP_BIDSCOIN, OPTIONS_TOOLTIP_DCM2NIIX
    from constants import EDITOR_EPILOG
    from gui import defaults, Dialogs


LOGGER = logging.getLogger(__name__)

class myWidgetItem(QTableWidgetItem):

    def __init__(self, value: str='', iseditable: bool=True):
        """A QTableWidget that is editable or not"""
        super().__init__()

        self.setText(value)
        self.setEditable(iseditable)

    def setEditable(self, iseditable: bool=True):
        """Make the WidgetItem editable"""

        self.iseditable = iseditable

        if iseditable:
            self.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable)
            self.setForeground(QtGui.QColor('black'))
        else:
            self.setFlags(QtCore.Qt.ItemIsEnabled)
            self.setForeground(QtGui.QColor('gray'))


class myQTableWidget(QTableWidget):

    def __init__(self, minimum: bool=True):
        super().__init__()

        self.setAlternatingRowColors(False)
        self.setShowGrid(False)

        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(ROW_HEIGHT)
        self.setMinimumHeight(2 * (ROW_HEIGHT + 5))
        self.setSizeAdjustPolicy(
                QtWidgets.QAbstractScrollArea.AdjustToContents)

        self.minimizeHeight(minimum)

    def minimizeHeight(self, minimum: bool=True):
        """Set the vertical QSizePolicy to Minimum"""

        self.minimum = minimum

        if minimum:
            self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                               QtWidgets.QSizePolicy.Minimum)
        else:
            self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                               QtWidgets.QSizePolicy.Expanding)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        actionQuit = QAction("Quit", self)
        actionQuit.triggered.connect(self.closeEvent)

        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(ICON_FILENAME), 
                       QtGui.QIcon.Normal, 
                       QtGui.QIcon.Off)
        self.setWindowIcon(icon)

    def closeEvent(self, event):
        """Handle exit. """
        # TODO: Do not use class method but self.something
        QApplication.quit()     


class Ui_MainWindow(MainWindow):

    def setupUi(self, MainWindow, 
                bidsfolder, sourcefolder, 
                bidsmap_filename, 
                input_bidsmap, output_bidsmap, template_bidsmap,
                selected_tab_index=2, 
                subprefix='sub-', sesprefix='ses-', 
                reload: bool=False):

        # Set the data
        self.MainWindow = MainWindow
        self.bidsfolder = bidsfolder
        self.sourcefolder = sourcefolder
        self.bidsmap_filename = bidsmap_filename
        self.input_bidsmap = input_bidsmap
        self.output_bidsmap = output_bidsmap
        self.template_bidsmap = template_bidsmap
        self.subprefix = subprefix
        self.sesprefix = sesprefix

        self.has_edit_dialog_open = None

        self.recording_list = []

        # Set-up the tabs
        self.tabwidget = QtWidgets.QTabWidget()
        tabwidget = self.tabwidget
        tabwidget.setTabPosition(QtWidgets.QTabWidget.North)
        tabwidget.setTabShape(QtWidgets.QTabWidget.Rounded)
        tabwidget.setObjectName("tabwidget")

        self.set_tab_file_browser(sourcefolder)
        self.set_tab_options()
        self.set_tab_bidsmap()
        tabwidget.setTabText(0, "File browser")
        tabwidget.setTabText(1, "Options")
        tabwidget.setTabText(2, "BIDS map")
        tabwidget.setCurrentIndex(selected_tab_index)

        # Set-up the buttons
        buttonBox = QDialogButtonBox()
        buttonBox.setStandardButtons(QDialogButtonBox.Save |
                                     QDialogButtonBox.Reset |
                                     QDialogButtonBox.Help)
        buttonBox.button(QDialogButtonBox.Help)\
            .setToolTip('Go to the online BIDScoin documentation')
        buttonBox.button(QDialogButtonBox.Save)\
            .setToolTip('Save the Options and BIDS-map to disk if '
                        'you are satisfied with all the BIDS output names')
        buttonBox.button(QDialogButtonBox.Reset)\
            .setToolTip('Reload the options and BIDS-map from disk')
        buttonBox.helpRequested.connect(self.get_help)
        buttonBox.button(QDialogButtonBox.Reset).clicked\
            .connect(self.reload)
        buttonBox.button(QDialogButtonBox.Save).clicked\
            .connect(self.save_bidsmap_to_file)

        # Set-up the main layout
        centralwidget = QtWidgets.QWidget(self.MainWindow)
        centralwidget.setLocale(QtCore.QLocale(QtCore.QLocale.English,
                                               QtCore.QLocale.UnitedStates))
        centralwidget.setObjectName("centralwidget")
        top_layout = QtWidgets.QVBoxLayout(centralwidget)
        top_layout.addWidget(tabwidget)
        top_layout.addWidget(buttonBox)

        self.MainWindow.setCentralWidget(centralwidget)

        # Restore the samples_table stretching after the main window 
        # has been sized / current tabindex has been set 
        # (otherwise the main window can become too narrow)
        header = self.samples_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)

        if not reload:
            self.setObjectName("MainWindow")

            self.set_menu_and_status_bar()

            # Center the main window to the center point of screen
            cp = QDesktopWidget().availableGeometry().center()

            # Move rectangle's center point to screen's center point
            self.MainWindow.adjustSize()
            qr = self.MainWindow.frameGeometry()
            qr.moveCenter(cp)

            # Top left of rectangle becomes top left of window centering it
            self.MainWindow.move(qr.topLeft())

    def set_menu_and_status_bar(self):
        # Set the menus
        menubar = QtWidgets.QMenuBar(self.MainWindow)
        menuFile = QtWidgets.QMenu(menubar)
        menuFile.setTitle("File")
        menubar.addAction(menuFile.menuAction())
        menuHelp = QtWidgets.QMenu(menubar)
        menuHelp.setTitle("Help")
        menubar.addAction(menuHelp.menuAction())
        self.MainWindow.setMenuBar(menubar)

        # Set the file menu actions
        actionReload = QAction(self.MainWindow)
        actionReload.setText("Reset")
        actionReload.setStatusTip("Reload the BIDS-map from disk")
        actionReload.setShortcut("Ctrl+R")
        actionReload.triggered.connect(self.reload)
        menuFile.addAction(actionReload)

        actionSave = QAction(self.MainWindow)
        actionSave.setText("Save")
        actionSave.setStatusTip("Save the BIDS-map to disk")
        actionSave.setShortcut("Ctrl+S")
        actionSave.triggered.connect(self.save_bidsmap_to_file)
        menuFile.addAction(actionSave)

        actionExit = QAction(self.MainWindow)
        actionExit.setText("Exit")
        actionExit.setStatusTip("Exit the application")
        actionExit.setShortcut("Ctrl+X")
        actionExit.triggered.connect(self.exit_application)
        menuFile.addAction(actionExit)

        # Set help menu actions
        actionHelp = QAction(self.MainWindow)
        actionHelp.setText("Documentation")
        actionHelp.setStatusTip("Go to the online BIDScoin documentation")
        actionHelp.setShortcut("F1")
        actionHelp.triggered.connect(self.get_help)
        menuHelp.addAction(actionHelp)

        actionBidsHelp = QAction(self.MainWindow)
        actionBidsHelp.setText("BIDS specification")
        actionBidsHelp.setStatusTip("Go to the online BIDS "
                                    "specification documentation")
        actionBidsHelp.setShortcut("F2")
        actionBidsHelp.triggered.connect(self.get_bids_help)
        menuHelp.addAction(actionBidsHelp)

        actionAbout = QAction(self.MainWindow)
        actionAbout.setText("About BIDScoin")
        actionAbout.setStatusTip("Show information about the application")
        actionAbout.triggered.connect(self.show_about)
        menuHelp.addAction(actionAbout)

        # Set the statusbar
        statusbar = QtWidgets.QStatusBar(self.MainWindow)
        statusbar.setObjectName("statusbar")
        statusbar.setStatusTip("Statusbar")
        self.MainWindow.setStatusBar(statusbar)

    def inspect_dicomfile(self, item):
        """When double clicked, show popup window. """
        if item.column() == 1:
            row = item.row()
            filename = self.samples_table.item(row, 5).text()
            dirname, basename = os.path.split(filename)
            cls = MRI_select(dirname)
            if cls is not None:
                recording = cls(rec_path=dirname)
                self.popup = InspectWindow(recording)
                self.popup.show()
                # This can only be done after self.popup.show()
                self.popup.scrollbar.setValue(0)     
            else:
                LOGGER.warning(f"Could not read: {filename}")

    def set_tab_file_browser(self, sourcefolder):
        """Set the raw data folder inspector tab. """
        label = QLabel(sourcefolder)
        label.setWordWrap(True)

        self.model = QFileSystemModel()
        model = self.model
        model.setRootPath('')
        model.setFilter(QtCore.QDir.NoDotAndDotDot | 
                        QtCore.QDir.AllDirs | 
                        QtCore.QDir.Files)
        tree = QTreeView()
        tree.setModel(model)
        tree.setAnimated(False)
        tree.setIndentation(20)
        tree.setSortingEnabled(True)
        tree.setRootIndex(model.index(sourcefolder))
        tree.doubleClicked.connect(self.on_double_clicked)
        tree.header().resizeSection(0, 800)

        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(tree)
        tab1 = QtWidgets.QWidget()
        tab1.setObjectName("filebrowser")
        tab1.setLayout(layout)

        self.tabwidget.addTab(tab1, "")

    def subses_cell_was_changed(self, row, column):
        """
        Subject or session value has been changed 
        in subject-session table. 
        """
        source = "Nifti_dump"
        if column == 1:
            key = self.subses_table.item(row, 0).text()
            value = self.subses_table.item(row, 1).text()
            oldvalue = self.output_bidsmap[source][key]

            # Only if cell was actually clicked, update
            if key and value != oldvalue:
                LOGGER.warning(f"Expert usage: User has set "
                               "{self.SOURCE}['{key}'] "
                               "from '{oldvalue}' to '{value}'")
                self.output_bidsmap[source][key] = value
                self.update_subses_and_samples(self.output_bidsmap)

    def tool_cell_was_changed(self, tool, idx, row, column):
        """Option value has been changed tool options table. """
        if column == 2:
            table = self.tables_options[idx]  # Select the selected table
            key = table.item(row, 1).text()
            value = table.item(row, 2).text()
            oldvalue = self.output_bidsmap["Options"][tool][key]

            # Only if cell was actually clicked, update
            if key and value != oldvalue:
                LOGGER.info(f"User has set {self.SOURCE}['Options']['{key}'] "
                            "from '{oldvalue}' to '{value}'")
                self.output_bidsmap["Options"][tool][key] = value

    def handle_click_test_plugin(self, plugin: str):
        """Test the bidsmap plugin and show the result in a pop-up window

        :param plugin:    Name of the plugin that is being tested
                          in bidsmap['PlugIns']
         """
        if bids.test_plugins(plugin):
            result = 'Passed'
        else:
            result = 'Failed'
        QMessageBox.information(self.MainWindow, "Test", 
                                "Test {plugin}: {result}\n"
                                "See terminal output for more info"
                                .format(plugin, result))

    def handle_click_test_tool(self, tool: str):
        """Test the bidsmap tool and show the result in a pop-up window

        :param tool:    Name of the tool that is being tested 
                        in bidsmap['Options']
         """
        if bids.test_tooloptions(tool, self.output_bidsmap['Options'][tool]):
            result = 'Passed'
        else:
            result = 'Failed'
        QMessageBox.information(self.MainWindow, "Test", 
                                "Test {tool}: {result}\n"
                                "See terminal output for more info"
                                .format(tool, result))

    def handle_click_plugin_add(self):
        """Add a plugin by letting the user select a plugin-file"""
        plugin = QFileDialog.getOpenFileNames(
                self.MainWindow,
                'Select the plugin-file(s)', 
                directory=os.path.join(self.bidsfolder, 'code', 'bidscoin'),
                filter='Python files (*.py *.pyc *.pyo);; All files (*)'
                )
        LOGGER.info(f'Added plugins: {plugin[0]}')
        self.output_bidsmap['PlugIns'] += plugin[0]
        self.update_plugintable()

    def plugin_cell_was_changed(self, row, column):
        """Add / edit a plugin or delete if cell is empty"""
        if column == 1:
            plugin = self.plugin_table.item(row, column).text()
            if plugin and row == len(self.output_bidsmap['PlugIns']):
                LOGGER.info(f"Added plugin: '{plugin}'")
                self.output_bidsmap['PlugIns'].append(plugin)
            elif plugin:
                LOGGER.info("Edited plugin: '{}' -> '{}'"
                            .format(self.output_bidsmap['PlugIns'][row],
                                    plugin)
                            )
                self.output_bidsmap['PlugIns'][row] = plugin
            elif row < len(self.output_bidsmap['PlugIns']):
                LOGGER.info("Deleted plugin: '{}'"
                            .format(self.output_bidsmap['PlugIns'][row]))
                del self.output_bidsmap['PlugIns'][row]
            else:
                LOGGER.error(f"Unexpected cell change for {plugin}")

            self.update_plugintable()

    def update_plugintable(self):
        """
        Plots an extendable table of plugins from 
        self.output_bidsmap['PlugIns']
        """
        plugins = self.output_bidsmap['PlugIns']
        num_rows = len(plugins) + 1

        # Fill the rows of the plugin table
        plugintable = self.plugin_table
        plugintable.disconnect()
        plugintable.setRowCount(num_rows)
        for i, plugin in enumerate(plugins + ['']):
            for j in range(3):
                if j == 0:
                    item = myWidgetItem('path', iseditable=False)
                    plugintable.setItem(i, j, item)
                elif j == 1:
                    item = myWidgetItem(plugin)
                    item.setToolTip('Double-click to edit the name '
                                    'of the plugin in the heuristics '
                                    'folder or the full pathname of '
                                    'the plugin in a custom location')
                    plugintable.setItem(i, j, item)
                elif j == 2:                  # Add the test-button cell
                    test_button = QPushButton('Test')
                    test_button.clicked.connect(
                            partial(self.handle_click_test_plugin, plugin))
                    test_button.setToolTip(f'Click to test {plugin}')
                    plugintable.setCellWidget(i, j, test_button)

        # Append the Add-button cell
        add_button = QPushButton('Select')
        add_button.setToolTip('Click to interactively add a plugin')
        plugintable.setCellWidget(num_rows - 1, 2, add_button)
        add_button.clicked.connect(self.handle_click_plugin_add)

        plugintable.cellChanged.connect(self.plugin_cell_was_changed)

    def set_tab_options(self):
        """Set the options tab.  """

        # Create the tool tables
        bidsmap_options = self.output_bidsmap['Options']

        tool_list = []
        tool_options = {}
        for tool, parameters in bidsmap_options.items():
            # Set the tools
            if tool == "bidscoin":
                tooltip_text = OPTIONS_TOOLTIP_BIDSCOIN
            elif tool == "dcm2niix":
                tooltip_text = OPTIONS_TOOLTIP_DCM2NIIX
            else:
                tooltip_text = tool
            tool_list.append({
                "tool": tool,
                "tooltip_text": tooltip_text
            })
            # Store the options for each tool
            tool_options[tool] = []
            for key, value in parameters.items():
                tool_options[tool].append([
                    {
                        "value": tool,
                        "iseditable": False,
                        "tooltip_text": None
                    },
                    {
                        "value": key,
                        "iseditable": False,
                        "tooltip_text": tooltip_text
                    },
                    {
                        "value": value,
                        "iseditable": True,
                        "tooltip_text": "Double-click to edit the option"
                    }
                ])

        labels = []
        self.tables_options = []

        for n, tool_item in enumerate(tool_list):
            tool = tool_item['tool']
            tooltip_text = tool_item['tooltip_text']
            data = tool_options[tool]
            num_rows = len(data)
            # Always three columns (i.e. tool, key, value) + test-button
            num_cols = len(data[0]) + 1     

            label = QLabel(tool)
            label.setToolTip(tooltip_text)

            tool_table = myQTableWidget()
            tool_table.setRowCount(num_rows)
            tool_table.setColumnCount(num_cols)
            tool_table.setColumnHidden(0, True)  # Hide tool column
            tool_table.setMouseTracking(True)
            horizontal_header = tool_table.horizontalHeader()
            horizontal_header.setSectionResizeMode(
                    0, QHeaderView.ResizeToContents)
            horizontal_header.setSectionResizeMode(
                    1, QHeaderView.ResizeToContents)
            horizontal_header.setSectionResizeMode(2, QHeaderView.Stretch)
            horizontal_header.setSectionResizeMode(3, QHeaderView.Fixed)
            horizontal_header.setVisible(False)

            for i, row in enumerate(data):

                for j, element in enumerate(row):
                    value = element.get("value", "")
                    if value == "None":
                        value = ""
                    iseditable = element.get("iseditable", False)
                    tooltip_text = element.get("tooltip_text", None)
                    item = myWidgetItem(value, iseditable=iseditable)
                    tool_table.setItem(i, j, item)
                    if tooltip_text:
                        tool_table.item(i, j).setToolTip(tooltip_text)

            # Add the test-button cell
            test_button = QPushButton('Test')
            test_button.clicked.connect(
                    partial(self.handle_click_test_tool, tool))
            test_button.setToolTip(f'Click to test the {tool} options')
            tool_table.setCellWidget(0, num_cols - 1, test_button)

            tool_table.cellChanged.connect(
                    partial(self.tool_cell_was_changed, tool, n))

            labels.append(label)
            self.tables_options.append(tool_table)

        # Create the plugin table
        plugin_table = myQTableWidget(minimum=False)
        plugin_label = QLabel('Plugins')
        plugin_label.setToolTip('List of plugins')
        plugin_table.setMouseTracking(True)
        # Always three columns (i.e. path, plugin, test-button)
        plugin_table.setColumnCount(3)   
        horizontal_header = plugin_table.horizontalHeader()
        horizontal_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        horizontal_header.setSectionResizeMode(1, QHeaderView.Stretch)
        horizontal_header.setSectionResizeMode(2, QHeaderView.Fixed)
        horizontal_header.setVisible(False)

        self.plugin_table = plugin_table
        self.update_plugintable()

        # Set-up the tab layout and add the tables
        layout = QVBoxLayout()
        for label, tool_table in zip(labels, self.tables_options):
            layout.addWidget(label)
            layout.addWidget(tool_table)
        layout.addWidget(plugin_label)
        layout.addWidget(plugin_table)
        layout.addStretch(1)

        tab2 = QtWidgets.QWidget()
        tab2.setObjectName("Options")
        tab2.setLayout(layout)

        self.tabwidget.addTab(tab2, "")

    def set_tab_bidsmap(self):
        """Set the SOURCE file sample listing tab.  """

        layout = QVBoxLayout()

        # participants table
        subses_label = QLabel('Participant labels')
        layout.addWidget(subses_label)
        sessions_model = tab_session_model(self.input_bidsmap)
        self.sessions_table = QTableView()
        self.sessions_table.setModel(sessions_model)
        defaults.set_table_default(self.sessions_table, True)

        layout.addWidget(self.sessions_table)

        label = QLabel('Data samples')
        label.setToolTip('List of unique source-data samples')

        samples_model = tab_bidsmap_model(self.input_bidsmap)
        self.samples_table = QTableView()
        self.samples_table.setModel(samples_model)
        defaults.set_table_default(self.samples_table, False)
        self.samples_table.setMouseTracking(True)
        self.samples_table.setShowGrid(True)
        self.samples_table.setSortingEnabled(True)
        self.samples_table.sortByColumn(0, QtCore.Qt.AscendingOrder)
        self.samples_table.doubleClicked.connect(samples_model.sample_clicked)
        sessions_model.valueChanged.connect(samples_model.sub_update)

        layout.addWidget(label)
        layout.addWidget(self.samples_table)
        tab3 = QtWidgets.QWidget()
        tab3.setObjectName("BIDSmapping")
        tab3.setLayout(layout)

        self.tabwidget.addTab(tab3, "")

    def get_help(self):
        """Get online help. """
        webbrowser.open(MAIN_HELP_URL)

    def get_bids_help(self):
        """Get online help. """
        webbrowser.open(HELP_URL_DEFAULT)

    def reload(self):
        """Reset button: reload the original input BIDS map. """
        if self.has_edit_dialog_open:
            self.dialog_edit.reject(confirm=False)

        LOGGER.info('User reloads the bidsmap')
        self.output_bidsmap, _ = bids.load_bidsmap(self.bidsmap_filename)
        self.sessions_table.model().loadBidsmap(self.output_bidsmap)
        self.samples_table.model().loadBidsmap(self.output_bidsmap)

        # Start with a fresh errorlog
        for filehandler in LOGGER.handlers:
            if filehandler.name=='errorhandler' and os.path.getsize(filehandler.baseFilename):
                errorfile = filehandler.baseFilename
                LOGGER.info(f'Resetting {errorfile}')
                # TODO: This works but it is a hack that somehow prefixes 
                # a lot of whitespace to the first LOGGER call
                with open(errorfile, 'w'):          
                    pass

    def save_bidsmap_to_file(self):
        """Check and save the BIDSmap to file. """
        if self.output_bidsmap[self.SOURCE].get('fmap'):
            for run in self.output_bidsmap[self.SOURCE]['fmap']:
                if not run['bids']['IntendedFor']:
                    LOGGER.warning(f"IntendedFor fieldmap value is empty for {run['provenance']}")

        filename, _ = QFileDialog.getSaveFileName(self.MainWindow, 'Save File',
                        os.path.join(self.bidsfolder, 'code', 'bidscoin', 'bidsmap.yaml'),
                        'YAML Files (*.yaml *.yml);;All Files (*)')
        if filename:
            bids.save_bidsmap(filename, self.output_bidsmap)
            QtCore.QCoreApplication.setApplicationName(f'{filename} - BIDS editor')

    def handle_edit_button_clicked(self):
        """Make sure that index map has been updated. """
        button = self.MainWindow.focusWidget()
        rowindex = self.samples_table.indexAt(button.pos()).row()
        modality = self.samples_table.item(rowindex, 2).text()
        provenance = self.samples_table.item(rowindex, 5).text()

        self.open_edit_dialog(provenance, modality)

    def on_double_clicked(self, index):
        filename = self.model.fileInfo(index).absoluteFilePath()
        if os.path.isdir(filename):
            return

        dirname, basename = os.path.split(filename)
        cls = MRI_select(dirname)
        if cls is not None:
            recording = cls(rec_path=dirname)
            self.popup = Dialogs.InspectWindow(recording)
            self.popup.show()
            # This can only be done after self.popup.show()
            self.popup.scrollbar.setValue(0)     
        else:
            LOGGER.warning(f"Could not read: {filename}")

    def show_about(self):
        """ """
        about = f"BIDS editor\n{bids.version()}"
        QMessageBox.about(self.MainWindow, 'About', about)

    def open_edit_dialog(self, provenance, modality, exec=False):
        """Check for open edit window, find the right modality index and open the edit window"""

        if not self.has_edit_dialog_open:
            # Find the source index of the run in the list of runs (using the provenance) and open the edit window
            for run in self.output_bidsmap[self.SOURCE][modality]:
                if run['provenance']==provenance:
                    LOGGER.info(f'User is editing {provenance}')
                    self.dialog_edit = EditDialog(provenance, modality, self.output_bidsmap, self.template_bidsmap, self.subprefix, self.sesprefix)
                    if provenance:
                        self.has_edit_dialog_open = provenance
                    else:
                        self.has_edit_dialog_open = True
                    self.dialog_edit.done_edit.connect(self.update_subses_and_samples)
                    self.dialog_edit.finished.connect(self.release_edit_dialog)
                    if exec:
                        self.dialog_edit.exec()
                    else:
                        self.dialog_edit.show()
                    break

        else:
            # Ask the user if he wants to save his results first before opening a new edit window
            self.dialog_edit.reject()
            if self.has_edit_dialog_open:
                return

            self.open_edit_dialog(provenance, modality, exec)

    def release_edit_dialog(self):
        """Allow a new edit window to be opened"""
        self.has_edit_dialog_open = None

    def exit_application(self):
        """Handle exit. """
        self.MainWindow.close()


class EditDialog(QDialog):
    """
    EditDialog().result() == 1: done with result, i.e. done_edit -> new bidsmap
    EditDialog().result() == 2: done without result
    """

    # Emit the new bidsmap when done
    done_edit = QtCore.pyqtSignal(dict)

    def __init__(self, provenance, modality, bidsmap, template_bidsmap, subprefix='sub-', sesprefix='ses-'):
        super().__init__()

        # Set the data
        self.source_modality  = modality
        self.target_modality  = modality
        self.current_modality = modality
        self.source_bidsmap   = bidsmap
        self.target_bidsmap   = copy.deepcopy(bidsmap)
        self.template_bidsmap = template_bidsmap
        self.subprefix        = subprefix
        self.sesprefix        = sesprefix
        for run in bidsmap[self.SOURCE][modality]:
            if run['provenance'] == provenance:
                self.source_run = run
        self.target_run = copy.deepcopy(self.source_run)
        self.get_allowed_suffixes()

        # Set-up the window
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(ICON_FILENAME), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)
        self.setWindowFlags(QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowMaximizeButtonHint)
        self.setWindowTitle("Edit BIDS mapping")

        # Get data for the tables
        data_provenance, data_dicom, data_bids = self.get_editwin_data()

        # Set-up the provenance table
        self.provenance_label = QLabel()
        self.provenance_label.setText("Provenance")
        self.provenance_table = self.set_table(data_provenance)
        self.provenance_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.provenance_table.setToolTip(f"The {self.SOURCE} source file from which the attributes were taken (Copy: Ctrl+C)")
        self.provenance_table.cellDoubleClicked.connect(self.inspect_dicomfile)

        # Set-up the DICOM table
        self.dicom_label = QLabel()
        self.dicom_label.setText("Attributes")
        self.dicom_table = self.set_table(data_dicom, minimum=False)
        self.dicom_table.cellChanged.connect(self.dicom_cell_was_changed)
        self.dicom_table.setToolTip(f"The {self.SOURCE} attributes that are used to uniquely identify source files. NB: Expert usage (e.g. using '*string*' wildcards, see documentation), only change these if you know what you are doing!")

        # Set-up the modality dropdown menu
        self.set_modality_dropdown_section()
        self.modality_dropdown.setToolTip('The BIDS modality (data type). First make sure this one is correct, then choose the right suffix')

        # Set-up the BIDS table
        self.bids_label = QLabel()
        self.bids_label.setText("Labels")
        self.bids_table = self.set_table(data_bids, minimum=False)
        self.bids_table.setToolTip(f"The BIDS key-value pairs that are used to construct the BIDS output name. Feel free to change the values except for the dynamic 'run' field, which should normally not be touched")
        self.bids_table.cellChanged.connect(self.bids_cell_was_changed)

        # Set-up the BIDS outputname field
        self.set_bids_name_section()

        # Group the tables in boxes
        sizepolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizepolicy.setHorizontalStretch(1)

        groupbox1 = QGroupBox(self.SOURCE + ' input')
        groupbox1.setSizePolicy(sizepolicy)
        layout1 = QVBoxLayout()
        layout1.addWidget(self.provenance_label)
        layout1.addWidget(self.provenance_table)
        layout1.addWidget(self.dicom_label)
        layout1.addWidget(self.dicom_table)
        groupbox1.setLayout(layout1)

        groupbox2 = QGroupBox("BIDS output")
        groupbox2.setSizePolicy(sizepolicy)
        layout2 = QVBoxLayout()
        layout2.addWidget(self.label_dropdown)
        layout2.addWidget(self.modality_dropdown)
        layout2.addWidget(self.bids_label)
        layout2.addWidget(self.bids_table)
        layout2.addWidget(self.label_bids_name)
        layout2.addWidget(self.view_bids_name)
        groupbox2.setLayout(layout2)

        # Add the boxes to the layout
        layout_tables = QHBoxLayout()
        layout_tables.addWidget(groupbox1)
        layout_tables.addWidget(groupbox2)

        # Set-up buttons
        buttonBox = QDialogButtonBox()
        buttonBox.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Reset | QDialogButtonBox.Help)
        buttonBox.button(QDialogButtonBox.Reset).setToolTip('Reset the edits you made')
        buttonBox.button(QDialogButtonBox.Ok).setToolTip('Apply the edits you made and close this window')
        buttonBox.button(QDialogButtonBox.Cancel).setToolTip('Discard the edits you made and close this window')
        buttonBox.button(QDialogButtonBox.Help).setToolTip('Go to the online BIDScoin documentation')
        buttonBox.accepted.connect(self.update_run)
        buttonBox.rejected.connect(partial(self.reject, False))
        buttonBox.helpRequested.connect(self.get_help)
        buttonBox.button(QDialogButtonBox.Reset).clicked.connect(self.reset)

        # Set-up the main layout
        layout_all = QVBoxLayout(self)
        layout_all.addLayout(layout_tables)
        layout_all.addWidget(buttonBox)

        self.center()

        finish = QAction(self)
        finish.triggered.connect(self.closeEvent)

    def center(self):
        """Center the edit window. """
        qr = self.frameGeometry()

        # Center point of screen
        cp = QDesktopWidget().availableGeometry().center()

        # Move rectangle's center point to screen's center point
        qr.moveCenter(cp)

        # Top left of rectangle becomes top left of window centering it
        self.move(qr.topLeft())

    def get_allowed_suffixes(self):
        """Derive the possible suffixes for each modality from the template. """
        allowed_suffixes = {}
        for modality in bids.bidsmodalities + (bids.unknownmodality, bids.ignoremodality):
            allowed_suffixes[modality] = []
            runs = self.template_bidsmap[self.SOURCE][modality]
            if not runs:
                continue
            for run in runs:
                suffix = run['bids'].get('suffix', None)
                if suffix and suffix not in allowed_suffixes[modality]:
                    allowed_suffixes[modality].append(suffix)

        # Sort the allowed suffixes alphabetically
        for modality in bids.bidsmodalities + (bids.unknownmodality, bids.ignoremodality):
            allowed_suffixes[modality] = sorted(allowed_suffixes[modality])

        self.allowed_suffixes = allowed_suffixes

    def get_editwin_data(self) -> tuple:
        """
        Derive the tabular data from the target_run, needed to render the edit window.

        :return: (data_provenance, data_dicom, data_bids)
        """
        data_provenance = [
            [
                {
                    "value": "path",
                    "iseditable": False
                },
                {
                    "value": os.path.dirname(self.target_run['provenance']),
                    "iseditable": False
                },
            ],
            [
                {
                    "value": "filename",
                    "iseditable": False
                },
                {
                    "value": os.path.basename(self.target_run['provenance']),
                    "iseditable": True
                },
            ]
        ]

        data_dicom = []
        for key, value in self.target_run['attributes'].items():
            data_dicom.append([
                {
                    "value": key,
                    "iseditable": False
                },
                {
                    "value": str(value),
                    "iseditable": True
                }
            ])

        data_bids = []
        for bidslabel in bids.bidslabels:
            if bidslabel in self.target_run['bids']:
                if self.target_modality in bids.bidsmodalities and bidslabel=='suffix':
                    iseditable = False
                else:
                    iseditable = True

                data_bids.append([
                    {
                        "value": bidslabel,
                        "iseditable": False
                    },
                    {
                        "value": self.target_run['bids'][bidslabel],
                        "iseditable": iseditable
                    }
                ])

        return data_provenance, data_dicom, data_bids

    def inspect_dicomfile(self, row=None, column=None):
        """When double clicked, show popup window. """
        if row == 1 and column == 1:
            filename = self.target_run['provenance']
            dirname, basename = os.path.split(filename)
            cls = select(dirname)
            if cls is not None:
                recording = cls(rec_path=dirname)
                self.popup = InspectWindow(recording)
                self.popup.show()
                # This can only be done after self.popup.show()
                self.popup.scrollbar.setValue(0)     
            else:
                LOGGER.warning(f"Could not read: {filename}")

    def dicom_cell_was_changed(self, row, column):
        """DICOM attribute value has been changed. """
        if column == 1:
            key = self.dicom_table.item(row, 0).text()
            value = self.dicom_table.item(row, 1).text()
            oldvalue = self.target_run['attributes'].get(key, None)

            # Only if cell was actually clicked, update (i.e. not when BIDS modality changes). TODO: fix
            if key and value!=oldvalue:
                LOGGER.warning(f"Expert usage: User has set {self.SOURCE}['{key}'] from '{oldvalue}' to '{value}' for {self.target_run['provenance']}")
                self.target_run['attributes'][key] = value

    def bids_cell_was_changed(self, row, column):
        """BIDS attribute value has been changed. """
        if column == 1:
            key = self.bids_table.item(row, 0).text()
            value = self.bids_table.item(row, 1).text()
            oldvalue = self.target_run['bids'].get(key, None)

            # Only if cell was actually clicked, update (i.e. not when BIDS modality changes). TODO: fix
            if key and value!=oldvalue:
                # Validate user input against BIDS or replace the (dynamic) bids-value if it is a run attribute
                if not (value.startswith('<<') and value.endswith('>>')):
                    value = bids.cleanup_value(bids.get_dynamic_value(value, self.target_run['provenance']))
                if key == 'run':
                    LOGGER.warning(f"Expert usage: User has set bids['{key}'] from '{oldvalue}' to '{value}' for {self.target_run['provenance']}")
                else:
                    LOGGER.info(f"User has set bids['{key}'] from '{oldvalue}' to '{value}' for {self.target_run['provenance']}")
                self.target_run['bids'][key] = value
                self.bids_table.item(row, 1).setText(value)

                self.refresh_bidsname()

    def fill_table(self, table, data):
        """Fill the table with data"""

        table.blockSignals(True)
        table.clearContents()

        num_rows = len(data)
        table.setRowCount(num_rows)

        self.suffix_dropdown = QComboBox()
        suffix_dropdown = self.suffix_dropdown
        suffix_dropdown.setToolTip("The suffix that sets the different run types apart. First make sure the 'Modality' dropdown-menu is set correctly before chosing the right suffix here")

        for i, row in enumerate(data):
            key = row[0]["value"]
            if self.target_modality in bids.bidsmodalities and key == 'suffix':
                item = myWidgetItem("suffix", iseditable=False)
                table.setItem(i, 0, item)
                labels = self.allowed_suffixes[self.target_modality]
                suffix_dropdown.addItems(labels)
                suffix_dropdown.setCurrentIndex(suffix_dropdown.findText(self.target_run['bids']['suffix']))
                suffix_dropdown.currentIndexChanged.connect(self.suffix_dropdown_change)
                table.setCellWidget(i, 1, suffix_dropdown)
                continue
            for j, element in enumerate(row):
                value = element.get("value", "")
                if value == "None":
                    value = ""
                iseditable = element.get("iseditable", False)
                item = myWidgetItem(value, iseditable=iseditable)
                table.setItem(i, j, item)

        table.blockSignals(False)

    def set_table(self, data, minimum: bool=True) -> QTableWidget:
        """Return a table widget from the data. """
        table = myQTableWidget(minimum=minimum)
        table.setColumnCount(2) # Always two columns (i.e. key, value)
        horizontal_header = table.horizontalHeader()
        horizontal_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        horizontal_header.setSectionResizeMode(1, QHeaderView.Stretch)
        horizontal_header.setVisible(False)

        self.fill_table(table, data)

        return table

    def set_modality_dropdown_section(self):
        """Dropdown select modality list section. """
        self.label_dropdown = QLabel()
        self.label_dropdown.setText("Modality")

        self.modality_dropdown = QComboBox()
        self.modality_dropdown.addItems(bids.bidsmodalities + (bids.unknownmodality, bids.ignoremodality))
        self.modality_dropdown.setCurrentIndex(self.modality_dropdown.findText(self.target_modality))
        self.modality_dropdown.currentIndexChanged.connect(self.modality_dropdown_change)

    def set_bids_name_section(self):
        """Set non-editable BIDS output name section. """
        self.label_bids_name = QLabel()
        self.label_bids_name.setText("Output name")

        self.view_bids_name = QTextBrowser()
        self.view_bids_name.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.view_bids_name.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.view_bids_name.setMinimumHeight(ROW_HEIGHT + 2)

        self.refresh_bidsname()

    def refresh_bidsname(self):
        bidsname = os.path.join(self.target_modality, bids.get_bidsname(self.target_bidsmap[self.SOURCE]['subject'], self.target_bidsmap[self.SOURCE]['session'],
                                                                        self.target_modality, self.target_run, '', self.subprefix, self.sesprefix)) + '.*'

        f = self.view_bids_name.font()
        if self.target_modality==bids.unknownmodality:
            self.view_bids_name.setToolTip(f"Red: This imaging modality is not part of BIDS but will be converted to a BIDS-like entry in the '{bids.unknownmodality}' folder. Click 'OK' if you want your BIDS output data to look like this")
            self.view_bids_name.setTextColor(QtGui.QColor('red'))
            f.setStrikeOut(False)
        elif self.target_modality == bids.ignoremodality:
            self.view_bids_name.setToolTip("Gray / Strike-out: This imaging modality will be ignored and not converted BIDS. Click 'OK' if you want your BIDS output data to look like this")
            self.view_bids_name.setTextColor(QtGui.QColor('gray'))
            f.setStrikeOut(True)
        else:
            self.view_bids_name.setToolTip(f"Green: This '{self.target_modality}' imaging modality is part of BIDS. Click 'OK' if you want your BIDS output data to look like this")
            self.view_bids_name.setTextColor(QtGui.QColor('green'))
            f.setStrikeOut(False)
        self.view_bids_name.setFont(f)
        self.view_bids_name.clear()
        self.view_bids_name.textCursor().insertText(bidsname)

    def refresh(self, suffix_idx):
        """
        Refresh the edit dialog window with a new target_run from the template bidsmap.

        :param suffix_idx: The suffix or index number that will used to extract the run from the template bidsmap
        :return:
        """

        # Get the new target_run
        self.target_run = bids.get_run(self.template_bidsmap, self.SOURCE, self.target_modality, suffix_idx, self.target_run['provenance'])

        # Insert the new target_run in our target_bidsmap
        self.target_bidsmap = bids.update_bidsmap(self.target_bidsmap,
                                                  self.current_modality,
                                                  self.target_run['provenance'],
                                                  self.target_modality,
                                                  self.target_run,
                                                  source=self.SOURCE)

        # Now that we have updated the bidsmap, we can also update the current_modality
        self.current_modality = self.target_modality

        # Refresh the edit window
        self.reset(refresh=True)

    def reset(self, refresh: bool=False):
        """Resets the edit with the target_run if refresh=True or otherwise with the original source_run (=default)"""

        # Reset the target_run to the source_run
        if not refresh:
            LOGGER.info('User resets the BIDS mapping')
            self.current_modality = self.source_modality
            self.target_modality  = self.source_modality
            self.target_run       = copy.deepcopy(self.source_run)
            self.target_bidsmap   = copy.deepcopy(self.source_bidsmap)

            # Reset the modality dropdown menu
            self.modality_dropdown.setCurrentIndex(self.modality_dropdown.findText(self.target_modality))

        # Refresh the DICOM attributes and BIDS values with data from the target_run
        _, data_dicom, data_bids = self.get_editwin_data()

        # Refresh the existing tables
        self.fill_table(self.dicom_table, data_dicom)
        self.fill_table(self.bids_table, data_bids)

        # Refresh the BIDS output name
        self.refresh_bidsname()

    def modality_dropdown_change(self):
        """Update the BIDS values and BIDS output name section when the dropdown selection has been taking place. """
        self.target_modality = self.modality_dropdown.currentText()

        LOGGER.info(f"User has changed the BIDS modality from '{self.current_modality}' to '{self.target_modality}' for {self.target_run['provenance']}")

        self.refresh(0)

    def suffix_dropdown_change(self):
        """Update the BIDS values and BIDS output name section when the dropdown selection has been taking place. """
        target_suffix = self.suffix_dropdown.currentText()

        LOGGER.info(f"User has changed the BIDS suffix from '{self.target_run['bids']['suffix']}' to '{target_suffix}' for {self.target_run['provenance']}")

        self.refresh(target_suffix)

    def get_help(self):
        """Open web page for help. """
        help_url = HELP_URLS.get(self.target_modality, HELP_URL_DEFAULT)
        webbrowser.open(help_url)

    def reject(self, confirm=True):
        """Ask if the user really wants to close the window"""
        if confirm:
            self.raise_()
            answer = QMessageBox.question(self, 'Edit BIDS mapping', "Closing window, do you want to save the changes you made?",
                                          QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)
            if answer == QMessageBox.Yes:
                self.update_run()
                return
            if answer == QMessageBox.No:
                self.done(2)
                LOGGER.info(f'User has discarded the edit')
                return
            if answer == QMessageBox.Cancel:
                return

        LOGGER.info(f'User has canceled the edit')

        super(EditDialog, self).reject()

    def update_run(self):

        if self.target_modality=='fmap' and not self.target_run['bids']['IntendedFor']:
            answer = QMessageBox.question(self, 'Edit BIDS mapping', "The 'IntendedFor' bids-label was not set, which can make that your fieldmap won't be used when "
                                                                     "pre-processing / analyzing the associated imaging data (e.g. fMRI data). Do you want to go back "
                                                                     "and set this label?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Yes)
            if answer == QMessageBox.Yes:
                return

            LOGGER.warning(f"'IntendedFor' fieldmap value was not set")

        LOGGER.info(f'User has approved the edit')

        """Save the changes to the target_bidsmap and send it back to the main window: Finished! """
        self.target_bidsmap = bids.update_bidsmap(self.target_bidsmap,
                                                  self.current_modality,
                                                  self.target_run['provenance'],
                                                  self.target_modality,
                                                  self.target_run,
                                                  source=self.SOURCE)

        self.done_edit.emit(self.target_bidsmap)
        self.done(1)


def bidseditor(bidsfolder: str, sourcefolder: str='', bidsmapfile: str='', templatefile: str='', subprefix='sub-', sesprefix='ses-'):
    """

    :param bidsfolder:
    :param bidsmapfile:
    :param templatefile:
    :return:
    """

    # Start logging
    bids.setup_logging(os.path.join(bidsfolder, 'code', 'bidscoin', 'bidseditor.log'))
    LOGGER.info('')
    LOGGER.info('-------------- START BIDSeditor ------------')

    # Obtain the initial bidsmap info
    bidscoinfolder = os.path.join(bidsfolder,'code','bidscoin')
    template_bidsmap, templatefile = bids.load_bidsmap(templatefile, bidscoinfolder)
    input_bidsmap, bidsmapfile     = bids.load_bidsmap(bidsmapfile,  bidscoinfolder)

    if not input_bidsmap:
        LOGGER.error(f'No bidsmap file found in {bidsfolder}. Please run the bidsmapper first and / or use the correct bidsfolder')
        return

    # loop over all sources in local map
    for SOURCE in input_bidsmap:
        if SOURCE == "Options" or SOURCE == "PlugIns":
            continue
        if input_bidsmap[SOURCE] is None:
            LOGGER.warning("{} declared but not defined in {}"
                           .format(SOURCE, bidsmapfile))
            continue
        # Checking validity of bidsmaps
        if SOURCE not in template_bidsmap or template_bidsmap[SOURCE] is None:
            raise Exception("[{}] not in {} (template)".format(SOURCE, templatefile))
        MRI_cls = MRI_select_by_name(SOURCE)
        if MRI_cls is None:
            LOGGER.error("Can't find class corresponding to {}"
                         .format(SOURCE))
            continue

        modalities = MRI_cls.bidsmodalities 
        for modality in modalities:
            if modality not in template_bidsmap[SOURCE]:
                LOGGER.warning("{} not in {}[{}]".format(modality, templatefile, SOURCE))
            if modality not in input_bidsmap[SOURCE]:
                LOGGER.warning("{} not in {}[{}]".format(modality, fbidsmapile, SOURCE))

        output_bidsmap = copy.deepcopy(input_bidsmap)

        # Parse the sourcefolder from the bidsmap provenance info
        if not sourcefolder:
            # Loop through all bidsmodalities and runs until we find provenance info
            for modality in modalities:
                if input_bidsmap[SOURCE][modality] is None:
                    continue
                for run in input_bidsmap[SOURCE][modality]:
                    if run['provenance']:
                        sourcefolder = os.path.join(os.path.dirname(run['provenance']),
                                                    "../../..")
                        sourcefolder = os.path.normpath(sourcefolder)
                        LOGGER.info('Source: {}'.format(sourcefolder))
                        break
                if sourcefolder:
                    break

    # Start the Qt-application
    app = QApplication(sys.argv)
    app.setApplicationName(f'{bidsmapfile} - BIDS editor [{SOURCE}]')
    mainwin = MainWindow()
    gui = Ui_MainWindow()
    gui.setupUi(mainwin, 
                bidsfolder, sourcefolder, 
                bidsmapfile, input_bidsmap, output_bidsmap, template_bidsmap, 
                subprefix=subprefix, sesprefix=sesprefix)
    mainwin.show()
    app.exec()

    LOGGER.info('-------------- FINISHED! -------------------')
    LOGGER.info('')

    bids.reporterrors()


if __name__ == "__main__":

    # Parse the input arguments and run bidseditor
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=textwrap.dedent(__doc__),
                                     epilog=textwrap.dedent(EDITOR_EPILOG)
                                     )
    parser.add_argument('bidsfolder',
                        help='The destination folder with '
                        'the (future) bids data')
    parser.add_argument('-s','--sourcefolder',
                        help='The source folder containing the raw data. '
                        'If empty, it is derived from the bidsmap provenance '
                        'information')
    parser.add_argument('-b','--bidsmap',
                        help='The bidsmap YAML-file with the study '
                        'heuristics. If the bidsmap filename is relative '
                        '(i.e. no "/" in the name) then it is assumed to be '
                        'located in bidsfolder/code/bidscoin. '
                        'Default: bidsmap.yaml', 
                        default='bidsmap.yaml')
    parser.add_argument('-t','--template',
                        help='The bidsmap template with the default '
                        'heuristics (this could be provided by your '
                        'institute). If the bidsmap filename is relative '
                        '(i.e. no "/" in the name) then it is assumed to be '
                        'located in bidsfolder/code/bidscoin. '
                        'Default: bidsmap_template.yaml',
                        default='bidsmap_template.yaml')
    parser.add_argument('-n','--subprefix',
                        help="The prefix common for all the source "
                        "subject-folders. Default: 'sub-'", 
                        default='sub-')
    parser.add_argument('-m','--sesprefix',
                        help="The prefix common for all the source "
                        "session-folders. Default: 'ses-'",
                        default='ses-')
    args = parser.parse_args()

    bidseditor(bidsfolder=args.bidsfolder,
               sourcefolder=args.sourcefolder,
               bidsmapfile=args.bidsmap,
               templatefile=args.template,
               subprefix=args.subprefix,
               sesprefix=args.sesprefix)
