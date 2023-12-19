###############################################################################
# hmriNIFTI.py provides the implementation of MRI class for Nifti file format
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

import os
import logging
import json
import shutil
import pprint
from datetime import datetime, timedelta

from bidsme.tools import tools

from .MRI import MRI
from . import _hmriNIFTI

from ..common import action_value
from ..common import retrieveFormDict


logger = logging.getLogger(__name__)


class hmriNIFTI(MRI):
    _type = "hmriNIFTI"

    __slots__ = ["_DICOMDICT_CACHE", "_DICOMFILE_CACHE",
                 "__csas", "__csai", "__phoenix",
                 "__adFree", "__alFree", "__seqName"]

    __spetialFields = {"NumberOfMeasurements",
                       "PhaseEncodingDirection",
                       "B1mapNominalFAValues",
                       "B1mapMixingTime",
                       "RFSpoilingPhaseIncrement",
                       "MTState",
                       "ReceiveCoilActiveElements",
                       "PhaseEncodingSign",
                       "EffectiveEchoSpacing",
                       "TotalReadoutTime"
                       }

    _file_extentions = [".nii", ".nii.gz"]

    def __init__(self, rec_path=""):
        super().__init__()

        self._DICOMDICT_CACHE = None
        self._DICOMFILE_CACHE = ""
        self.__alFree = list()
        self.__adFree = list()
        self.__csas = dict()
        self.__csai = dict()
        self.__phoenix = dict()
        self.__seqName = ""

        if rec_path:
            self.setRecPath(rec_path)

    ################################
    # reimplementation of virtuals #
    ################################
    @classmethod
    def _isValidFile(cls, file: str) -> bool:
        """
        Checks whether a file is a NII file with a valid json dump,
        produced by hMRI package of SPM12

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

            try:
                acqpar = cls.__loadJsonDump(file)
                if not acqpar:
                    return False
                manufacturer = acqpar.get("Manufacturer").strip()
                if manufacturer.lower() == "siemens":
                    acqpar["CSASeriesHeaderInfo"]
                    acqpar["CSAImageHeaderInfo"]
            except json.JSONDecodeError as e:
                logger.error("{}:{} corrupted file {}"
                             .format(cls.formatIdentity(),
                                     e, file))
                raise
            except KeyError as e:
                logger.error("{}:{} corrupted file {}"
                             .format(cls.formatIdentity(),
                                     e,
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

            self.__seqName = self._DICOMDICT_CACHE["SequenceName"].lower()
            manufacturer = self._DICOMDICT_CACHE["Manufacturer"]
            manuf_changed = self.setManufacturer(manufacturer,
                                                 _hmriNIFTI.manufacturers)
            if self.manufacturer == "Siemens":
                self.__csas = self._DICOMDICT_CACHE["CSASeriesHeaderInfo"]
                self.__csai = self._DICOMDICT_CACHE["CSAImageHeaderInfo"]
                self.__phoenix = self.__csas.get("MrPhoenixProtocol", {})
                if not self.__phoenix:
                    self.__phoenix = self.__csas.get("MrProtocol", {})
                if "sWipMemBlock" in self.__phoenix:
                    self.__alFree = \
                        self.__phoenix["sWipMemBlock"].get("alFree", [])
                    self.__adFree = \
                        self.__phoenix["sWipMemBlock"].get("adFree", [])

            if manuf_changed:
                self.resetMetaFields()
                self.setupMetaFields(_hmriNIFTI.metafields)
                self.testMetaFields()

    def _getAcqTime(self) -> datetime:
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
                res = retrieveFormDict(field, self._DICOMDICT_CACHE,
                                       fail_on_last_not_found=False)
        except Exception as e:
            logger.warning("{}: Could not parse '{}' for {}"
                           .format(self.currentFile(False), field, e))
            res = None
        return res

    def _transformField(self, value, prefix: str):
        if prefix == "time":
            return value / 1000
        elif prefix == "":
            return value

        try:
            return action_value(value, prefix)
        except Exception as e:
            logger.error("{}: Invalid field prefix {}: {}"
                         .format(self.formatIdentity(),
                                 prefix, e))
            raise

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

    def copyRawFile(self, destination: str) -> str:
        if os.path.isfile(os.path.join(destination,
                                       self.currentFile(True))):
            logger.warning("{}: File {} exists at destination"
                           .format(self.recIdentity(),
                                   self.currentFile(True)))
        shutil.copy2(self.currentFile(), destination)
        shutil.copy2(tools.change_ext(self.currentFile(), "json"),
                     destination)
        return os.path.join(destination, self.currentFile(True))

    def _getSubId(self) -> str:
        return str(self.getField("PatientID"))

    def _getSesId(self) -> str:
        return ""

    ########################
    # Additional fonctions #
    ########################
    def _adaptMetaField(self, name):
        value = None
        if name == "PhaseEncodingDirection":
            value = self._DICOMDICT_CACHE.get("InPlanePhaseEncodingDirection")\
                    .strip()
            if value == "ROW":
                return "i"
            elif value == "COL":
                return "j"
            return None
        if self.manufacturer == "Siemens":
            if name == "NumberOfMeasurements":
                value = self.__phoenix.get("lRepetitions", 0) + 1
            elif name == "PhaseEncodingSign":
                value = self.__csai.get("PhaseEncodingDirectionPositive", 0)
                if value:
                    return "+"
                else:
                    return "-"
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
                nMeas = self.__phoenix.get("lRepetitions", 0)
                value = [x / 2 for x in value[:nMeas + 1]]
            elif name == "B1mapMixingTime":
                if self.__seqName in ("b1v2d3d2", "b1epi2d3d2"):
                    value = self.__alFree[0] / 1e6
                elif self.__seqName in ("b1epi4a3d2", "b1epi2b3d2"):
                    value = self.__alFree[1] / 1e6
                elif self.__seqName == "seste1d3d2":
                    value = self.__alFree[13] / 1e6
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
                    value = self.__adFree[11] / 1e6
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
                value = self.__csai.get("CoilString", "")
            elif name == "EffectiveEchoSpacing":
                BPPPE = self.__csai.get("BandwidthPerPixelPhaseEncode", 0)
                MSP = self._DICOMDICT_CACHE.get("AcquisitionMatrix", [0])
                msp = MSP[-1]
                if msp != 0 and BPPPE != 0:
                    return 1. / (BPPPE * msp)
                else:
                    return None
            elif name == "TotalReadoutTime":
                BPPPE = self.__csai.get("BandwidthPerPixelPhaseEncode", 0)
                MSP = self._DICOMDICT_CACHE.get("AcquisitionMatrix", [0])
                msp = MSP[-1]
                if msp != 0 and BPPPE != 0:
                    return (msp - 1) / (BPPPE * msp)
                else:
                    return None

        return value

    @staticmethod
    def __loadJsonDump(file: str) -> dict:
        json_dump = tools.change_ext(file, "json")
        with open(json_dump, "r") as f:
            js = json.load(f)
            if "acqpar" in js:
                return js["acqpar"][0]
            else:
                return None
