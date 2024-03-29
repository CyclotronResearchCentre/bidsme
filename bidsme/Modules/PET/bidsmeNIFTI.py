###############################################################################
# bidsmeNIFTI.py provides an implementation of PET class for Nifti file format
# with dumped header in form of json file
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

from ..common import retrieveFormDict, action_value
from .PET import PET
from . import _DICOM
from . import _ECAT

import os
import logging
import shutil
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class bidsmeNIFTI(PET):
    _type = "bidsmeNIFTI"

    __slots__ = ["_HEADER_CACHE", "_FILE_CACHE",
                 "_header_file",
                 "_headerData"
                 ]

    _file_extentions = [".nii", ".nii.gz"]

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

        path, base = os.path.split(file)
        base, ext = os.path.splitext(base)
        header = os.path.join(path, "header_dump_" + base + ".json")
        if os.path.isfile(header):
            return True
        else:
            logger.debug("{}: Missing header dump file"
                         .format(cls.formatIdentity()))
            return False

    def _loadFile(self, path: str) -> None:
        if path != self._FILE_CACHE:
            # The DICM tag may be missing for anonymized DICOM files
            path, base = os.path.split(path)
            base, ext = os.path.splitext(base)
            header = os.path.join(path, "header_dump_" + base + ".json")
            try:
                with open(header, "r") as f:
                    self._headerData = json.load(f)
                    self.custom = self._headerData["custom"]
            except json.JSONDecodeError:
                logger.error("{}: corrupted header {}"
                             .format(self.formatIdentity(),
                                     header))
                raise
            except KeyError as e:
                logger.error("{}: missing {} key in {}"
                             .format(self.formatIdentity(),
                                     e,
                                     header))
                raise
            self._FILE_CACHE = path
            self._HEADER_CACHE = self._headerData.pop("header")
            self._header_file = header
            form = self._headerData["format"].split("/")
            if form[0] != self._module:
                logger.error("{}: format is not {}"
                             .format(self.recIdentity,
                                     self._module))
                raise Exception("Wrong format")
            if form[1] == "DICOM":
                if self.setManufacturer(self._headerData["manufacturer"],
                                        _DICOM.manufacturers):
                    self.resetMetaFields()
                    self.setupMetaFields(_DICOM.metafields)
                    self.testMetaFields()
            elif form[1] == "ECAT":
                if self.setManufacturer(self._headerData["manufacturer"],
                                        _ECAT.manufacturers):
                    self.resetMetaFields()
                    self.setupMetaFields(_ECAT.metafields)
                    self.testMetaFields()
            else:
                logger.error("{}: unknown format {}"
                             .format(self.recIdentity,
                                     form[1]))
                raise Exception("Wrong format")

    def _getAcqTime(self) -> datetime:
        if self._headerData["acqDateTime"]:
            return datetime.strptime(self._headerData["acqDateTime"],
                                     "%Y-%m-%dT%H:%M:%S.%f")
        return None

    def dump(self):
        if self._HEADER_CACHE is None:
            self.loadFile(0)
        return self._HEADER_CACHE

    def _getField(self, field: list):
        res = None
        try:
            res = retrieveFormDict(field, self._HEADER_CACHE,
                                   fail_on_last_not_found=False)
        except Exception:
            logger.warning("{}: Could not parse '{}'"
                           .format(self.currentFile(False), field))
            res = None
        return res

    def _recNo(self):
        return self._headerData["recNo"]

    def _recId(self):
        return self._headerData["recId"]

    def isCompleteRecording(self):
        return True

    def clearCache(self) -> None:
        self._HEADER_CACHE = None
        self._FILE_CACHE = ""

    def copyRawFile(self, destination: str) -> str:
        if os.path.isfile(os.path.join(destination,
                                       self.currentFile(True))):
            logger.warning("{}: File {} exists at destination"
                           .format(self.recIdentity(),
                                   self.currentFile(True)))
        shutil.copy2(self.currentFile(), destination)
        shutil.copy2(self._header_file, destination)
        return os.path.join(destination, self.currentFile(True))

    def _getSubId(self) -> str:
        return self._headerData["subId"]

    def _getSesId(self) -> str:
        return self._headerData["sesId"]

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

    ########################
    # Additional fonctions #
    ########################
    def _adaptMetaField(self, name):
        return None
