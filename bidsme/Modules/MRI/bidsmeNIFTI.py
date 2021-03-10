###############################################################################
# bidsmeNIFTI.py provides an implementation of MRI class for Nifti file format
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

from ..common import retrieveFormDict
from .MRI import MRI
from . import _DICOM
from tools import tools

import os
import logging
import shutil
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class bidsmeNIFTI(MRI):
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

        if os.path.isfile(file):
            if os.path.basename(file).startswith('.'):
                logger.warning('{}: file {} is hidden'
                               .format(cls.formatIdentity(),
                                       file))
                return False
            path, base = os.path.split(file)

            header = os.path.join(path,
                                  "header_dump_"
                                  + tools.change_ext(base, "json"))
            if os.path.isfile(header):
                return True
        return False

    def _loadFile(self, path: str) -> None:
        if path != self._FILE_CACHE:
            # The DICM tag may be missing for anonymized DICOM files
            path_dir, base = os.path.split(path)
            header = os.path.join(path_dir,
                                  "header_dump_"
                                  + tools.change_ext(base, "json"))
            try:
                with open(header, "r") as f:
                    dicomdict = json.load(f)
                    self._headerData = {
                            "format": dicomdict["format"],
                            "acqDateTime": dicomdict["acqDateTime"],
                            "manufacturer": dicomdict["manufacturer"],
                            }
                    dicomdict["header"]
                    self.custom = dicomdict["custom"]
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
            self._HEADER_CACHE = dicomdict["header"]
            self._header_file = header
            form = dicomdict["format"].split("/")
            if form[0] != self._module:
                logger.error("{}: format is not {}"
                             .format(self.recIdentity,
                                     self._module))
                raise Exception("Wrong format")
            if form[1] == "DICOM":
                mod = _DICOM
            else:
                logger.error("{}: unknown format {}"
                             .format(self.recIdentity,
                                     form[1]))
                raise Exception("Wrong format")

            if self.setManufacturer(dicomdict["manufacturer"],
                                    mod.manufacturers):
                self.resetMetaFields()
                self.setupMetaFields(mod.metafields)
                self.testMetaFields()

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

    def recNo(self):
        return self._headerData["recNo"]

    def recId(self):
        return self._headerData["recId"]

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
        return self._headerData["subId"]

    def _getSesId(self) -> str:
        return self._headerData["sesId"]

    ########################
    # Additional fonctions #
    ########################
    def _adaptMetaField(self, name):
        return None
