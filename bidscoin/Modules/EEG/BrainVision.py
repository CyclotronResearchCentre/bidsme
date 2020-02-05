from .EEG import EEG
from bidsMeta import MetaField
from tools import tools

import os
import logging
import json
import shutil
import pprint
from datetime import datetime, timedelta

from configparser import ConfigParser

logger = logging.getLogger(__name__)

class BrainVision(EEG):
    _type = "BrainVision"

    __slots__ = ["_CACHE", "_FILE_CACHE",
                 "_datafile", "_markfile"]

    def __init__(self, rec_path=""):
        super().__init__()

        self._CACHE = None
        self._FILE_CACHE = ""
        self._datafile = None
        self.__markfile = None

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
            self._CACHE = ConfigParser()
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
            self._markfile = iself._genPath(
                    dirpath,
                    base,
                    self._CACHE["Common Infos"].get("MarkerFile"))
            if self._markfile:
                if not os.path.isfile(self._markfile):
                    raise FileNotFoundError("{}: MarkerFile {} not found"
                                            .format(self.formatIdentity(),
                                                    self._markfile))
        self.index = index


