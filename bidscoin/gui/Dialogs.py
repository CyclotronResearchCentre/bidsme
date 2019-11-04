import logging

from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                             QLabel, QTextBrowser, QDialogButtonBox,
                             QTableWidget, QTableWidgetItem,
                             QAbstractItemView,
                             QTableView, QGroupBox, QComboBox)

from constants import ICON_FILENAME

from gui import defaults
from gui.tab_attributes_model import tab_attributes_model
from gui.tab_bids_model import tab_bids_model

logger = logging.getLogger(__name__)


class InspectWindow(QDialog):
    def __init__(self, recording, parent=None):
        super().__init__(parent)

        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(ICON_FILENAME),
                       QtGui.QIcon.Normal,
                       QtGui.QIcon.Off)
        self.setWindowIcon(icon)
        self.setWindowTitle("Inspect {} file".format(recording.type))

        layout = QVBoxLayout(self)
        dirname = recording.rec_path
        filename = recording.currentFile()

        label_path = QLabel('Path: ' + dirname)
        label_path.setWordWrap(True)
        label_path.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        layout.addWidget(label_path)

        label = QLabel('Filename: ' + filename)
        label.setWordWrap(True)
        label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        layout.addWidget(label)

        try:
            text = recording.dump()
        except ValueError as e:
            err = "No valid file '{}' in {}".format(filename,
                                                    recording.rec_path)
            logger.error(err)
            text = err
        except Exception as e:
            err = str(e)
            logger.error(err)

        textBrowser = QTextBrowser(self)
        textBrowser.insertPlainText(text)
        textBrowser.setLineWrapMode(False)
        # For setting the slider to the top
        # (can only be done after self.show()
        self.scrollbar = textBrowser.verticalScrollBar()
        layout.addWidget(textBrowser)

        buttonBox = QDialogButtonBox(self)
        buttonBox.setStandardButtons(QDialogButtonBox.Ok)
        buttonBox.button(QDialogButtonBox.Ok).setToolTip('Close this window')
        layout.addWidget(buttonBox)

        # Set the width to the width of the text
        fontMetrics = QtGui.QFontMetrics(textBrowser.font())
        textwidth = fontMetrics.size(0, text).width()
        self.resize(min(textwidth + 70, 1200), self.height())

        buttonBox.accepted.connect(self.close)


