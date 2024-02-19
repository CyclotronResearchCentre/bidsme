###############################################################################
# DICOM.py provides an implementation of PET class for DICOM file format
###############################################################################
# Copyright (c) 2019-2020, University of Liège
# Author: Nikita Beliy
# Owner: Liege University https://www.uliege.be
# Credits: [Marcel Zwiers]
# Maintainer: Nikita Beliy
# Email: Nikita.Beliy@uliege.be
# Status: developpement
###############################################################################
# This file is part of BIDSme
# BIDSme is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# eegBidsCreator is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with BIDSme.  If not, see <https://www.gnu.org/licenses/>.
##############################################################################


from .PET import PET
from . import _DICOM
from .. import _dicom_common

import logging
import pydicom
from datetime import datetime

logger = logging.getLogger(__name__)


class DICOM(PET):
    _type = "DICOM"

    __slots__ = ["_DICOM_CACHE", "_DICOMFILE_CACHE"]

    _file_extentions = [".dcm", ".DCM", ".ima", ".IMA"]

    __specialFields = {}

    def __init__(self, rec_path=""):
        super().__init__()

        self._DICOM_CACHE = None
        self._DICOMFILE_CACHE = ""
        self.switches["exportHeader"] = True

        if rec_path:
            self.setRecPath(rec_path)

    @classmethod
    def _isValidFile(cls, file: str) -> bool:
        """
        Checks whether a file is a DICOM-file.
        It checks if file ends in .dcm or .DCM
        and contains 'DICM' string at 0x80

        Parameters:
        -----------
        file: str
            path to file to test

        Returns:
        --------
        bool:
            True if file is identified as DICOM
        """
        return _dicom_common.isValidDICOM(file, ["PT", "CT"])

    def _loadFile(self, path: str) -> None:
        if path != self._DICOMFILE_CACHE:
            # The DICM tag may be missing for anonymized DICOM files
            dicomdict = pydicom.dcmread(path, stop_before_pixels=True)
            self._DICOMFILE_CACHE = path
            self._DICOM_CACHE = dicomdict
            if self.setManufacturer(self.getField("Manufacturer"),
                                    _DICOM.manufacturers):
                self.resetMetaFields()
                self.setupMetaFields(_DICOM.metafields)
                self.testMetaFields()

    def _getAcqTime(self) -> datetime:
        for Id in ("Acquisition", "Content", "Instance"):
            acq = _dicom_common.combineDateTime(self._DICOM_CACHE, Id)
            if acq is not None:
                return acq
        return None

    def dump(self):
        if self._DICOM_CACHE is None:
            self.loadFile(0)
        res = _dicom_common.extractStruct(self._DICOM_CACHE)
        for f in self.__specialFields:
            res[f] = self._getField([f])
        return res

    def _getField(self, field: list):
        res = None
        try:
            if field[0] in self.__specialFields:
                res = self._adaptMetaField(field[0])
            else:
                res = _dicom_common.retrieveFromDataset(
                        field,
                        self._DICOM_CACHE,
                        fail_on_last_not_found=False)
        except Exception as e:
            logger.warning("{}: Could not parse '{}' for {}"
                           .format(self.currentFile(False), field, e))
            res = None
        return res

    def _recNo(self):
        return self.getField("SeriesNumber", 0)

    def _recId(self):
        seriesdescr = self.getField("SeriesDescription")
        if seriesdescr is None:
            seriesdescr = self.getField("ProtocolName")
        if seriesdescr is None:
            logger.warning("{}: Unable to get recording Id for file {}"
                           .format(self.formatIdentity(),
                                   self.currentFile()))
            seriesdescr = "unknown"
        return seriesdescr.strip().replace('/', ' ').replace('\\', ' ')

    def isCompleteRecording(self):
        return True

    def clearCache(self) -> None:
        del self._DICOM_CACHE
        self._DICOM_CACHE = None
        self._DICOMFILE_CACHE = ""

    def _getSubId(self) -> str:
        return str(self.getField("PatientID"))

    def _getSesId(self) -> str:
        return ""

    ########################
    # Additional fonctions #
    ########################
    def _adaptMetaField(self, name):
        return None
