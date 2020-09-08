###############################################################################
# BrainVision.py provides the implementation of EEG class for BrainVision
# file format
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

from ..common import action_value
from .EEG import EEG
from bidsMeta import MetaField

import os
import re
import logging
import shutil
import json
import math
import gzip
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class BrainVision(EEG):
    _type = "BrainVision"

    __slots__ = ["_CACHE", "_FILE_CACHE",
                 "_MRK_CACHE",
                 "_datafile", "_markfile",
                 "_chanValues"
                 ]
    __spetialFields = {
                       "SamplingFrequency",
                       "SamplingInterval"
                       }
    __fileversion = "Brain Vision Data Exchange Header File Version 1.0"

    def __init__(self, rec_path=""):
        from configparser import ConfigParser
        super().__init__()

        self._CACHE = ConfigParser(allow_no_value=True, strict=False)
        self._MRK_CACHE = ConfigParser()
        self._FILE_CACHE = ""
        self._datafile = None
        self.__markfile = None
        # Series number and secription is not defined

        self._chan_BIDS.Activate("sampling_frequency")
        self._chan_BIDS.Activate("reference")
        self._chan_BIDS.AddField(
                name="resolution",
                longName="Channel signal resolution",
                override=True
                )

        self._task_BIDS.Activate("sample")
        self._task_BIDS.Activate("trial_type")

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

    def _loadFile(self, path: str) -> None:
        if path != self._FILE_CACHE:
            self.clearCache()
            dirpath, base = os.path.split(path)
            base = os.path.splitext(base)[0]

            with open(path, "r", encoding="utf-8") as f:
                f.readline()
                self._CACHE.read_file(self._readline_generator(f),
                                      source=path)

            self._datafile = self._genPath(
                    dirpath,
                    base,
                    self._CACHE["Common Infos"]["DataFile"])
            if not self._datafile:
                raise ValueError("{}: {} DataFile not defined"
                                 .format(self.formatIdentity(),
                                         path))
            if not self.getField("SamplingInterval"):
                raise KeyError("{}: Sampling interval not defined"
                               .format(self.formatIdentity()))

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

    def _getAcqTime(self) -> datetime:
        t = None
        if self._markfile:
            with open(self._markfile, "r", encoding="utf-8") as f:
                decl = f.readline().strip()
                if not decl != self.__fileversion:
                    raise ValueError("{}: Incorrect Marker file version {}"
                                     .format(self.formatIdentity(),
                                             decl))
                self._MRK_CACHE.read_file(f, source=self._markfile)
                for mk, val in self._MRK_CACHE["Marker Infos"].items():
                    val = val.split(",")
                    if val[0].strip() == "New Segment":
                        t = datetime.strptime(val[5], "%Y%m%d%H%M%S%f")
                        dt = timedelta(microseconds=self.getField(
                            "SamplingInterval"))
                        dt = int(val[2]) * dt
                        t = t - dt
                        break
        if t is None:
            logger.warning("{}: Marker file do not contain any "
                           "'New Segment' markers"
                           .format(self.formatIdentity()))
        return t

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
        if prefix.startswith("ch_"):
            det = prefix[len("ch_"):]
            val = value.split(',')
            if det == "name":
                return val[0]
            elif det == "ref":
                return val[1]
            elif det == "resolution":
                return float(val[2])
            elif det == "unit":
                return val[3]

        try:
            return action_value(value, prefix)
        except Exception as e:
            logger.error("{}: Invalid field prefix {}:{}"
                         .format(self.formatIdentity(),
                                 prefix, e))
            raise

    def recNo(self):
        return self.index

    def recId(self):
        return os.path.splitext(self.currentFile(True))[0]

    def isCompleteRecording(self):
        return True

    def clearCache(self) -> None:
        from configparser import ConfigParser
        self._CACHE = ConfigParser()
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
                                  "MarkerFile={}.vmrk".format(base),
                                  line)
                else:
                    line = re.sub("MarkerFile *=.*", "")
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

    def _copy_bidsified(self, directory: str, bidsname: str, ext: str) -> None:
        """
        Copy all data files to destination, and adapt file references.
        Also creates channels, electrodes and events tsv files

        Parameters
        ----------
        directory: str
            destination directory where files should be copies,
            including modality folder. Assured to exists.
        bidsname: str
            bidsified name without extention
        ext: str
            extention of the data file
        """
        # Copiyng header
        dest_vhdr = os.path.join(directory, bidsname + ext)
        with open(self.currentFile(), "r") as f_in,\
                open(dest_vhdr, "w") as f_out:
            for line in f_in.readlines():
                line = re.sub("DataFile *=.*",
                              "DataFile={}.eeg".format(bidsname),
                              line)
                f_out.write(line)
        # copiyng data file
        out_name = os.path.join(directory, bidsname + ".eeg")
        if self.zip:
            with open(self._datafile, 'rb') as f_in:
                with gzip.open(out_name + ".gz", 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            shutil.copy2(self._datafile,
                         os.path.join(out_name))

        # Getting channels info
        base = bidsname.rsplit("_", 1)[0]
        dest_chan = os.path.join(directory, base + "_channels")
        with open(dest_chan + ".tsv", "w") as f:
            f.write(self._chan_BIDS.GetHeader())
            f.write("\n")
            for key, val in self._CACHE["Channel Infos"].items():
                chanValues = self._chan_BIDS.GetTemplate()
                val = val.split(",")
                chanValues["name"] = val[0]
                chanValues["type"] = None
                chanValues["reference"] = val[1]
                chanValues["sampling_frequency"] = \
                    self.getField("SamplingFrequency")
                chanValues["resolution"] = float(val[2])
                if len(val) >= 4:
                    chanValues["units"] = val[3]
                f.write(self._chan_BIDS.GetLine(chanValues))
                f.write("\n")
            self._chan_BIDS.DumpDefinitions(dest_chan + ".json")

        # Getting electrodes info
        if "Coordinates" in self._CACHE:
            dest_elec = os.path.join(directory, base)
            dest_elec = re.sub("task-", "acq-", )
            with open(dest_elec + ".tsv", "w") as f:
                f.write(self._elec_BIDS.GetHeader())
                f.write("\n")
                for key, val in self._CACHE["Coordinates"].items():
                    chanValues = self._elec_BIDS.GetTemplate()
                    val = val.split(",")
                    chanValues["name"] = self._CACHE["Channel Infos"]\
                        .get(key).split(",")[0]
                    r = float(val[0])

                    theta = math.pi * float(val[1]) / 180
                    phi = math.pi * float(val[2]) / 180
                    if r == 0:
                        chanValues["x"] = None
                        chanValues["y"] = None
                        chanValues["z"] = None
                    else:
                        chanValues["x"] = r * math.sin(theta) * math.cos(phi)
                        chanValues["y"] = r * math.sin(theta) * math.sin(phi)
                        chanValues["z"] = r * math.cos(theta)
                    f.write(self._elec_BIDS.GetLine(chanValues))
                    f.write("\n")
                self._elec_BIDS.DumpDefinitions(dest_elec + ".json")
                dest_coord = os.path.join(directory,
                                          "{}_acq-{}_coordsystem.json"
                                          .format(self.getBidsPrefix(),
                                                  self.labels["task"]))
                d = {"EEGCoordinateSystem": "BESA",
                     "EEGCoordinateSystemUnits": "mm"}
                with open(dest_coord, "w") as f:
                    json.dump(d, f, indent="  ", separators=(',', ':'))

        # Gettin markers info
        if self._markfile:
            dest_vmrk = os.path.join(directory, bidsname + ".vmrk")
            with open(self._markfile, "r") as f_in,\
                    open(dest_vmrk, "w") as f_out:
                for line in f_in.readlines():
                    line = re.sub("DataFile *=.*",
                                  "DataFile={}.eeg".format(bidsname),
                                  line)
                    f_out.write(line)

            dest_vmrk = os.path.join(directory, base + "_events")
            with open(dest_vmrk + ".tsv", "w") as f:
                last_onset = 0
                last_onset = 0
                dt = timedelta(
                        microseconds=self.getField("SamplingInterval"))
                f.write(self._task_BIDS.GetHeader())
                f.write("\n")
                for mk, val in self._MRK_CACHE["Marker Infos"].items():
                    mrkValues = self._task_BIDS.GetTemplate()
                    val = val.split(",")
                    name = val[0]
                    # descr = val[1]
                    pos = int(val[2])
                    dur = dt * int(val[3])
                    # chan = val[4]

                    if name.strip() == "New Segment":
                        last_onset = datetime.strptime(val[5],
                                                       "%Y%m%d%H%M%S%f")\
                                - self.acqTime()
                        last_seg = pos
                    mrkValues["onset"] = ((pos - last_seg) * dt + last_onset)\
                        .total_seconds()
                    mrkValues["duration"] = dur
                    mrkValues["sample"] = pos
                    mrkValues["trial_type"] = name
                    f.write(self._task_BIDS.GetLine(mrkValues))
                    f.write("\n")
            self._task_BIDS.DumpDefinitions(dest_vmrk + ".json")

    def _getSubId(self) -> str:
        return None

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
        name = re.sub("\\$b", base, name)
        return os.path.join(dirpath, name)

    def _adaptMetaField(self, field: str):
        if field == "SamplingFrequency":
            return 1e6 / self.getField("SamplingInterval")
        if field == "SamplingInterval":
            return float(self.getField("Common Infos/SamplingInterval"))
        return None

    def _readline_generator(self, fp):
        line = fp.readline()
        while line:
            if '[Comment]' in line:
                break
            else:
                yield line
                line = fp.readline()
