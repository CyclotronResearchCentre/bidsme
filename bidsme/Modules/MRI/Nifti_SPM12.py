###############################################################################
# Nifti_SPM12.py provides the implementation of MRI class for Nifti file format
# as created by SPM12 (hMRI tollbox)
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
import logging
import json
import shutil
import pprint
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class Nifti_SPM12(MRI):
    _type = "Nifti_SPM12"

    __slots__ = ["_DICOMDICT_CACHE", "_DICOMFILE_CACHE",
                 "isSiemens",
                 "__csas", "__phoenix",
                 "__adFree", "__alFree", "__seqName"]

    __spetialFields = {"NumberOfMeasurements",
                       "PhaseEncodingDirection",
                       "B1mapNominalFAValues",
                       "B1mapMixingTime",
                       "RFSpoilingPhaseIncrement",
                       "MTState",
                       "ReceiveCoilActiveElements"
                       }

    def __init__(self, rec_path=""):
        super().__init__()

        self._DICOMDICT_CACHE = None
        self._DICOMFILE_CACHE = ""
        self.isSiemens = False
        self.__alFree = list()
        self.__adFree = list()
        self.__seqName = ""

        if rec_path:
            self.setRecPath(rec_path)

        #####################
        # Common recomended #
        #####################
        recommend = self.metaFields_rec["__common__"]
        recommend["Manufacturer"] = MetaField("Manufacturer")
        recommend["ManufacturersModelName"] = MetaField("ManufacturerModelName")
        recommend["DeviceSerialNumber"] = MetaField("DeviceSerialNumber")
        recommend["StationName"] = MetaField("StationName")
        recommend["SoftwareVersions"] = MetaField("SoftwareVersions")
        recommend["MagneticFieldStrength"] = MetaField("MagneticFieldStrength", 1.)
        recommend["ReceiveCoilName"] = MetaField("ReceiveCoilName")
        recommend["ReceiveCoilActiveElements"] = MetaField("ReceiveCoilActiveElements")
        # recommend["GradientSetType"]
        recommend["MRTransmitCoilSequence"] = MetaField("MRTransmitCoilSequence")
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
        recommend["PartialFourierDirection"] = MetaField("PartialFourierDirection")
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
        recommend["InstitutionalDepartmentName"] = MetaField("InstitutionalDepartmentName")

        #####################
        # sMRI metafields   #
        #####################
        optional = self.metaFields_opt["anat"]
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


    ################################
    # reimplementation of virtuals #
    ################################
    @classmethod
    def _isValidFile(cls, file: str) -> bool:
        """
        Checks whether a file is a NII file with a valid json dump,
        produced by hMRI package of SPM12
        """
        if os.path.isfile(file) and file.endswith(".nii"):
            if os.path.basename(file).startswith('.'):
                logger.warning('{}: file {} is hidden'
                               .format(cls.formatIdentity(),
                                       file))
            try:
                acqpar = cls.__loadJsonDump(file)
            except json.JSONDecodeError:
                logger.error("{}: corrupted file {}"
                             .format(cls.formatIdentity(),
                                     file))
                raise
            except Exception:
                return False
            if "Modality" in acqpar:
                return True
            else:
                logger.warning("{}: missing 'Modality' "
                               "in file {}"
                               .format(cls.formatIdentity(),
                                       file))
                return False
        return False

    def _loadFile(self, path: str) -> None:
        if path != self._DICOMFILE_CACHE:
            # The DICM tag may be missing for anonymized DICOM files
            dicomdict = self.__loadJsonDump(path)
            self._DICOMFILE_CACHE = path
            self._DICOMDICT_CACHE = dicomdict
            self.isSiemens = (self._DICOMDICT_CACHE["Manufacturer"]
                              == "SIEMENS ")
            self.__seqName = self._DICOMDICT_CACHE["SequenceName"].lower()
            if self.isSiemens:
                self.__csas = self._DICOMDICT_CACHE["CSASeriesHeaderInfo"]
                self.__phoenix = self.__csas["MrPhoenixProtocol"]
                if "sWipMemBlock" in self.__phoenix:
                    self.__alFree = self.__phoenix["sWipMemBlock"]["alFree"]
                    self.__adFree = self.__phoenix["sWipMemBlock"]["adFree"]

    def acqTime(self) -> datetime:
        date_stamp = int(self.getField("AcquisitionDate"))
        time_stamp = float(self.getField("AcquisitionTime"))
        days = date_stamp % 1
        return datetime.fromordinal(date_stamp) \
            + timedelta(days=days - 366, seconds=time_stamp)

    def dump(self):
        if self._DICOMDICT_CACHE:
            return pprint.pformat(self._DICOMDICT_CACHE,
                                  indent=2, width=40, compact=True)
        elif len(self.files) > 0:
            self.loadFile(0)
            return pprint.pformat(self._DICOMDICT_CACHE,
                                  indent=2, width=40, compact=True)
        else:
            logger.error("No defined files")
            return "No defined files"

    def _getField(self, field: list):
        res = None
        try:
            if field[0] in self.__spetialFields:
                res = self._adaptMetaField(field[0])
            else:
                value = self._DICOMDICT_CACHE
                for f in field:
                    if isinstance(value, list):
                        value = value[int(f)]
                    elif isinstance(value, dict):
                        value = value.get(f, None)
                    else:
                        break
                res = value
        except Exception:
            logger.warning("{}: Could not parse '{}'"
                           .format(self.currentFile(False), field))
            res = None
        return res

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
        return value

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
        self._DICOMDICT_CACHE = None
        self._DICOMFILE_CACHE = ""

    def copyRawFile(self, destination: str) -> None:
        if os.path.isfile(os.path.join(destination,
                                       self.currentFile(True))):
            logger.warning("{}: File {} exists at destination"
                           .format(self.recIdentity(),
                                   self.currentFile(True)))
        shutil.copy2(self.currentFile(), destination)
        shutil.copy2(tools.change_ext(self.currentFile(), "json"),
                     destination)

    def _getSubId(self) -> str:
        return str(self.getField("PatientID"))

    def _getSesId(self) -> str:
        return ""

    ########################
    # Additional fonctions #
    ########################
    def _adaptMetaField(self, name):
        if not self.isSiemens:
            raise ValueError("{}: {} is defined only for Siemens"
                             .format(self.recIdentity(), name))

        if name == "NumberOfMeasurements":
            value = self._DICOMDICT_CACHE.get("lRepetitions", 0) + 1
        elif name == "PhaseEncodingDirection":
            value = self._DICOMDICT_CACHE["CSAImageHeaderInfo"]\
                    .get("PhaseEncodingDirectionPositive", 0)
            if value == 0:
                value = -1
        elif name == "B1mapNominalFAValues":
            if self.__seqName in ("b1v2d3d2", "b1epi4a3d2", "b1epi2b3d2",
                                  "b1epi2d3d2"):
                value = list(range(self.__adFree[2], 0, -self.__adFree[3]))
            elif self.__seqName == "seste1d3d2":
                value = list(range(230, -10, 0))
            else:
                logger.warning("{}: Unable to get {}: sequence {} "
                               "not defined"
                               .format(self.recIdentity(),
                                       name, self.__seqName))
                value = []
        elif name == "B1mapMixingTime":
            if self.__seqName in ("b1v2d3d2", "b1epi2d3d2"):
                value = self.__alFree[0] * 1e-6
            elif self.__seqName in ("b1epi4a3d2", "b1epi2b3d2"):
                value = self.__alFree[1] * 1e-6
            elif self.__seqName == "seste1d3d2":
                value = self.__alFree[13] * 1e-6
            else:
                logger.warning("{}: Unable to get {}: sequence {} "
                               "not defined"
                               .format(self.recIdentity(),
                                       name, self.__seqName))
                value = None
        elif name == "RFSpoilingPhaseIncrement":
            if self.__seqName in ("b1v2d3d2", "b1epi4a3d2", "b1epi2d3d2"):
                value = self.__adFree[5]
            elif self.__seqName in ("fl3d_2l3d8", "fl3d_2d3d6"):
                value = self.__adFree[2]
            elif self.__seqName == "seste1d3d2":
                value = self.__adFree[11] * 1e-6
            else:
                logger.warning("{}: Unable to get {}: sequence {} "
                               "not defined"
                               .format(self.recIdentity(),
                                       name, self.__seqName))
                value = 0

        elif name == "MTState":
            value = self.__phoenix["sPrepPulses"].get("ucMTC", 0)
            if value == 0:
                value = "Off"
            else:
                value = "On"
        elif name == "ReceiveCoilActiveElements":
            value = self._DICOMDICT_CACHE["CSASeriesHeaderInfo"]\
                    .get("CoilString", "")

        return value

    @staticmethod
    def __loadJsonDump(file: str) -> dict:
        json_dump = file[:-4] + ".json"
        with open(json_dump, "r") as f:
            return json.load(f)["acqpar"][0]
