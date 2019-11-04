import os
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QAbstractTableModel
from PyQt5.QtCore import QVariant

from PyQt5.QtGui import QBrush
from PyQt5.QtGui import QColor

from gui import Dialogs
from Modules.MRI.selector import select_by_name as MRI_select_by_name

logger = logging.getLogger(__name__)


class tab_bidsmap_model(QAbstractTableModel):

    __slots__ = ["rec_list", "run_list", "bidsmap"]

    def __init__(self, bidsmap, parent=None):
        super().__init__(parent)
        self.rec_list = list()
        self.run_list = list()
        self.loadBidsmap(bidsmap)

    def rowCount(self, parent):
        return len(self.rec_list)

    def columnCount(self, parent):
        return 5

    def data(self, index, role):
        row = index.row()
        column = index.column()
        if role == Qt.DisplayRole:
            if column == 0:    # Id column
                return "{:03}".format(row + 1)
            elif column == 1:  # Provenance sample name (short)
                return self.rec_list[row].currentFile(base=True)
            elif column == 2:  # Type
                return self.rec_list[row].type
            elif column == 3:  # Modality
                return self.rec_list[row].modality
            elif column == 4:  # Bidsified name
                return "{}/{}.*".format(self.rec_list[row].modality,
                                        self.rec_list[row].get_bidsname())
        elif role == Qt.ForegroundRole:
            if self.rec_list[row].modality == "__unknown__":
                return QBrush(QColor("red"))
        elif role == Qt.BackgroundRole:
            if self.rec_list[row].modality == "__ignored__":
                return QBrush(QColor("gray"))
        return QVariant()

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section == 0:
                return "Id"
            elif section == 1:
                return "Input file"
            elif section == 2:
                return "Type"
            elif section == 3:
                return "BIDS Modality"
            elif section == 4:
                return "Bidsified name"
        return QVariant()

    def sample_clicked(self, index):
        recording = self.rec_list[index.row()]
        run_id = self.run_list[index.row()]
        if index.column() == 1:
            self.popup = Dialogs.InspectWindow(recording)
            self.popup.show()
            self.popup.scrollbar.setValue(0)
        elif index.column() == 4:
            edit = Dialogs.EditSample(recording, self.bidsmap[recording.type], run_id)
            edit.exec()

    def sub_update(self, source, sub, ses):
        idx_start = -1
        idx_end = -1
        for idx, rec in enumerate(self.rec_list):
            if rec.type == source:
                if idx_start < 0:
                    idx_start = idx 
                idx_end = idx
                rec.Subject = sub
                rec.Session = ses
        if idx_start >= 0:
            self.dataChanged.emit(self.createIndex(idx_start, 4), 
                                  self.createIndex(idx_end, 4))

    def loadBidsmap(self, bidsmap):
        self.rec_list.clear()
        self.run_list.clear()
        self.layoutAboutToBeChanged.emit()
        for source in bidsmap:
            if source in ("Options", "PlugIns"):
                continue
            for modality in bidsmap[source]:
                if modality in ("subject", "session"):
                    continue
                if bidsmap[source][modality]:
                    for run_id, run in enumerate(bidsmap[source][modality]):
                        provenance = os.path.dirname(run['provenance'])
                        try:
                            recording = MRI_select_by_name(source)()
                            recording.modality = modality
                            recording.set_rec_path(provenance)
                            recording.set_attributes(bidsmap[source])
                            recording.set_main_attributes(run)
                            recording.Subject = bidsmap[source]["subject"]
                            recording.Session = bidsmap[source]["session"]
                            recording.set_labels(modality,run)
                            if recording.match_run(run):
                                logger.debug("run matched")
                            else:
                                logger.error("{}-{}: bidsmap do not match file {}"
                                             .format(source, modality, provenance))

                        except Exception as e:
                            logger.error("Failed to load file {}"
                                         .format(provenance))
                            logger.error(str(e))
                            continue
                        self.rec_list.append(recording)
                        self.run_list.append(run_id)
        self.bidsmap = bidsmap
        self.layoutChanged.emit()


