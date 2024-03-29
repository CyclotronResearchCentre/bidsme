###############################################################################
# ECAT.py provides an implementation of PET class for generic ECAT file format
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
from ..common import action_value
from . import _ECAT

import logging
import numpy

from datetime import datetime
from nibabel import ecat

logger = logging.getLogger(__name__)


class ECAT(PET):
    _type = "ECAT"

    __slots__ = ["_ECAT_CACHE", "_SUB_CACHE", "_FILE_CACHE"]
    __specialFields = {"ScanStart", "InjectionStart",
                       "FramesStart", "FramesDuration"}
    _file_extentions = [".v"]

    def __init__(self, rec_path=""):
        super().__init__()

        self._ECAT_CACHE = None
        self._SUB_CACHE = None
        self._FILE_CACHE = ""
        self.switches["exportHeader"] = True

        if rec_path:
            self.setRecPath(rec_path)

    @classmethod
    def _isValidFile(cls, file: str) -> bool:
        """
        Checks whether a file is a ECAT-file.
        It checks if file ends in .v
        and starts with MATRIX72

        Parameters:
        -----------
        file: str
            path to file to test

        Returns:
        --------
        bool:
            True if file is identified as ECAT
        """
        with open(file, "rb") as f:
            magic = f.read(14).decode()
            magic = magic.strip(" \0")
            if magic.startswith("MATRIX"):
                return True
            else:
                logger.debug("{}: Missing magic string"
                             .format(cls.formatIdentity()))
                return False

    def _loadFile(self, path: str) -> None:
        if path != self._FILE_CACHE:
            e = ecat.load(path)
            self._ECAT_CACHE = e.header
            self._SUB_CACHE = e.get_subheaders().subheaders
            self._FILE_CACHE = path
            self.setManufacturer("Unknown", {})
            self.resetMetaFields()
            self.setupMetaFields(_ECAT.metafields)
            self.testMetaFields()

    def _getAcqTime(self) -> datetime:
        return self.getField("datetime:scan_start_time")

    def dump(self):
        if self._ECAT_CACHE is None:
            self.loadFile(0)
        res = dict()
        for key, val in self._ECAT_CACHE.items():
            res[key] = self.__transform(val)
        for index, im in enumerate(self._SUB_CACHE):
            res[index] = dict()
            for key in im.dtype.names:
                res[index][key] = self.__transform(im[key])
        for f in self.__specialFields:
            res[f] = self._getField([f])

        return res

    def _getField(self, field: list):
        res = None
        try:
            if field[0] in self.__specialFields:
                res = self._adaptMetaField(field[0])
            else:
                if field[0].isdigit():
                    it = int(field[0])
                    res = self._SUB_CACHE[it][field[1]]
                    res = self.__transform(res)
                else:
                    res = self.__transform(self._ECAT_CACHE[field[0]])
                    if len(field) > 1:
                        res = res[int(field[1])]
        except Exception as e:
            logger.warning("{}: Could not parse '{}' for {}"
                           .format(self.currentFile(False), field, e))
            res = None
        return res

    def _transformField(self, value, prefix: str):
        if prefix == "":
            return value
        if prefix == "datetime":
            return datetime.fromtimestamp(value)
        if prefix == "date":
            return datetime.fromtimestamp(value).date()
        if prefix == "time":
            return datetime.fromtimestamp(value).time()
        try:
            return action_value(value, prefix)
        except Exception as e:
            logger.error("{}: Invalid field prefix {}: {}"
                         .format(self.formatIdentity(),
                                 prefix, e))

    def _recNo(self):
        return self._getField(["acquisition_type"])

    def _recId(self):
        return self._getField(["study_type"])

    def _getSubId(self) -> str:
        return self._getField(["patient_id"])

    def _getSesId(self) -> str:
        return ""

    def isCompleteRecording(self):
        return True

    def clearCache(self) -> None:
        del self._ECAT_CACHE
        del self._SUB_CACHE
        self._ECAT_CACHE = None
        self._SUB_CACHE = None

    @staticmethod
    def __transform(val: numpy.ndarray) -> object:
        tmp = val.tolist()
        if isinstance(tmp, bytes):
            try:
                tmp = tmp.decode()
            except UnicodeError:
                logger.debug("Can't decode bytes string")
                tmp = "BytesString"
        return tmp

    def _adaptMetaField(self, name):
        value = None
        if name == "FramesStart":
            value = [self.__transform(frame["frame_start_time"]) / 1000
                     for frame in self._SUB_CACHE]
            return value
        if name == "FramesDuration":
            value = [self.__transform(frame["frame_duration"]) / 1000
                     for frame in self._SUB_CACHE]
            return value
        if name == "ScanStart":
            return 0
        if name == "InjectionStart":
            return self.getField("dose_start_time")\
                    - self.getField("scan_start_time")
