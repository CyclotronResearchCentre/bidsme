###############################################################################
# NIFTI.py provides an implementation of PET class for generic NIFTI file
# format
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

from ..common import retrieveFormDict
from .PET import PET
from tools import tools
from .. import _nifti_common

import os
import logging
import shutil
import gzip

from datetime import datetime

logger = logging.getLogger(__name__)


class NIFTI(PET):
    _type = "NIFTI"

    __slots__ = ["_NIFTI_CACHE", "_FILE_CACHE",
                 "_nii_type", "_endiannes"
                 ]

    __specialFields = {"AcquisitionTime",
                       "SeriesNumber",
                       "RecordingId",
                       "PatientId",
                       "SessionId"}

    def __init__(self, rec_path=""):
        super().__init__()

        self._NIFTI_CACHE = None
        self._FILE_CACHE = ""
        self._nii_type = ""
        self._endiannes = "<"

        if rec_path:
            self.setRecPath(rec_path)

    @classmethod
    def _isValidFile(cls, file: str) -> bool:
        """
        Checks whether a file is a NIFTI(1,2)-file.
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
        if not os.path.isfile(file):
            return False
        if file.endswith(".nii") or file.endswith(".hdr"):
            if os.path.basename(file).startswith('.'):
                logger.warning('{}: file {} is hidden'
                               .format(cls.formatIdentity(),
                                       file))
            if file.endswith(".hdr"):
                if not os.path.isfile(file[:-4] + ".img"):
                    return False
            try:
                return _nifti_common.isValidNIFTI(file)
            except Exception:
                return False
        return False

    def _loadFile(self, path: str) -> None:
        if path != self._DICOMFILE_CACHE:
            self._endianness, self._nii_type = _nifti_common.getEndType(path)
            self._FILE_CACHE = path

            if self._nii_type == "n+2":
                self._NIFTI_CACHE =\
                        _nifti_common.parceNIFTIheader_2(path,
                                                         self._endianness)
            else:
                self._NIFTI_CACHE =\
                        _nifti_common.parceNIFTIheader_1(path,
                                                         self._endianness)

    def dump(self):
        if self._NIFTI_CACHE is not None:
            return str(self._NIFTI_CACHE)
        elif len(self.files) > 0:
            self.loadFile(0)
            return str(self._NIFTI_CACHE)
        else:
            logger.error("No defined files")
            return "No defined files"

    def _getField(self, field: list):
        res = None
        try:
            if field[0] in self.__specialFields:
                res = self._adaptMetaField(field[0])
            else:
                res = retrieveFormDict(field, self._NIFTI_CACHE,
                                       fail_on_last_missing=False)
        except Exception as e:
            logger.warning("{}: Could not parse '{}' for {}"
                           .format(self.currentFile(False), field, e))
            res = None
        return res

    def copyRawFile(self, destination: str) -> None:
        if os.path.isfile(os.path.join(destination,
                                       self.currentFile(True))):
            logger.warning("{}: File {} exists at destination"
                           .format(self.recIdentity(),
                                   self.currentFile(True)))
        shutil.copy2(self.currentFile(), destination)
        if self._nii_type == "ni1":
            data_file = tools.change_ext(self.currentFile(), "img")
            shutil.copy2(data_file, destination)

    def _copy_bidsified(self, directory: str, bidsname: str, ext: str) -> None:
        if self._nii_type == "ni1":
            shutil.copy2(self.currentFile(),
                         os.path.join(directory, bidsname + ext))
            data_file = tools.change_ext(self.currentFile(), "img")
            shutil.copy2(data_file,
                         os.path.join(directory, bidsname + ".img"))
        else:
            out_fname = os.path.join(directory, bidsname + ext)
            if self.zip:
                with open(self.currentFile(), 'rb') as f_in:
                    with gzip.open(out_fname, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                shutil.copy2(self.currentFile(),
                             os.path.join(directory, bidsname + ext))

    def _getAcqTime(self) -> datetime:
        return None

    def recNo(self):
        return self.index

    def recId(self):
        return os.path.splitext(self.currentFile(True))[0]

    def _getSubId(self) -> str:
        return None

    def _getSesId(self) -> str:
        return ""

    def isCompleteRecording(self):
        return True

    def clearCache(self) -> None:
        del self._NIFTI_CACHE
        self._NIFTI_CACHE = None
        self._FILE_CACHE = ""

    ########################
    # Additional fonctions #
    ########################
    def _adaptMetaField(self, name):
        return None
