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


class tab_attributes_model(QAbstractTableModel):

    __slots__ = ["recording", "attributes", "bidsmap",
                 "modality", 
                 "run", "run_id",
                 "edited"]

    def __init__(self, recording, bidsmap, run, parent=None):
        super().__init__(parent)
        self.edited = False
        self.recording = recording

        self.bidsmap = bidsmap
        
        self.modality = None
        self.run_id = None
        self.setModality(recording.modality, run)

    def rowCount(self, parent=None):
        return len(self.recording.attributes) + 1

    def columnCount(self, parent=None):
        return 4

    def data(self, index, role):
        if not self.checkIndex(index):
            return QVariant()

        row = index.row()
        column = index.column()

        attr = None
        if row < len(self.attributes):
            attr = self.attributes[row]
            main_att = False
            if attr in self.run["attributes"] and \
                    self.run["attributes"][attr]:
                main_att = True
            else:
                self.run["attributes"][attr] = ""

        if attr is None:
            if role == Qt.DisplayRole and column == 0:
                return "Add"
            else:
                return QVariant()
        if role == Qt.DisplayRole:
            if column == 0:    # Add/remove
                return "Remove"
            if column == 1:    # Attribute name
                return attr
            elif column == 2:  # Pattern
                return str(self.run["attributes"][attr])
            elif column == 3:
                return self.recording.attributes[attr]
        if role == Qt.ForegroundRole:
            if main_att and \
                    not self.recording.match_attribute(
                            attr, self.run["attributes"][attr]):
                return QBrush(QColor("red"))
        if role == Qt.FontRole:
            if column == 1 and main_att:
                font = QFont()
                font.setBold(True)
                return font

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section == 0:
                return "Action"
            if section == 1:
                return "Attribute"
            elif section == 2:
                return "Pattern"
            elif section == 3:
                return "Value"
        return QVariant()

    def flags(self, index):
        flags = super().flags(index)

        if index.column() == 2 and index.row() < len(self.attributes):
            return Qt.ItemIsEditable | flags
        else:
            return flags

    def setData(self, index, value, role):
        if role == Qt.EditRole:
            if not self.checkIndex(index):
                return False
            attr = self.attributes[index.row()]
            self.run["attributes"][attr] = value
            self.dataChanged.emit(self.createIndex(index.row(), 0),
                                  self.createIndex(index.row(), self.columnCount()))
            return True
        return False

    def action_clicked(self, index):
        if index.column() != 0:
            return
        if index.row() < len(self.attributes):
            # delete field
            att = self.attributes[index.row()]
            quest = QMessageBox()
            quest.setText("Remove attribute '{}'?"
                          .format(att))
            quest.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            if quest.exec() == QMessageBox.Yes:
                self.beginRemoveRows(QModelIndex(), index.row(), index.row())
                if att in self.run["attributes"]:
                    del self.run["attributes"][att]
                del self.attributes[index.row()]
                del self.recording.attributes[att]
                self.endRemoveRows()
        else:
            # Add new column
            pass

    def GetModalities(self):
        return [mod for mod in self.recording.bidsmodalities] +\
                        [self.recording.ignoremodality,
                         self.recording.unknownmodality]
    
    def GetRuns(self):
        logger.debug("{}".format(self.modality))
        if self.modality not in self.bidsmap \
               or not self.bidsmap[self.modality]:
           if self.run and "bids" in self.run \
                   and "suffix" in self.run["bids"]:
               return ["{}: {}".format(0, self.run["bids"]["suffix"])]
           else:
               return ["0: undefined"]
        return ["{}: {}".format(ind, run["bids"]["suffix"]) 
               for ind, run in enumerate(self.bidsmap[self.modality])]

    def setModality(self, modality, run):
        if modality not in self.GetModalities():
            raise KeyError("Modality {} not found"
                           .format(recording.modality))
        if modality not in self.bidsmap or not self.bidsmap[modality]:
            # New modality
            self._newModality(modality)
            return
        if modality in self.bidsmap and len(self.bidsmap[modality]) <= run:
            raise KeyError("Run {} out of range"
                           .format(run))
        if run < 0:
            # guessing run
            for run, bmap in enumerate(self.bidsmap[modality]):
                if self.recording.match_run(bmap):
                    break
        if modality != self.modality:
            logger.info("Changing modality from {} to {} for {}"
                        .format(self.modality, modality, 
                                self.recording.currentFile()))
        self.modality = modality
        self._loadRun(run)
            
    def _newModality(self, modality):
        logger.info("Creating new modality for {}"
                    .format(self.recording.currentFile()))
        self.layoutAboutToBeChanged.emit()
        self.run = {"provenance": self.recording.currentFile(),
                    "attributes": {att:"" for att 
                                   in self.recording.attributes},
                    "bids": {}}
        if modality in self.recording.bidsmodalities:
            self.run["bids"] = {tag:"" for tag 
                                in self.recording.bidsmodalities[modality]}
        self.run_id = 0
        self.modality = modality
        self.layoutChanged.emit()

    def _loadRun(self, run):
        self.layoutAboutToBeChanged.emit()
        self.run = copy.deepcopy(
                self.bidsmap[self.modality][run]
                )
        if "provenance" not in self.run:
            logger.warning("Missing 'provenance' for run '{}:{}'"
                           .format(self.modality, self.run_id))
            self.run["provenance"] = self.recording.currentFile()
        if "attributes" not in self.run:
            logger.warning("Missing 'attributes' for run '{}:{}'"
                           .format(self.modality, self.run_id))
            self.run["attributes"] = {att:"" for att in self.recording.attributes}
        if "bids" not in self.run:
            logger.warning("Missing 'bids' for run '{}:{}'"
                           .format(self.modality, self.run_id))
            self.run["bids"] = {}
            if self.modality in self.recording.bidsmodalities:
                self.run["bids"] = {tag:"" for tag
                                    in self.recording.bidsmodalities[modality]}
                self.run["bids"]["suffix"] = ""
        
        for att in self.run["attributes"]:
            self.recording.get_attribute(att)
        self.run_id = run
        self.attributes = list(self.recording.attributes)
        self.layoutChanged.emit()
