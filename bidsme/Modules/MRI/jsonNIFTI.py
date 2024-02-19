###############################################################################
# jsonNIFTI.py provides an implementation of MRI class for Nifti file format
# with a generic json file containing metadata
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

import os
import logging
import shutil
import json
from datetime import datetime

from bidsme.tools import tools

from .MRI import MRI
from ..common import retrieveFormDict

logger = logging.getLogger(__name__)


class jsonNIFTI(MRI):
    _type = "jsonNIFTI"

    __slots__ = ["_HEADER_CACHE", "_FILE_CACHE",
                 "_header_file",
                 ]
    _file_extentions = [".nii", ".nii.gz"]
    __specialFields = {}

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
            header = tools.change_ext(file, "json")
            if os.path.isfile(header):
                return True
        return False

    def _loadFile(self, path: str) -> None:
        if path != self._FILE_CACHE:
            # The DICM tag may be missing for anonymized DICOM files
            header = tools.change_ext(path, "json")
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

            self.manufacturer = self._HEADER_CACHE.get("Manufacturer",
                                                       "Unknown")
            self.resetMetaFields()
            meta = {"Unknown": {}}
            meta[self.manufacturer] = {key: ("<{}>".format(key), None)
                                       for key in self._HEADER_CACHE}
            self.setupMetaFields(meta)
            self.testMetaFields()

    def _getAcqTime(self) -> datetime:
        return None

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

    def _recNo(self):
        return self.getField("SeriesNumber", self.index)

    def _recId(self):
        seriesdescr = self.getField("SeriesDescription")
        if seriesdescr is None:
            seriesdescr = self.getField("ProtocolName")
        if seriesdescr is None:
            logger.warning("{}: Unable to get recording Id for file {}"
                           .format(self.formatIdentity(),
                                   self.currentFile()))
            seriesdescr = os.path.splitext(self.currentFile(True))[0]
        return seriesdescr.strip()

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
        return ""

    def _getSesId(self) -> str:
        return ""

    ########################
    # Additional fonctions #
    ########################
    def _adaptMetaField(self, name):
        return None
