###############################################################################
# DICOM.py provides an implementation of MRI class for DICOM file format
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
from bidsMeta import MetaField
from tools import tools

import os
import re
import logging
import pydicom
import shutil
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class DICOM(MRI):
    _type = "DICOM"

    __slots__ = ["_DICOM_CACHE", "_DICOMFILE_CACHE",
                 "isSiemens"]
    __specialFields = {}

    def __init__(self, rec_path=""):
        super().__init__()

        self._DICOM_CACHE = None
        self._DICOMFILE_CACHE = ""
        self.isSiemens = False

        if rec_path:
            self.setRecPath(rec_path)

        #####################
        # Common recomended #
        #####################
        recommend = self.metaFields_rec["__common__"]
        recommend["Manufacturer"] = MetaField("Manufacturer")
        recommend["ManufacturersModelName"] =\
            MetaField("ManufacturerModelName")
        recommend["DeviceSerialNumber"] = MetaField("DeviceSerialNumber")
        recommend["StationName"] = MetaField("StationName")
        recommend["SoftwareVersions"] = MetaField("SoftwareVersions")
        recommend["MagneticFieldStrength"] =\
            MetaField("MagneticFieldStrength", 1.)
        recommend["ReceiveCoilName"] = MetaField("ReceiveCoilName")
        recommend["ReceiveCoilActiveElements"] =\
            MetaField("ReceiveCoilActiveElements")
        # recommend["GradientSetType"]
        recommend["MRTransmitCoilSequence"] =\
            MetaField("MRTransmitCoilSequence")
        # recommend["MatrixCoilMode"]
        # recommend["CoilCombinationMethod"]
        # recommend["PulseSequenceType"]
        recommend["ScanningSequence"] = MetaField("ScanningSequence")
        recommend["SequenceVariant"] = MetaField("SequenceVariant")
        recommend["ScanOptions"] = MetaField("ScanOptions")
        recommend["SequenceName"] = MetaField("SequenceName")
        # recommend["NumberShots"]
        # recommend["PulseSequenceDetails"]
        # recommend["NonlinearGradientCorrection"]
        # recommend["ParallelReductionFactorInPlane"]
        # recommend["ParallelAcquisitionTechnique"]
        recommend["PartialFourier"] = MetaField("PartialFourier")
        recommend["PartialFourierDirection"] =\
            MetaField("PartialFourierDirection")
        # recommend["PhaseEncodingDirection"]
        # recommend["EffectiveEchoSpacing"]
        # recommend["TotalReadoutTime"]
        recommend["EchoTime"] = MetaField("EchoTime", 1e-3)
        recommend["InversionTime"] = MetaField("InversionTime", 1e-3)
        # recommend["SliceTiming"]
        # recommend["SliceEncodingDirection"]
        # recommend["DwellTime"] = MetaField("Private_0019_1018", 1e-6)
        recommend["FlipAngle"] = MetaField("FlopAngle", 1.)
        # recommend["MultibandAccelerationFactor"]
        # recommend["NegativeContrast"]
        # recommend["MultibandAccelerationFactor"]
        # recommend["AnatomicalLandmarkCoordinates"]
        recommend["InstitutionName"] = MetaField("InstitutionName")
        recommend["InstitutionAddress"] = MetaField("InstitutionAddress")
        recommend["InstitutionalDepartmentName"] =\
            MetaField("InstitutionalDepartmentName")

        #####################
        # sMRI metafields   #
        #####################
        # optional = self.metaFields_opt["anat"]
        # optional["ContrastBolusIngredient"]

        #####################
        # fMRI metafields   #
        #####################
        required = self.metaFields_req["func"]
        required["RepetitionTime"] = MetaField("RepetitionTime", 1e-3)
        required["TaskName"] = MetaField("<<bids:task>>")

        recommend = self.metaFields_rec["func"]
        # recommend["NumberOfVolumesDiscardedByScanner"]
        # recommend["NumberOfVolumesDiscardedByUser"]
        # recommend["DelayTime"]
        # recommend["AcquisitionDuration"]
        # recommend["DelayAfterTrigger"]
        # recommend["Instructions"]
        # recommend["TaskDescription"]
        # recommend["CogAtlasID"]
        # recommend["CogPOID"]

        #####################
        # fMap metafields   #
        #####################
        required = self.metaFields_req["fmap"]
        # required["IntendedFor"]

        recommend = self.metaFields_rec["fmap"]
        # recommend["EchoTime1"]
        # recommend["EchoTime2"]
        # recommend["Units"]

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
        if not os.path.isfile(file):
            return False
        if file.endswith(".dcm") or file.endswith(".DCM"):
            if os.path.basename(file).startswith('.'):
                logger.warning('{}: file {} is hidden'
                               .format(cls.formatIdentity(),
                                       file))
                return False
            try:
                with open(file, 'rb') as dcmfile:
                    dcmfile.seek(0x80, 1)
                    if dcmfile.read(4) == b'DICM':
                        return True
            except Exception:
                return False
        return False

    def _loadFile(self, path: str) -> None:
        if path != self._DICOMFILE_CACHE:
            # The DICM tag may be missing for anonymized DICOM files
            dicomdict = pydicom.dcmread(path, stop_before_pixels=True)
            self._DICOMFILE_CACHE = path
            self._DICOM_CACHE = dicomdict

    def acqTime(self) -> datetime:
        if "AcquisitionDateTime" in self._DICOM_CACHE:
            dt_stamp = self._DICOM_CACHE["AcquisitionDateTime"]
            return self.__transform(dt_stamp)

        acq = datetime.min

        if "AcquisitionDate" in self._DICOM_CACHE:
            date_stamp = self.__transform(self._DICOM_CACHE["AcquisitionDate"])
        else:
            logger.warning("{}: Acquisition Date not defined"
                           .format(self.recIdentity()))
            return acq

        if "AcquisitionDate" in self._DICOM_CACHE:
            time_stamp = self.__transform(self._DICOM_CACHE["AcquisitionTime"])
        else:
            logger.warning("{}: Acquisition Time not defined"
                           .format(self.recIdentity()))
            return acq
        acq = datetime.combine(date_stamp, time_stamp)
        return acq

    def dump(self):
        if self._DICOM_CACHE is not None:
            return str(self._DICOM_CACHE)
        elif len(self.files) > 0:
            self.loadFile(0)
            return str(self._DICOM_CACHE)
        else:
            logger.error("No defined files")
            return "No defined files"

    def _getField(self, field: list):
        res = None
        try:
            if field[0] in self.__specialFields:
                res = self._adaptMetaField(field[0])
            else:
                value = self._DICOM_CACHE
                for ind, f in enumerate(field):
                    f = f.strip()
                    tag = self.__getTag(f)
                    if tag is not None:
                        f = tag
                    if isinstance(value, pydicom.dataset.Dataset):
                        value = value[f]
                    elif isinstance(value, pydicom.dataelem.DataElement):
                        if value.VR == "SQ":
                            value = value[int(f)]
                    if isinstance(value, pydicom.dataelem.DataElement) \
                            and value.VR != "SQ":
                        break
                res = self.__transform(value)
                for i in range(ind + 1, len(field)):
                    res = res[int(field[i])]
        except Exception as e:
            logger.warning("{}: Could not parse '{}' for {}"
                           .format(self.currentFile(False), field, e))
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

    def _transformField(self, value, prefix: str):
        if prefix.startswith("time"):
            exp = prefix[len("time"):]
            if exp:
                exp = int(exp)
            else:
                exp = 3
            return value / 10 ** exp
        elif prefix == "":
            return value
        else:
            logger.warning("{}/{}: Unknown field prefix {}"
                           .format(self.formatIdentity(),
                                   prefix))

    def clearCache(self) -> None:
        del self._DICOM_CACHE
        self._DICOM_CACHE = None
        self._DICOMFILE_CACHE = ""

    def copyRawFile(self, destination: str) -> None:
        if os.path.isfile(os.path.join(destination,
                                       self.currentFile(True))):
            logger.warning("{}: File {} exists at destination"
                           .format(self.recIdentity(),
                                   self.currentFile(True)))
        shutil.copy2(self.currentFile(), destination)
        data_file = self.currentFile(True)
        json_file = "dcm_dump_" + tools.change_ext(data_file, "json")
        json_file = os.path.join(destination, json_file)
        with open(json_file, "w") as f:
            d = self.__extractStruct(self._DICOM_CACHE)
            json.dump(d, f, indent=2)

    def _getSubId(self) -> str:
        return str(self.getField("PatientID"))

    def _getSesId(self) -> str:
        return ""

    ########################
    # Additional fonctions #
    ########################
    def _adaptMetaField(self, name):
        return None

    @staticmethod
    def __transform(element: pydicom.dataelem.DataElement,
                    clean: bool = False):
        if element is None:
            return None
        VR = element.VR
        VM = element.VM
        val = element.value

        if VM > 1:
            return [DICOM.__decodeValue(val[i], VR, clean) for i in range(VM)]
        else:
            return DICOM.__decodeValue(val, VR, clean)

    @staticmethod
    def __decodeValue(val, VR: str, clean=False):
        """
        Decodes a value from pydicom.DataElement to corresponding
        python class following description in:
        http://dicom.nema.org/medical/dicom/current/output/
        chtml/part05/sect_6.2.html

        Nested values are not permitted

        Parameters
        ----------
        val:
            value as stored in DataElements.value
        VR: str
            Value representation defined by DICOM
        clean: bool
            if True, values of not-basic classes (None, int, float)
            transformed to string

        Returns
        -------
            decoded value
        """

        # Byte Numbers:
        # parced by pydicom, just return value
        if VR in ("FL", "FD",
                  "SL", "SS", "SV",
                  "UL", "US", "UV"):
            return val

        # Text Numbers
        # using int(), float()
        if VR == "DS":
            return float(val)
        if VR == "IS":
            return int(val)

        # Text and text-like
        # using strip to remove apddings
        if VR in ("AE", "CS",
                  "LO", "LT",
                  "SH", "ST", "UC",
                  "UR", "UT", "UI"):
            return val.strip(" \0")

        # Persons Name
        # Use decoded original value
        if VR == "PN":
            if isinstance(val, str):
                return val.strip(" \0")
            if len(val.encodings) > 0:
                enc = val.encodings[0]
            return val.original_string.decode(enc)

        # Age string
        # unit mark is ignored, value converted to int
        if VR == "AS":
            if val[-1] in "YMWD":
                return int(val[:-1])
            else:
                return int(val)

        # Date and time
        # converted to corresponding datetime subclass
        if VR == "TM":
            if "." in val:
                dt = datetime.strptime(val, "%H%M%S.%f").time()
            else:
                dt = datetime.strptime(val, "%H%M%S").time()
            if clean:
                return dt.isoformat()
            else:
                return dt
        if VR == "DA":
            dt = datetime.strptime(val, "%Y%m%d").date()
            if clean:
                return dt.isoformat()
            else:
                return dt
        if VR == "DT":
            val = val.strip()
            date_string = "%Y%m%d"
            time_string = "%H%M%S"
            ms_string = ""
            uts_string = ""
            if "." in val:
                ms_string += ".%f"
            if "+" in val or "-" in val:
                uts_string += "%z"
            if len(val) == 8 or \
                    (len(val) == 13 and uts_string != ""):
                logger.warning("{}: Format is DT, but string looks like DA"
                               .format(val))
                t = datetime.strptime(val, date_string + uts_string)
            elif len(val) == 6 or \
                    (len(val) == 13 and ms_string != ""):
                logger.warning("{}: Format is DT, but string looks like TM"
                               .format(val))
                t = datetime.strptime(val, time_string + ms_string)
            else:
                t = datetime.strptime(val, date_string + time_string
                                      + ms_string + uts_string)
            if t.tzinfo is not None:
                t += t.tzinfo.utcoffset(t)
                t = t.replace(tzinfo=None)
            if clean:
                return t.isoformat()
            else:
                return t

        # Invalid type
        # Attributes and sequences will produce warning and return
        # None
        if VR in ("AT", "SQ", "UN"):
            logger.warning("Invalid VR: {}".format(VR))
            return None

        # Other type
        # Not clear how parce them
        if VR in ("OB", "OD", "OF", "OL", "OV", "OW"):
            logger.warning("Other VR: {}".format(VR))
            return None

        # unregistered VR
        logger.error("{} is not valid DICOM VR".format(VR))
        raise ValueError("invalid VR")

    @staticmethod
    def __getTag(tag: str) -> tuple:
        """
        Parces a DICOM tag from string into a tuple of int

        String is expected to have format '(%4d, %4d)', and
        tag numbers are expected to be in DICOM standart form:
        hex numbers without '0x' prefix

        Parameters
        ----------
        tag: str
            string tag, e.g. '(0008, 0030)'

        Returns
        -------
        (int, int)
        None
        """
        res = re.match("\\(([0-9a-fA-F]{4})\\, ([0-9a-fA-F]{4})\\)", tag)
        if res:
            return (int(res.group(1), 16), int(res.group(2), 16))
        else:
            return None

    @staticmethod
    def __extractStruct(dataset: pydicom.dataset.Dataset) -> dict:
        """
        Recurcively extract data from DICOM dataset and put it
        into dictionary. Key are created from keyword, or if not
        defined from tag.

        Values are parced from DataElement values, multiple values
        are stored as list.
        Sequences are stored as lists of dictionaries

        Parameters
        ----------
        dataset: pydicom.dataset.Dataset
            dataset to extract

        Returns
        -------
        dict
        """
        res = dict()

        for el in dataset:
            key = el.keyword
            if key == '':
                key = str(el.tag)
            if el.VR == "SQ":
                res[key] = [DICOM.__extractStruct(val)
                            for val in el]
            else:
                res[key] = DICOM.__transform(el, clean=True)
        return res
