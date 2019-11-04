import logging

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QAbstractTableModel
from PyQt5.QtCore import QVariant
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class tab_session_model(QAbstractTableModel):
    __slots__ = ["bidsmap", "sources"]
    valueChanged = pyqtSignal(str, str, str, name="valueChanged")

    def __init__(self, bidsmap, parent=None):
        super().__init__(parent)
        self.loadBidsmap(bidsmap)

    def rowCount(self, parent):
        return len(self.sources)

    def columnCount(self, parent):
        return 3

    def data(self, index, role):
        row = index.row()
        column = index.column()
        tag = self.sources[row]
        if role == Qt.DisplayRole:
            if column == 0:  # Type
                return tag
            elif column == 1:  # Subject
                return str(self.bidsmap[tag]["subject"])
            elif column == 2:  # Session
                return str(self.bidsmap[tag]["session"])
        return QVariant()

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section == 0:
                return "File format"
            elif section == 1:
                return "Subject"
            elif section == 2:
                return "Session"
        return QVariant()

    def setData(self, index, value, role):
        if not isinstance(value, str):
            return False
        if role == Qt.EditRole:
            if not self.checkIndex(index):
                return False
            tag = self.sources[index.row()]
            if index.column() == 1:
                self.bidsmap[tag]["subject"] = value
                self.valueChanged.emit(tag, 
                                       self.bidsmap[tag]["subject"],
                                       self.bidsmap[tag]["session"])
                return True
            elif index.column() == 2:
                self.bidsmap[tag]["session"] = value
                self.valueChanged.emit(tag, 
                                       self.bidsmap[tag]["subject"],
                                       self.bidsmap[tag]["session"])
                return True

    def flags(self, index):
        flags = super().flags(index)

        if index.column() in (1,2):
            return Qt.ItemIsEditable | flags
        else:
            return flags

    def loadBidsmap(self, bidsmap):
        self.layoutAboutToBeChanged.emit()
        self.bidsmap = bidsmap
        self.sources = list()
        for source in self.bidsmap:
            if source in ("Options", "PlugIns"):
                continue
            self.sources.append(source)
            for tag in ("subject", "session"):
                if tag not in self.bidsmap[source]:
                    err = "Missing {} in {} section".format(tag, source)
                    logger.error(err)
                    raise KeyError(err)
        self.layoutChanged.emit()


