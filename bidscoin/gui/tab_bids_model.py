import logging
import copy

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QAbstractTableModel
from PyQt5.QtCore import QVariant
from PyQt5.QtCore import QModelIndex

from PyQt5.QtGui import QBrush
from PyQt5.QtGui import QFont
from PyQt5.QtGui import QColor

from PyQt5.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)


class tab_bids_model(QAbstractTableModel):

    __slots__ = ["edited", "sub", "ses", "suffix", "tags", "values",
                 "recording"]

    def __init__(self, recording):
        super().__init__()
        self.edited = False
        self.recording = recording
        self.sub = recording.getSubId()
        self.ses = recording.getSesId()
        self.suffix = recording.suffix
        self.tags = recording.bidsmodalities[recording.modality]
        self.values = copy.deepcopy(recording.labels)

    def rowCount(self, parent=None):
        return len(self.tags) + 3

    def columnCount(self, index, parent=None):
        return 1

    def data(self, index, role):
        if not self.checkIndex(index):
            return QVariant()
        row = index.row()
        column = index.column()

        if role == Qt.DisplayRole:
            if row == 0:
                return self.sub
            elif row == 1:
                return self.ses
            elif row == 2:
                return self.suffix
            else:
                return str(self.values[row - 3])

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Vertical:
            if section == 0:
                return "Subject"
            if section == 1:
                return "Session"
            if section == 2:
                return "Suffix"
            else:
                return str(self.tags[section - 3])

    def setTags(self, modality, run):
        self.layoutAboutToBeChanged.emit()
        if modality in self.recording.bidsmodalities:
            self.tags = self.recording.bidsmodalities[self.recording.modality]
            self.suffix = run["suffix"]
        else:
            self.tags = list()
            self.suffix = ""
        self.values = [""] * len(self.tags)
        for idx,tag in enumerate(self.tags):
            if tag in run and run[tag]:
                self.values[idx] = run[tag]
        self.layoutChanged.emit()

    def updateTags(self, run):
        self.layoutAboutToBeChanged.emit()
        self.values = [""] * len(self.tags)
        for idx,tag in enumerate(self.tags):
            if tag in run and run[tag]:
                self.values[idx] = run[tag]
        self.suffix = run["suffix"]
        self.layoutChanged.emit()
