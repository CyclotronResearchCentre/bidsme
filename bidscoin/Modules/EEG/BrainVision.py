from .EEG import EEG
from bidsMeta import MetaField

import os
import re
import logging
import shutil
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class BrainVision(EEG):
    _type = "BrainVision"

    __slots__ = ["_CACHE", "_FILE_CACHE",
                 "_MRK_CACHE",
                 "_datafile", "_markfile",
                 "_acqTime"]
    __spetialFields = {}
    __fileversion = "Brain Vision Data Exchange Header File Version 1.0"

    def __init__(self, rec_path=""):
        from configparser import ConfigParser
        super().__init__()

        self._CACHE = ConfigParser(allow_no_value=True)
        self._MRK_CACHE = ConfigParser()
        self._FILE_CACHE = ""
        self._datafile = None
        self.__markfile = None
        self._acqTime = datetime(1900, 1, 1, 0, 0)
        # Series number and secription is not defined
        self.setAttribute("SeriesNumber", 0)
        self.setAttribute("SeriesDescription", "unknown")

        if rec_path:
            self.setRecPath(rec_path)

        self.metaFields["SamplingFrequency"]\
            = MetaField("<SamplingFrequency>", 1.)

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
            with open(file, "r", encoding="utf-8") as f:
                decl = f.readline().strip()
                if decl != cls.__fileversion:
                    return False
            return True
        return False

    def loadFile(self, index: int) -> None:
        path = os.path.join(self._recPath, self.files[index])
        if not self.isValidFile(path):
            raise ValueError("{}: {} is not valid file"
                             .format(self.formatIdentity(), path))
        if path != self._FILE_CACHE:
            self.clearCache()
            dirpath, base = os.path.split(path)
            base = os.path.splitext(base)[0]

            with open(path, "r", encoding="utf-8") as f:
                f.readline()
                self._CACHE.read_file(f, source=path)

            self._datafile = self._genPath(
                    dirpath,
                    base,
                    self._CACHE["Common Infos"]["DataFile"])
            if not self._datafile:
                raise ValueError("{}: {} DataFile not defined"
                                 .format(self.formatIdentity(),
                                         path))
            if not self.getField("Common Infos/SamplingInterval"):
                raise KeyError("{}: Sampling interval not defined"
                               .format(self.formatIdentity()))
            self.setAttribute("SamplingInterval",
                              self.getAttribute(
                                  "float:Common Infos/SamplingInterval")
                              )

            if not os.path.isfile(self._datafile):
                raise FileNotFoundError("{}: DataFile {} not found"
                                        .format(self.formatIdentity(),
                                                self._datafile))
            self._markfile = self._genPath(
                    dirpath,
                    base,
                    self._CACHE["Common Infos"].get("MarkerFile"))
            self._acqTime = datetime(1900, 1, 1, 0, 0)
            if self._markfile:
                if not os.path.isfile(self._markfile):
                    raise FileNotFoundError("{}: MarkerFile {} not found"
                                            .format(self.formatIdentity(),
                                                    self._markfile))
                with open(self._markfile, "r", encoding="utf-8") as f:
                    decl = f.readline().strip()
                    if not decl != self.__fileversion:
                        raise ValueError("{}: Incorrect Marker file version {}"
                                         .format(self.formatIdentity(),
                                                 decl))
                    self._MRK_CACHE.read_file(f, source=self._markfile)
                    t = None
                    for mk, val in self._MRK_CACHE["Marker Infos"].items():
                        val = val.split(",")
                        if val[0].strip() == "New Segment":
                            t = datetime.strptime(val[5], "%Y%m%d%H%M%S%f")
                            dt = timedelta(microseconds=self.getAttribute(
                                "SamplingInterval"))
                            dt = int(val[2]) * dt
                            t = t - dt
                            break
                    if not t:
                        logger.warning("{}: Marker file do not contain any "
                                       "'New Segment' markers"
                                       .format(self.formatIdentity()))
                    else:
                        self._acqTime = t

            # Series number and secription is not defined
            self.setAttribute("SeriesNumber", index)
            self.setAttribute("SeriesDescription", base)
            self.setAttribute(
                    "SamplingFrequency",
                    1e6 / self.getAttribute("SamplingInterval"))

        self.index = index

    def acqTime(self) -> datetime:
        return self._acqTime

    def dump(self):
        if not self._FILE_CACHE:
            if len(self.files) > 0:
                self.loadFile(0)
            else:
                logger.error("{}: No defined files"
                             .format(self.recIdentity()))
                return "No defined files"
        res = ""
        for section in self._CACHE.sections():
            line = "[{}]\n".format(section)
            res += line
            for key, val in self._CACHE.items(section):
                line = "{} = {}\n".format(key, val)
                res += line
            res += '\n'
        return res

    def _getField(self, field: list):
        res = None
        try:
            if field[0] in self.__spetialFields:
                res = self._adaptMetaField(field[0])
            else:
                res = self._CACHE[field[0]][field[1]]
        except Exception:
            logger.warning("{}: Could not parse '{}'"
                           .format(self.recIdentity(), field))
            res = None
        return res

    def _transformField(self, value, prefix: str):
        if prefix == "":
            return value
        elif prefix == "int":
            return int(value)
        elif prefix == "float":
            return float(value)
        elif prefix.startswith("ch_"):
            det = prefix[len("ch_"):]
            val = value.split(',')
            if det == "name":
                return val[0]
            elif det == "ref":
                return val[1]
            elif det ==  "resolution":
                return float(val[2])
            elif det == "unit":
                return val[3]

        logger.warning("{}/{}: Unknown field prefix {}"
                       .format(self.formatIdentity(),
                               prefix))
        return value
                

    def recNo(self):
        return self.getAttribute("SeriesNumber", 0)

    def recId(self):
        seriesdescr = self.getAttribute("SeriesDescription", "unknown")
        return seriesdescr.strip()

    def isCompleteRecording(self):
        return True

    def clearCache(self) -> None:
        from configparser import ConfigParser
        self._CACHE = ConfigParser(allow_no_value=True)
        self._MRK_CACHE = ConfigParser()
        self._FILE_CACHE = ""

    def copyRawFile(self, destination: str) -> None:
        base = os.path.splitext(self.currentFile(True))[0]
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
                if self._markfile:
                    line = re.sub("MarkerFile *=.*",
                                  "MarkerFile={}.eeg".format(base),
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

    def _post_copy(self, basename: str, ext: str) -> None:
        shutil.copy2(self._datafile, basename + ".eeg")

        if self._markfile:
            dest_vmrk = basename + ".vmrk"
            base = os.path.basename(basename)
            with open(self._markfile, "r") as f_in,\
                    open(dest_vmrk, "w") as f_out:
                for line in f_in.readlines():
                    line = re.sub("DataFile *=.*",
                                  "DataFile={}.eeg".format(base),
                                  line)
                    f_out.write(line)
            for mk, val in self._MRK_CACHE["Marker Infos"].items():
                val = val.split(",")



    def _getSubId(self) -> str:
        return "unknown"

    def _getSesId(self) -> str:
        return ""

    ########################
    # Additional fonctions #
    ########################
    def _genPath(self, dirpath: str, base: str, name: str) -> str:
        """
        Generates a path to dile based on Data/MarkerFile
        entry in header

        Parameters
        ----------
        dirpath: str
            path to directory containing header file
        base: str
            header file base name
        name: str
            name of file as found in header file

        Returnds
        --------
        str:
            path to referenced file
        """
        name = re.sub("\$b", base, name)
        return os.path.join(dirpath, name)