class EditSample(QDialog):
    __slots__ = ["recording", "bidsmap"]

    def __init__(self, recording, bidsmap, run):
        super().__init__()

        self.recording = recording
        self.bidsmap = bidsmap

        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(ICON_FILENAME), 
                       QtGui.QIcon.Normal, 
                       QtGui.QIcon.Off)
        self.setWindowIcon(icon)
        self.setWindowFlags(QtCore.Qt.WindowSystemMenuHint | 
                            QtCore.Qt.WindowTitleHint | 
                            QtCore.Qt.WindowCloseButtonHint | 
                            QtCore.Qt.WindowMaximizeButtonHint)
        self.setWindowTitle("Edit BIDS mapping")

        # Set-up the provenance table
        provenance_label = QLabel("Provenance")
        self.provenance_table = QTableWidget()
        self.provenance_table.setRowCount(2)
        self.provenance_table.setItem(0,0, QTableWidgetItem("Path"))
        self.provenance_table.setItem(0,1, QTableWidgetItem(recording.rec_path))
        self.provenance_table.setItem(1,0, QTableWidgetItem("File"))
        self.provenance_table.setItem(1,1, QTableWidgetItem(recording.currentFile(True)))
        defaults.set_table_default(self.provenance_table, True)
        self.provenance_table.setEditTriggers(
                QAbstractItemView.NoEditTriggers)
        self.provenance_table.setToolTip("The {} source file from which "
                                         "the attributes were taken "
                                         "(Copy: Ctrl+C)"
                                         .format(self.recording.type))
        self.provenance_table.cellDoubleClicked.connect(self.inspect_file)

        self.dicom_label = QLabel()
        self.dicom_label.setText("Attributes")
        self.attributes = tab_attributes_model(recording, bidsmap, run)
        self.attributes_table = QTableView()
        self.attributes_table.setModel(self.attributes)
        defaults.set_table_default(self.attributes_table, False)
        self.attributes_table.doubleClicked.connect(self.attributes.action_clicked)

        groupbox1 = QGroupBox(recording.type + ' input')
        layout1 = QVBoxLayout()
        layout1.addWidget(provenance_label)
        layout1.addWidget(self.provenance_table)
        layout1.addWidget(self.dicom_label)
        layout1.addWidget(self.attributes_table)
        groupbox1.setLayout(layout1)

        groupbox2 = QGroupBox("BIDS output")
        layout2 = QVBoxLayout()

        # Modality selection
        label_dropdown = QLabel("Modality")
        self.modality_dropdown = QComboBox()
        self.modality_dropdown.addItems(self.attributes.GetModalities())
        self.modality_dropdown.setCurrentIndex(
                self.modality_dropdown.findText(
                    self.attributes.recording.modality))
        self.modality_dropdown.currentIndexChanged.connect(
                self.modality_dropdown_change)
        layout2.addWidget(label_dropdown)
        layout2.addWidget(self.modality_dropdown)

        # Run (suffix) selection
        label_bids = QLabel("Run")
        self.run_dropdown = QComboBox()
        self.run_dropdown.addItems(self.attributes.GetRuns())
        layout2.addWidget(label_bids)
        layout2.addWidget(self.run_dropdown)
        self.run_dropdown.currentIndexChanged.connect(
                self.run_dropdown_change)
        self.bids = tab_bids_model(self.recording)
        bids_table = QTableView()
        bids_table.setModel(self.bids)
        layout2.addWidget(bids_table)
        #layout2.addWidget(self.label_bids_name)
        #layout2.addWidget(self.view_bids_name)

        groupbox2.setLayout(layout2)

        # Add the boxes to the layout
        layout_tables = QHBoxLayout()
        layout_tables.addWidget(groupbox1)
        layout_tables.addWidget(groupbox2)

        # Set-up buttons
        buttonBox = QDialogButtonBox()
        buttonBox.setStandardButtons(QDialogButtonBox.Ok | 
                                     QDialogButtonBox.Cancel | 
                                     QDialogButtonBox.Reset | 
                                     QDialogButtonBox.Help)
        buttonBox.button(QDialogButtonBox.Reset).setToolTip('Reset the edits you made')
        buttonBox.button(QDialogButtonBox.Ok).setToolTip('Apply the edits you made and close this window')
        buttonBox.button(QDialogButtonBox.Cancel).setToolTip('Discard the edits you made and close this window')
        buttonBox.button(QDialogButtonBox.Help).setToolTip('Go to the online BIDScoin documentation')

        # buttonBox.accepted.connect(self.attributes.update_run)
        # buttonBox.rejected.connect(partial(self.reject, False))
        # buttonBox.helpRequested.connect(self.get_help)
        # buttonBox.button(QDialogButtonBox.Reset).clicked.connect(self.reset)

        # Set-up the main layout
        layout_all = QVBoxLayout(self)
        layout_all.addLayout(layout_tables)
        layout_all.addWidget(buttonBox)

    def inspect_file(self, row=None, column=None):
        """When double clicked, show popup window. """
        if row == 1 and column == 1:
            self.popup = InspectWindow(self.recording)
            self.popup.show()
            # This can only be done after self.popup.show()
            self.popup.scrollbar.setValue(0)

    def modality_dropdown_change(self):
        self.attributes.setModality(self.modality_dropdown.currentText(), -1)
        self.run_dropdown.clear()
        self.run_dropdown.addItems(self.attributes.GetRuns())
        self.bids.setTags(self.attributes.modality, 
                          self.attributes.run["bids"])

    def run_dropdown_change(self):
        self.attributes.setModality(self.attributes.modality,
                                    self.run_dropdown.currentIndex())
        self.bids.updateTags(self.attributes.run["bids"])
