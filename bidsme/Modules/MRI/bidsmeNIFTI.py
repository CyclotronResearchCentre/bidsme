###############################################################################
# bidsmeNIFTI.py provides an implementation of MRI class for Nifti file format
# with dumped DICOM header in form of json file
###############################################################################
# Copyright (c) 2019-2020, University of Liège
# Author: Nikita Beliy
# Owner: Liege University https://www.uliege.be
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

from ..common import retrieveFormDict
from .MRI import MRI
from . import _DICOM

import os
import logging
import shutil
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class bidsmeNIFTI(MRI):
    _type = "bidsmeNIFTI"

    __slots__ = ["_HEADER_CACHE", "_FILE_CACHE",
                 "_header_file"
                 ]
    __specialFields = {"acq_time"}

    def __init__(self, rec_path=""):
        super().__init__()

        self._HEADER_CACHE = None
        self._FILE_CACHE = ""
        self._header_file = ""

        if rec_path:
            self.setRecPath(rec_path)

    ################################
    # reimplementation of virtuals #
    ################################
    @classmethod
    def _isValidFile(cls, file: str) -> bool:
        """
        Checks whether a file is a NII file
        with a valid dump of DICOM header

        Parameters
        ----------
        file: str
            path to file to test

        Returns
        -------
        bool:
            True if file is identified as NIFTI
        """

        if os.path.isfile(file) and file.endswith(".nii"):
            if os.path.basename(file).startswith('.'):
                logger.warning('{}: file {} is hidden'
                               .format(cls.formatIdentity(),
                                       file))
                return False
            path, base = os.path.split(file)
            base, ext = os.path.splitext(base)
            header = os.path.join(path, "dcm_dump_" + base + ".json")
            if os.path.isfile(header):
                return True
        return False

    def _loadFile(self, path: str) -> None:
        if path != self._FILE_CACHE:
            # The DICM tag may be missing for anonymized DICOM files
            path, base = os.path.split(path)
            base, ext = os.path.splitext(base)
            header = os.path.join(path, "dcm_dump_" + base + ".json")
            try:
                with open(header, "r") as f:
                    dicomdict = json.load(f)
            except json.JSONDecodeError:
                logger.error("{}: corrupted header {}"
                             .format(self.formatIdentity(),
                                     header))
                raise
            self._FILE_CACHE = path
            self._HEADER_CACHE = dicomdict
            self._header_file = header
            if self.setManufacturer(self._getField("Manufacturer")):
                self.resetMetaFields()
                self.setupMetaFields(_DICOM.metafields)
                self.testMetaFields()

    def acqTime(self) -> datetime:
        return self.getAttribute("acq_time")

    def dump(self):
        if self._HEADER_CACHE is not None:
            return str(self._HEADER_CACHE)
        elif len(self.files) > 0:
            self.loadFile(0)
            return str(self._HEADER_CACHE)
        else:
            logger.error("No defined files")
            return "No defined files"

    def _getField(self, field: list):
        res = None
        try:
            if field[0] in self.__specialFields:
                res = self._adaptMetaField(field[0])
            else:
                res = retrieveFormDict(field, self._HEADER_CACHE,
                                       fail_on_last_not_found=False)
        except Exception:
            logger.warning("{}: Could not parse '{}'"
                           .format(self.currentFile(False), field))
            res = None
        return res

    def recNo(self):
        return self.getField("SeriesNumber", 0)

    def recId(self):
        seriesdescr = self.getField("SeriesDescription")
        if seriesdescr is None:
            seriesdescr = self.getField("ProtocolName")
        if seriesdescr is None:
            logger.warning("{}: Unable to get recording Id for file {}"
                           .format(self.formatIdentity(),
                                   self.currentFile()))
            seriesdescr = "unknown"
        return seriesdescr.strip()

    def isCompleteRecording(self):
        return True

    def clearCache(self) -> None:
        self._HEADER_CACHE = None
        self._FILE_CACHE = ""

    def copyRawFile(self, destination: str) -> None:
        if os.path.isfile(os.path.join(destination,
                                       self.currentFile(True))):
            logger.warning("{}: File {} exists at destination"
                           .format(self.recIdentity(),
                                   self.currentFile(True)))
        shutil.copy2(self.currentFile(), destination)
        shutil.copy2(self._header_file, destination)

    def _getSubId(self) -> str:
        return str(self.getField("PatientID"))

    def _getSesId(self) -> str:
        return ""

    ########################
    # Additional fonctions #
    ########################
    def _adaptMetaField(self, name):
        if name == "acq_time":
            if "AcquisitionDateTime" in self._HEADER_CACHE:
                dt_stamp = self._HEADER_CACHE["AcquisitionDateTime"]
                return self.__transform(dt_stamp, "DT")

            acq = datetime.min

            if "AcquisitionDate" in self._HEADER_CACHE:
                date_stamp = self.__transform(
                        self._HEADER_CACHE["AcquisitionDate"],
                        "DA"
                        )
            else:
                logger.warning("{}: Acquisition Date not defined"
                               .format(self.recIdentity()))
                return acq

            if "AcquisitionTime" in self._HEADER_CACHE:
                time_stamp = self.__transform(
                        self._HEADER_CACHE["AcquisitionTime"],
                        "TM")
            else:
                logger.warning("{}: Acquisition Time not defined"
                               .format(self.recIdentity()))
                return acq
            acq = datetime.combine(date_stamp, time_stamp)
            return acq

        return None

    def __transform(self, value, VR: str):
        # Date and time
        # converted to corresponding datetime subclass
        if VR == "TM":
            if "." in value:
                dt = datetime.strptime(value, "%H:%M:%S.%f").time()
            else:
                dt = datetime.strptime(value, "%H:%M:%S").time()
            return dt
        if VR == "DA":
            dt = datetime.strptime(value, "%Y-%m-%d").date()
            return dt
        if VR == "DT":
            value = value.strip()
            date_string = "%Y-%m-%d"
            time_string = "%H:%M:%S"
            sep_string = "T"
            ms_string = ""
            uts_string = ""
            if "." in value:
                ms_string += ".%f"
            if "+" in value or "-" in value:
                uts_string += "%z"
            if len(value) == 8 or \
                    (len(value) == 13 and uts_string != ""):
                logger.warning("{}: Format is DT, but string looks like DA"
                               .format(value))
                t = datetime.strptime(value, date_string + uts_string)
            elif len(value) == 6 or \
                    (len(value) == 13 and ms_string != ""):
                logger.warning("{}: Format is DT, but string looks like TM"
                               .format(value))
                t = datetime.strptime(value, time_string + ms_string)
            else:
                t = datetime.strptime(value, date_string + sep_string
                                      + time_string + ms_string + uts_string)
            if t.tzinfo is not None:
                t += t.tzinfo.utcoffset(t)
                t = t.replace(tzinfo=None)
            return t
