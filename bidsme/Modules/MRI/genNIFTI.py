###############################################################################
# genNIFTI.py provides an implementation of MRI class for generic NIFTI file
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


from .MRI import MRI
from tools import tools

import os
import re
import logging
import struct
import shutil
from datetime import datetime

logger = logging.getLogger(__name__)


class genNIFTI(MRI):
    _type = "genNIFTI"

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
                with open(file, 'rb') as niifile:
                    d = niifile.read(4)
                    hdr = d.decode("<i", d)
                    if hdr in (348, 540):
                        # little endian
                        return True
                    if hdr == (348, 540):
                        # big endian
                        return True
            except Exception:
                return False
        return False

    def _loadFile(self, path: str) -> None:
        if path != self._DICOMFILE_CACHE:
            # The DICM tag may be missing for anonymized DICOM files
            nii = open(path, "rb")
            # getting endiannes and type
            header_size = struct.unpack("<i", nii.read(4))
            if header_size == 348:
                self._endiannes = "<"
                if path.endswith(".hdr"):
                    self._nii_type = "ni1"
                else:
                    self._nii_type = "n+1"
            elif header_size == "510":
                self._endiannes = ">"
                self._nii_type = "n+2"
                if path.endswith(".hdr"):
                    logger.error("{}:{} .hdr/.img cannot be NIFTI-2"
                                 .format(self.formatIdentity(), path))
            elif header_size == 1543569408:
                self._endiannes = ">"
                header_size = 348
                if path.endswith(".hdr"):
                    self._nii_type = "ni1"
                else:
                    self._nii_type = "n+1"
            elif header_size == -33488896:
                self._endiannes = ">"
                self._nii_type = "n+2"
                header_size = 510
                if path.endswith(".hdr"):
                    logger.error("{}:{} .hdr/.img cannot be NIFTI-2"
                                 .format(self(self.formatIdentity(),
                                              path)))
                    raise Exception("Corrupted file")

            # confirming endiannes and type
            if self._nii_type == "n+2":
                nii.seek(16)
                dim_0 = struct.decode(self._endiannes + "q", nii.read(2))
                nii.seek(4)
                magic = nii.read(8).decode()
            else:
                nii.seek(40)
                dim_0 = struct.decode(self._endiannes + "h", nii.read(2))
                nii.seek(344)
                magic = nii.read(4).decode()

            if dim_0 < 1 or dim_0 > 7:
                logger.critical("{}:{} corrupted file -- "
                                "conflicting endiannes"
                                .format(self.formatIdentity(), path))
                raise Exception("Corrupted file")
            if magic != self._nii_type:
                logger.critical("{}:{} corrupted file -- "
                                "conflicting format version"
                                .format(self.formatIdentity(), path))
                raise Exception("Corrupted file")

            self._FILE_CACHE = path

            nii.seek(0)
            nii_header = nii.read(header_size)
            if self._nii_type == "n+2":
                self._NIFTI_CACHE = self.__parse_header2(nii_header)
            else:
                self._NIFTI_CACHE = self.__parse_header1(nii_header)

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
                value = self._NIFTI_CACHE
                for ind, f in enumerate(field):
                    if isinstance(value, list):
                        value = value[int(f)]
                        continue
                    if isinstance(value, dict):
                        value = value[f]
                    raise Exception("Not iterable")
                res = value
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
        shutil.copy2(self.currentFile(),
                     os.path.join(directory, bidsname + ext))
        if self._nii_type == "ni1":
            data_file = tools.change_ext(self.currentFile(), "img")
            shutil.copy2(data_file,
                         os.path.join(directory, bidsname + ".img"))

    def acqTime(self) -> datetime:
        return self.getAttribute("AcquisitionTime")

    def recNo(self):
        self.getAttribute("RecordingNumber", 0)

    def recId(self):
        return self.getAttribute("RecordingId",
                                 os.path.splitext(self.currentFile(False)[0])
                                 )

    def _getSubId(self) -> str:
        return str(self.getAttribute("PatientId"))

    def _getSesId(self) -> str:
        return str(self.getAttribute("SessionId"))

    def isCompleteRecording(self):
        return True

    def clearCache(self) -> None:
        del self._NIFTI_CACHE
        self._NIFTI_CACHE = None
        self._FILE_CACHE = ""

    ########################
    # Additional fonctions #
    ########################
    def __parse_header1(self, header: bytes) -> dict:
        """
        Parces NIFTI-1 header to dictionary

        Parameters
        ----------
        header: bytes
            header extracted from nii file (348 bites)

        Returns
        -------
        dict:
            parced dictionary
        """
        endian = self._endiannes
        res = dict()
        res["diminfo"] = struct.unpack("c", header[39:40])
        res["dim"] = struct.unpack(endian + "8h", header[40:56])
        res["intent_p1"] = struct.unpack(endian + "f", header[56:60])
        res["intent_p2"] = struct.unpack(endian + "f", header[60:64])
        res["intent_p3"] = struct.unpack(endian + "f", header[64:68])
        res["intent_code"] = struct.unpack(endian + "h", header[68:70])
        res["datatype"] = struct.unpack(endian + "h", header[70:72])
        res["bitpix"] = struct.unpack(endian + "h", header[70:72])
        res["slice_start"] = struct.unpack(endian + "h", header[72:74])
        res["pixdim"] = struct.unpack(endian + "8f", header[74:108])
        res["vox_offset"] = struct.unpack(endian + "f", header[108:112])
        res["scl_slope"] = struct.unpack(endian + "f", header[112:116])
        res["scl_inter"] = struct.unpack(endian + "f", header[116:120])
        res["slice_end"] = struct.unpack(endian + "h", header[120:122])
        res["slice_code"] = struct.unpack(endian + "b", header[122:123])
        res["xyz_units"] = struct.unpack(endian + "b", header[123:124])
        res["cal_max"] = struct.unpack(endian + "f", header[124:128])
        res["cal_min"] = struct.unpack(endian + "f", header[128:132])
        res["slice_duration"] = struct.unpack(endian + "f", header[132:136])
        res["toffset"] = struct.unpack(endian + "f", header[136:140])
        res["glmax"] = struct.unpack(endian + "i", header[140:144])
        res["glmin"] = struct.unpack(endian + "i", header[144:148])
        res["descrip"] = header[148:228].decode()
        res["aux_file"] = header[228:252].decode()
        res["qform_code"] = struct.unpack(endian + "h", header[252:254])
        res["sform_code"] = struct.unpack(endian + "h", header[254:256])
        res["quatern_b"] = struct.unpack(endian + "f", header[256:260])
        res["quatern_c"] = struct.unpack(endian + "f", header[260:264])
        res["quatern_d"] = struct.unpack(endian + "f", header[264:268])
        res["qoffset_x"] = struct.unpack(endian + "f", header[268:272])
        res["qoffset_y"] = struct.unpack(endian + "f", header[272:276])
        res["qoffset_z"] = struct.unpack(endian + "f", header[276:280])
        res["srow_x"] = struct.unpack(endian + "4f", header[280:296])
        res["srow_y"] = struct.unpack(endian + "4f", header[296:312])
        res["srow_z"] = struct.unpack(endian + "4f", header[312:328])
        res["intent_name"] = header[328:344].decode()

        return res

    def __parse_header2(self, header: bytes) -> dict:
        """
        Parces NIFTI-2 header to dictionary

        Parameters
        ----------
        header: bytes
            header extracted from nii file (348 bites)

        Returns
        -------
        dict:
            parced dictionary
        """
        endian = self._endiannes
        res = dict()
        res["datatype"] = struct.unpack(endian + "h", header[12:14])
        res["bitpix"] = struct.unpack(endian + "h", header[14:16])
        res["dim"] = struct.unpack(endian + "8q", header[16:80])
        res["intent_p1"] = struct.unpack(endian + "d", header[80:88])
        res["intent_p2"] = struct.unpack(endian + "d", header[88:96])
        res["intent_p3"] = struct.unpack(endian + "d", header[96:104])
        res["pixdim"] = struct.unpack(endian + "8d", header[104:168])
        res["vox_offset"] = struct.unpack(endian + "q", header[168:176])
        res["scl_slope"] = struct.unpack(endian + "d", header[176:184])
        res["scl_inter"] = struct.unpack(endian + "d", header[184:192])
        res["cal_max"] = struct.unpack(endian + "d", header[192:200])
        res["cal_min"] = struct.unpack(endian + "d", header[200:208])
        res["slice_duration"] = struct.unpack(endian + "d", header[208:216])
        res["toffset"] = struct.unpack(endian + "d", header[216:224])
        res["slice_start"] = struct.unpack(endian + "q", header[224:232])
        res["slice_end"] = struct.unpack(endian + "q", header[232:240])
        res["descrip"] = header[240:320].decode()
        res["aux_file"] = header[320:344].decode()
        res["qform_code"] = struct.unpack(endian + "i", header[344:348])
        res["sform_code"] = struct.unpack(endian + "i", header[348:352])
        res["quatern_b"] = struct.unpack(endian + "d", header[352:360])
        res["quatern_c"] = struct.unpack(endian + "d", header[360:368])
        res["quatern_d"] = struct.unpack(endian + "d", header[368:376])
        res["qoffset_x"] = struct.unpack(endian + "d", header[376:384])
        res["qoffset_y"] = struct.unpack(endian + "d", header[384:392])
        res["qoffset_z"] = struct.unpack(endian + "d", header[392:400])
        res["srow_x"] = struct.unpack(endian + "4d", header[400:432])
        res["srow_y"] = struct.unpack(endian + "4d", header[432:464])
        res["srow_z"] = struct.unpack(endian + "4d", header[464:496])
        res["slice_code"] = struct.unpack(endian + "i", header[496:500])
        res["xyz_units"] = struct.unpack(endian + "i", header[500:504])
        res["intent_code"] = struct.unpack(endian + "i", header[504:508])
        res["intent_name"] = header[508:524].decode()

        return res

    def _adaptMetaField(self, name):
        if name == "AcquisitionTime":
            return None
        if name == "RecordingNumber":
            return self.index
        if name == "RecordingId":
            return os.path.splitext(self.currentFile(False))[0]
        if name == "PatientId":
            recId = os.path.splitext(self.currentFile(False))[0]
            res = re.search("sub-([a-zA-Z0-9]+)", recId)
            if res:
                return res.group(1)
        if name == "SessionId":
            recId = os.path.splitext(self.currentFile(False))[0]
            res = re.search("ses-([a-zA-Z0-9]+)", recId)
            if res:
                return res.group(1)
        return None
