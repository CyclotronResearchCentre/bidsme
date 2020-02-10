from .EEG import EEG
from bidsMeta import MetaField
from tools import tools

import os
import logging
import json
import shutil
import pprint
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class BrainVision(EEG):
    _type = "BrainVision"

    __slots__ = ["_CACHE", "_FILE_CACHE",
                 "_datafile", "_markfile",
                 "_acqTime"]
    __spetialFields = {}

    def __init__(self, rec_path=""):
        from configparser import ConfigParser
        super().__init__()

        self._CACHE = ConfigParser()
        self._FILE_CACHE = ""
        self._datafile = None
        self.__markfile = None
        self._acqTime =  datetime.datetime(1900, 1, 1, 0, 0)
        # Series number and secription is not defined
        self.setAttribute(self, "SeriesNumber", 0)
        self.setAttribute(self, "SeriesDescription", "unknown")

        if rec_path:
            self.setRecPath(rec_path)

    ################################
    # reimplementation of virtuals #
    ################################
    @classmethod
    def _isValidFile(cls, file: str) -> bool:
        """
        Checks whether a file is a Brain vision file
        with .vhdr extention and with an existing 
        data and marker files
        """
        if os.path.isfile(file) and file.endswith(".vhdr"):
            if os.path.basename(file).startswith("."):
                logger.warning('{}: file {} is hidden'
                               .format(cls.formatIdentity(),
                                       file))
            with open(file, "read", enc="utf-8") as f:
                decl = file.readline()
                if decl != "Brain Vision DataExchange Header File Version 1.0":
                    return False
            return True
        return False

    def loadFile(self, index: int) -> None:
        path = os.path.join(self._recPath,self.files[index])
        if not self.isValidFile(path):
            raise ValueError("{}: {} is not valid file",
                             .format(self.formatIdentity(), path))
        if path != self._FILE_CACHE:
            self._FILE_CACHE = path
            dirpath, base = os.path.split(path)
            base = base.splitext()[0]

            with open(path, "r", encoding="utf-8") as f:
                f.readline()
                self._CACHE.read_file(f, isource=path)

            self._datafile = self._genPath(
                    dirpath, 
                    base,
                    self._CACHE["Common Infos"]["DataFile"])
            if not self._datafile:
                raise ValueError("{}: {} DataFile not defined"
                                 .format(self.formatIdentity(),
                                         path))
            if not os.path.isfile(self._datafile):
                raise FileNotFoundError("{}: DataFile {} not found"
                                        .format(self.formatIdentity(),
                                                self._datafile))
            self._markfile = self._genPath(
                    dirpath,
                    base,
                    self._CACHE["Common Infos"].get("MarkerFile"))
            if self._markfile:
                if not os.path.isfile(self._markfile):
                    raise FileNotFoundError("{}: MarkerFile {} not found"
                                            .format(self.formatIdentity(),
                                                    self._markfile))
                t = None
                with open(self._markfile, "r") as f:
                    for line in f.readlines():
                        if re.


            # Series number and secription is not defined
            self.setAttribute(self, "SeriesNumber", index)
            self.setAttribute(self, "SeriesDescription", base)

        self.index = index

    def _getField(self, field: list):
        res = None
        try: 
            if field[0] in self.__spetialFields:
                res = self._adaptMetaField(field[0])
            else:
                res = self._CACHE[field[0]][field[1]]
        except Exception as e: 
            logger.warning("{}: Could not parse '{}'"
                           .format(self.recIdentity(), field))
            res = None
        return res

    def recNo(self):
        return self.getField( "SeriesNumber", 0)

    def recId(self):
         seriesdescr = self.getField("SeriesDescription", "unknown")
         return seriesdescr.strip()

    def isCompleteRecording(self):
        return True

    def clearCache(self) -> None:
        self._CACHE = ConfigParser()
        self._FILE_CACHE = ""

    def copyRawFile(self, destination: str) -> None:
        base = self.currentFile(True).splitext()[0]
        dest_base = os.path.join(destination, base)

        # Copiyng header
        dest_vhdr = dest_base + ".vhdr"
        if os.path.isfile(dest_vhdr):
            logger.warning("{}: File {} exists at destination"
                           .format(self.recIdentity(),
                                   self.currentFile(True)))

        with open(self.currentFile(), "r") as f_in,\
                open(dest_vhdr, "w") as f_out:
            for line in f_in.readlines():
                line = re.sub("DataFile *=.*", 
                              "DataFile={}.eeg".format(base),
                              line)
                f_out.write(line)

        # Copying marker file
        dest_vmrk = dest_base + ".vmrk"
        if self._markfile:
            with open(self._markfile, "r") as f_in,\
                    open(dest_vmrk, "w") as f_out:
                for line in f_in.readlines():
                    line = re.sub("DataFile *=.*", 
                                  "DataFile={}.eeg".format(base),
                                  line)
                    f_out.write(line)

        # Copiyng data file
        dest_vhdr = dest_base + ".eeg"
        shutil.copy2(self._datafile, dest_vhdr)
                     

    def _getSubId(self) -> str:
        return "unknown"

    def _getSesId(self) -> str:
        return ""

    def acqTime(self) -> datetime:
        res =  datetime.datetime(1900, 1, 1, 0, 0)
        if self._markfile:
            with open(self._markfile, )
