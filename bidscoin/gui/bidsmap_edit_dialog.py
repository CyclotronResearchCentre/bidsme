import logging
import copy

from constants import ICON_FILENAME

from bidseditor import InspectWindow
from gui.tab_attributes_model import tab_attributes_model

from PyQt5 import QtGui
from PyQt5 import QtCore

from PyQt.QtWidgets import QDialog, QLabel
from PyQt.QtWidgets import QHeaderView, QAbstractItemView, QTableView


logger = logging.getLogger(__name__)


class bidsmap_edit_dialog(QDialog):

    def __init__(self, recording, bidsmap, template_bidsmap, parent=None):
        super().__init__(parent)

        if not recording.modality:
            err = "{}: Modality not defined".format(recording.type)
            logger.error(err)
            raise Exception(err)
        if not recording.currentFile():
            recording.loadFile(0)
        if not recording.currentFile():
            err = "{}: Can't load file".format(recording.type)
            logger.error(err)
            raise Exception(err)

        if recording.modality not in bidsmap:
            err = "{}: Missing {} in bidsmap".format(recording.type,
                                                     recording.modality)
            logger.error(err)
            raise Exception(err)

        self.source_bidsmap = bidsmap
        self.target_bidsmap = copy.deepcopy(bidsmap)
        self.template_bidsmap = template_bidsmap

        # Set-up the window
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

        self.provenance_label = QLabel()
        self.provenance_label.setText("Provenance")
        self.provenance_table.setColumnCount(2)
        horizontal_header = self.provenance_table.horizontalHeader()
        horizontal_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        horizontal_header.setSectionResizeMode(1, QHeaderView.Stretch)
        horizontal_header.setVisible(False)
        horizontal_header.setRowCount(4)
        self.provenance_table.setItem(0,0,"Path:")
        self.provenance_table.setItem(1,0,"File:")
        self.provenance_table.setItem(0,1,self.recording.rec_path)
        self.provenance_table.setItem(1,1,self.recording.currentFile())
        self.provenance_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.provenance_table.setToolTip("The {} source file from which the "
                                         "attributes were taken"
                                         .format(recording.type))
        self.provenance_table.cellDoubleClicked.connect(self.inspect_file)

        self.dicom_label = QLabel()
        self.dicom_label.setText("Attributes")
        self.dicom_table = QTableView()
        self.dicom_table.setModel(tab_attributes_model(self.recording,
                                                       self.bidsmap, 
                                                       0))
        self.dicom_table.setToolTip("The {} attributes that are used "
                                    "to uniquely identify source files. "
                                    "NB: Expert usage (e.g. using '*string*' "
                                    "wildcards, see documentation), "
                                    "only change these if you know what "
                                    "you are doing!")

    def inspect_file(self, item):
        self.popup = InspectWindow(self.recording)
