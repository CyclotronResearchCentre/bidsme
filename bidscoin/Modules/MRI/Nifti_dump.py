from Modules.MRI.MRI import MRI
from bidsMeta import MetaField
from tools import tools

import os
import logging
import json
import shutil
import pprint
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class Nifti_dump(MRI):
    __slots__ = ["_DICOMDICT_CACHE", "_DICOMFILE_CACHE","isSiemens",
                 "__adFree", "__alFree", "__seqName"]
    __spetialFields = {"NumberOfMeasurements", 
                       "PhaseEncodingDirection",
                       "B1mapNominalFAValues",
                       "B1mapMixingTime",
                       "RFSpoilingPhaseIncrement",
                       "MTState"}

    def __init__(self, rec_path=""):
        super().__init__()

        self._DICOMDICT_CACHE = None
        self._DICOMFILE_CACHE = ""
        self.isSiemens = False
        self.__alFree = list()
        self.__adFree = list()
        self.__seqName = ""
        
        self.type = "Nifti_dump"

        if rec_path:
            self.set_rec_path(rec_path)

        self.metaFields["RepetitionTime"]\
            = MetaField("RepetitionTime", 0.001)
        self.metaFields["Manufacturer"]\
            = MetaField("Manufacturer")
        self.metaFields["ManufacturerModelName"]\
            = MetaField("ManufacturerModelName")
        self.metaFields["DeviceSerialNumber"]\
            = MetaField("DeviceSerialNumber")
        self.metaFields["StationName"]\
            = MetaField("StationName")
        self.metaFields["SoftwareVersions"]\
            = MetaField("SoftwareVersions")
        self.metaFields["MagneticFieldStrength"]\
            = MetaField("MagneticFieldStrength",1.)
        self.metaFields["ReceiveCoilActiveElements"]\
            = MetaField("CSASeriesHeaderInfo/CoilString")
        self.metaFields["ScanningSequence"]\
            = MetaField("ScanningSequence")
        self.metaFields["SequenceVariant"]\
            = MetaField("SequenceVariant")
        self.metaFields["ScanOptions"]\
            = MetaField("ScanOptions", "", "")
        self.metaFields["SequenceName"]\
            = MetaField("SequenceName")
        self.metaFields["PhaseEncodingDirectionSign"]\
            = MetaField("PhaseEncodingDirectionSign", 1, 1)
        self.metaFields["InPlanePhaseEncodingDirection"]\
            = MetaField("InPlanePhaseEncodingDirection","")
        self.metaFields["EchoTime"]\
            = MetaField("EchoTime",0.001)
        self.metaFields["DwellTime"]\
            = MetaField("Private_0019_1018",0.001)
        self.metaFields["FlipAngle"]\
            = MetaField("FlipAngle",1.)
        self.metaFields["ProtocolName"]\
            = MetaField("ProtocolName")
        # self.metaFields["spoilingGradientMoment"]\
        #     = MetaField("spoilingGradientMoment", 1.)
        # self.metaFields["spoilingGradientDuration"]\
        #     = MetaField("spoilingGradientDuration", 0.001)
        self.metaFields["BandwidthPerPixelRO"]\
            = MetaField("PixelBandwidth",1.)
        self.metaFields["NumberOfMeasurements"]\
            = MetaField("NumberOfMeasurements",1, 1)
        self.metaFields["InstitutionName"]\
            = MetaField("InstitutionName")
        self.metaFields["InstitutionAddress"]\
            = MetaField("InstitutionAddress")
        self.metaFields["InstitutionalDepartmentName"]\
            = MetaField("InstitutionalDepartmentName")

    def _adaptMetaField(self, name):
        if not self.isSiemens:
            raise ValueError("{} is defined only for Siemens"
                             .format(name))

        if name == "NumberOfMeasurements":
            value = self._DICOMDICT_CACHE.get("lRepetitions",0) + 1
        elif name == "PhaseEncodingDirection":
            value = self._DICOM_CACHE["CSAImageHeaderInfo"]\
                    .get("PhaseEncodingDirectionPositive", 0)
            if value == 0:
                value = -1
        elif name == "B1mapNominalFAValues":
            if self.__seqName in ("b1v2d3d2", "b1epi4a3d2", "b1epi2b3d2",
                                  "b1epi2d3d2"):
                value = list(range(self.__adFree[2], 0, -self.__adFree[3]))
            elif sequence == "seste1d3d2":
                value = list(range(230,-10,0))
            else:
                logger.warning("{}-{}/{}: Unable to get {}: sequence {} "
                               "not defined"
                               .format(self.get_rec_no(), self.get_rec_id(),
                                       self.index, name, self.__seqName))
                value = []
        elif name == "B1mapMixingTime":
            if self.__seqName in ("b1v2d3d2", "b1epi2d3d2"):
                value = self.__alFree[0] * 1e-6
            elif self.__seqName in ( "b1epi4a3d2", "b1epi2b3d2"):
                value = self.__alFree[1] * 1e-6
            elif self.__seqName == "seste1d3d2":
                value = self.__alFree[13] * 1e-6
            else:
                logger.warning("{}-{}/{}: Unable to get {}: sequence {} "
                               "not defined"
                               .format(self.get_rec_no(), self.get_rec_id(),
                                       self.index, name, self.__seqName))
                value = None
        elif name == "RFSpoilingPhaseIncrement":
            if self.__seqName in ("b1v2d3d2", "b1epi4a3d2","b1epi2d3d2"):
                value = self.__adFree[5]
            elif self.__seqName in ( "fl3d_2l3d8", "fl3d_2d3d6"):
                value = self.__adFree[2]
            elif self.__seqName == "seste1d3d2":
                value = self.__adFree[11] * 1e-6
            else:
                logger.warning("{}-{}/{}: Unable to get {}: sequence {} "
                               "not defined"
                               .format(self.get_rec_no(), self.get_rec_id(),
                                       self.index, name, self.__seqName))
                value = 0

        elif name == "MTState":
            value = self._DICOMDICT_CACHE["CSASeriesHeaderInfo"]\
                    ["MrPhoenixProtocol"]\
                    ["sPrepPulses"].get("ucMTC", 0)
            if value == 0:
                value = "Off"
            else:
                value = "On"

        return value

    def copy_file(self, destination):
        shutil.copy(self.currentFile(), destination)
        shutil.copy(tools.change_ext(self.currentFile(),"json"),
                    destination)

    def acq_time(self) -> datetime:
        date_stamp = int(self.get_field("AcquisitionDate"))
        time_stamp = float(self.get_field("AcquisitionTime"))
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

    @classmethod
    def isValidFile(cls, file: str) -> bool:
        """
        Checks whether a file is a NII file with a valid json dump,
        produced by SPM12

        :param file:    The full pathname of the file
        :return:        Returns true if a file is a DICOM-file
        """

        if os.path.isfile(file) and file.endswith(".nii"):
            if os.path.basename(file).startswith('.'):
                logger.warning(f'NII_DUMP file is hidden: {file}')
            try:
                acqpar = cls.__loadJsonDump(file)
            except Exception as e:
                logger.warning("File {}: {}".format(file, str(e)))
                return False
            if "Modality" in acqpar:
                return True
            else :
                logger.warning("File {}: missing 'Modality' "
                               "in acquisition parameters"
                               .format(file))
                return False
        else:
            return False

    @staticmethod
    def __loadJsonDump(file: str) -> dict:
        json_dump = file[:-4] + ".json"
        with open(json_dump, "r") as f:
            return json.load(f)["acqpar"][0]

    def loadFile(self, index: int) -> None:
        path = os.path.join(self.rec_path,self.files[index])
        if not self.isValidFile(path):
            raise ValueError("{} is not valid {} file"
                             .format(path, self.name))
        if path != self._DICOMFILE_CACHE:
            # The DICM tag may be missing for anonymized DICOM files
            dicomdict = self.__loadJsonDump(path)
            self._DICOMFILE_CACHE = path
            self._DICOMDICT_CACHE = dicomdict
            self.isSiemens = (self._DICOMDICT_CACHE["Manufacturer"]
                              == "SIEMENS ")
            self.__seqName = self._DICOMDICT_CACHE["SequenceName"].lower()
            if self.isSiemens:
                if "sWipMemBlock" in self._DICOMDICT_CACHE\
                        ["CSASeriesHeaderInfo"]\
                        ["MrPhoenixProtocol"]:
                    self.__alFree = self._DICOMDICT_CACHE\
                            ["CSASeriesHeaderInfo"]\
                            ["MrPhoenixProtocol"]\
                            ["sWipMemBlock"]["alFree"]
                    self.__adFree = self._DICOMDICT_CACHE\
                            ["CSASeriesHeaderInfo"]\
                            ["MrPhoenixProtocol"]\
                            ["sWipMemBlock"]["adFree"]
            for key in self.attributes:
                self.attributes[key] = self.get_field(key)
        self.index = index

    def get_field(self, field: str, default=None, separator='/'):
        if field in self.__spetialFields:
            return self._adaptMetaField(field)

        value = self._DICOMDICT_CACHE
        try:
            field = field.split(separator)
            for f in field:
                if isinstance(value, list):
                    value = value[int(f)]
                elif isinstance(value, dict):
                    value = value.get(f, None)
                else:
                    break
            if value is None:
                if default is not None:
                    value = default
                else:
                    logger.warning("Could not parse '{}' from {}"
                                   .format(field, self._DICOMFILE_CACHE))
        except Exception as e: 
            logger.warning("Could not parse '{}' from {}"
                           .format(field, self._DICOMFILE_CACHE))
            value = None

        if value is None:
            return ""
        elif isinstance(value, int):
            return int(value)
        else:
            return str(value).strip()

    def clearCache(self) -> None:
        self._DICOMDICT_CACHE = None
        self._DICOMFILE_CACHE = ""

    def isComplete(self):
        return True

    @classmethod
    def get_type(cls):
        return "Nifti_dump"
