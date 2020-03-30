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
            self.isSiemens = self.is_dicomfile_siemens(self._DICOMFILE_CACHE)
        self.index = index

    def acqTime(self) -> datetime:
        if "AcquisitionDateTime" in self._DICOM_CACHE:
            dt_stamp = self._DICOM_CACHE["AcquisitionDateTime"]
            return self.__transform(dt_stamp)
        
        date_stamp = int(self.getField("AcquisitionDate"))
        time_stamp = float(self.getField("AcquisitionTime"))


    def get_field(self, field: str):
        try:
            value = self._DICOMDICT_CACHE.get(field)
            if not value:
                for elem in self._DICOMDICT_CACHE.iterall():
                    if elem.name == field:
                        value = elem.value
                        continue
        except Exception:
            try:
                value = self.parse_x_protocol(field)
            except Exception:
                logger.warning("Could not parse {} from {}"
                               .format(field, self._DICOMFILE_CACHE))
                value = None

        if not value:
            return ""
        elif isinstance(value, int):
            return int(value)
        else:
            return str(value)

    def parse_x_protocol(self, pattern: str) -> str:
        """
        Siemens writes a protocol structure as text into each DICOM file.
        This structure is necessary to recreate a scanning protocol
        from a DICOM, since the DICOM information alone
        wouldn't be sufficient.

        :param pattern:     A regexp expression:
                            '^' + pattern + '\t = \t(.*)\\n'
        :return:            The string extracted values from the dicom-file
                            according to the given pattern
        """
        if not self.isSiemens:
            logger.warning('Parsing {} may fail because {} does not seem '
                           'to be a Siemens DICOM file'
                           .format(pattern, self.file))
        regexp = '^' + pattern + '\t = \t(.*)\n'
        regex = re.compile(regexp.encode('utf-8'))
        with open(self.file, 'rb') as openfile:
            for line in openfile:
                match = regex.match(line)
                if match:
                    return match.group(1).decode('utf-8')
        logger.warning("Pattern: '{}' not found in {}"
                       .format(regexp.encode('unicode_escape').decode(),
                               self.file))
        return None

    def is_dicomfile_siemens(file: str) -> bool:
        """
        Checks whether a file is a *SIEMENS* DICOM-file.
        All Siemens Dicoms contain a dump of the  MrProt structure.
        The dump is marked with a header starting with 'ASCCONV BEGIN'.
        Though this check is not foolproof, it is very unlikely to fail.

        :param file:    The full pathname of the file
        :return:        Returns true if a file is a Siemens DICOM-file
        """
        return b'ASCCONV BEGIN' in open(file, 'rb').read()

    def isComplete(self):
        nrep = self.get_field('lRepetitions')
        nfiles = self.get_nFiles()

        if nrep and nrep > nfiles:
            logger.warning('{}: Incomplete acquisition: '
                           '\nExpected {}, found {} dicomfiles'
                           .format(self._DICOMFILE_CACHE, nrep, nfiles))
            return False
        return True

    
    def __transform(element: pydicom.dataelem.DataElement):
        if element is None:
            return None
        VR = element.VR
        VM = element.VM
        val = element.value

        if VR == "AE":
            """
            Application Entity
                A string of characters that identifies an Application Entity
                with leading and trailing spaces (20H) being non-significant.
                A value consisting solely of spaces shall not be used.
            """
            return str(value.value)
        elif VR == "AS":
            """
            Age String
                A string of characters with one of the following formats -- 
                nnnD, nnnW, nnnM, nnnY; where nnn shall contain 
                    the number of days for D, 
                    weeks for W, 
                    months for M, 
                    or years for Y.

            Example: "018M" would represent an age of 18 months.
            """
            if val.endswith("Y"):
                return int(val[:-1])
            elif val.endswith("M"):
                return int(val[:-1])
            elif val.endswith("W"):
                return int(val[:-1])
            elif val.endswith("W"):
                return int(val[:-1])
            else:
                return int(val)
        elif VR == "AT":
            """
            Attribute Tag
                Ordered pair of 16-bit unsigned integers that is the value
                of a Data Element Tag.

                Example: A Data Element Tag of (0018,00FF) would be encoded
                as a series of 4 bytes in a Little-Endian Transfer Syntax as
                18H,00H,FFH,00H.
            """
            logger.warning("Tag {}({}) contains DataElement"
                           .format(element.name, element.tag))
            return None
        elif VR == "CS":
            """
            Code String
                A string of characters identifying a controlled concept.
                Leading or trailing spaces (20H) are not significant.
            """
            return val
        elif VR == "DA":
            """
            Date
                A string of characters of the format YYYYMMDD;
                where YYYY shall contain year,
                MM shall contain the month,
                and DD shall contain the day,
                interpreted as a date of the Gregorian calendar system.
            """
            return datetime.strptime(val, "%Y%m%d")
        elif VR == "DS":
            """
            Decimal String
                A string of characters representing either 
                a fixed point number or a floating point number.
                A fixed point number shall contain only the characters 
                0-9 with an optional leading "+" or "-" and an optional "."
                to mark the decimal point.
                A floating point number shall be conveyed as defined 
                in ANSI X3.9, with an "E" or "e" to indicate the start
                of the exponent. 
                Decimal Strings may be padded with leading or trailing spaces. 
                Embedded spaces are not allowed.
            """
            return float(val)
        elif VR == "DT":
            """
            Date Time
                A concatenated date-time character string in the format:
                YYYYMMDDHHMMSS.FFFFFF&ZZXX
                
                The components of this string, from left to right, are
                YYYY = Year, MM = Month, DD = Day,
                HH = Hour (range "00" - "23"),
                MM = Minute (range "00" - "59"),
                SS = Second (range "00" - "60").
                FFFFFF = Fractional Second contains a fractional part of
                a second as small as 1 millionth of a second
                (range "000000" - "999999").

                &ZZXX is an optional suffix for offset from 
                Coordinated Universal Time (UTC), 
                where & = "+" or "-", 
                and ZZ = Hours and XX = Minutes of offset.
            """
            val = val.strip()
            time_stamp = None
            dt = timedelta()
            if val[-5] == "+":
                dt = timedelta(hours=int(val[-4:-2],
                               minutes=int(val[-2:])))
                val = val[0:-5]
            if val[-5] == "-":
                dt = -timedelta(hours=int(val[-4:-2],
                                minutes=int(val[-2:])))
                val = val[0:-5]
            if "." in val:
                time_stamp = datetime(val, "%Y%m%d%H%M%S.%f")
            else:
                time_stamp = datetime(val, "%Y%m%d%H%M%S")
            return time_stamp + dt
        elif VR == "FL":
            """
            Floating Point Single
            """
            return val
        elif VR == "FD":
            """
            Floating Point Double
            """
            return val
        elif VR == "IS":
            """
            Integer String
            """
            return int(val)
        elif VR == "LO"
            """
            Long String
            """
            return val
        elif VR == "LT":
            """
            Long Text
            """
            return val
        elif VR == "OB":
            """
            Other Byte
            """
            logger.warning("Tag {}({}) contains Transfert syntax"
                           .format(element.name, element.tag))
            return None
        elif VR == "OD":
            """
            Other double
            """
            logger.warning("Tag {}({}) contains Transfert syntax"
                           .format(element.name, element.tag))
            return None
        elif VR == "OF":
            """
            Other double
            """
            logger.warning("Tag {}({}) contains Transfert syntax"
                           .format(element.name, element.tag))
            return None
        elif VR == "OL":
            """
            Other double
            """
            logger.warning("Tag {}({}) contains Transfert syntax"
                           .format(element.name, element.tag))
            return None
        elif VR == "OV":
            """
            Other double
            """
            logger.warning("Tag {}({}) contains Transfert syntax"
                           .format(element.name, element.tag))
            return None
        elif VR == "OW":
            """
            Other double
            """
            logger.warning("Tag {}({}) contains Transfert syntax"
                           .format(element.name, element.tag))
            return None
