# flake8: noqa

from .MRI import MRI
from bidsMeta import MetaField
from tools import tools

import os
import re
import logging
import pydicom
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DICOM(MRI):
    _type = "DICOM"

    __slots__ = ["_DICOM_CACHE", "_DICOMFILE_CACHE", "isSiemens"]
    __spetialFields = {}

    def __init__(self, recording=""):
        super().__init__()

        self._DICOM_CACHE = None
        self._DICOMFILE_CACHE = ""
        self.isSiemens = False

        if recording:
            self.set_rec_path(recording)

    @classmethod
    def isValidFile(cls, file: str) -> bool:
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
        if file.endswith(".dcm") and file.endswith(".DCM"):
            if os.path.basename(file).startswith('.'):
                logger.warning('{}: file {} is hidden'
                               .format(cls.formatIdentity(),
                                       file))
            try:
                with open(file, 'rb') as dcmfile:
                    dcmfile.seek(0x80, 1)
                if dcmfile.read(4) == b'DICM':
                    return True
                raise
            except Exception:
                return False
        return False

    def loadFile(self, index: int) -> None:
        path = self.files[index]
        if not self.isValidFile(self, path):
            raise ValueError("{} is not valid {} file"
                             .format(path, self.name))
        if path != self._DICOMFILE_CACHE:
            dicomdict = pydicom.dcmread(path, stop_before_pixels=True)
            self._DICOMFILE_CACHE = path
            self._DICOMDICT_CACHE = dicomdict
        self.index = index

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
        if self._DICOMDICT_CACHE is not None:
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
                for f in field:
                    if isinstance(value, pydicom.dataset.Dataset):
                        value = value[f]
                    if isinstance(value, pydicom.dataelem.DataElement):
                        if value.VR == "SQ":
                            value = value[int(f)]
                        else:
                            value = self.__transform(value)
                            break
                res = value
        except Exception:
            logger.warning("{}: Could not parse '{}'"
                           .format(self.recIdentity(), field))
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
        return None

    def __transform(element: pydicom.dataelem.DataElement):
        if element is None:
            return None
        VR = element.VR
        VM = element.VM
        val = element.value

        if VM > 1:
            return [self.__decodeValue(val[i], VR) for i in range(VM)]
        else:
            return self.__decodeValue(val[i], VR)

    def __decodeValue(self, val, VR: str):
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
        if VR in ("AE", "CS", "PN", 
                  "LO", "LT",
                  "SH", "UC",
                  "UR", "UT", "UI"):
            return val.strip(" \0")

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
                return time.strptime(val, "%H%M%S.%f")
            else:
                return time.strptime(val, "%H%M%S")
        if VR == "DA":
            return date.strptime(val, "%Y%m%d")
        if VR == "DT":
            val = val.strip()
            date_string = "%Y%m%d"
            time_string = "%H%M%S"
            if "." in val:
                time_string += ".%f"
            if "+" in val or "-" in val:
                time_string += "%z"
            t = datetime.strptime(val, date_string + time_string)
            if t.tzinfo is not None:
                t += t.tzinfo.utcoffset(t)
                t = t.replace(tzinfo=None)
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
        logger.error("{} is not valid DICOM VR")
        raise ValueError("invalid VR")
