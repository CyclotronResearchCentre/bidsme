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

import os
import logging
import shutil
from datetime import datetime
import re
import pandas

from ..common import retrieveFormDict
from .EEG import EEG, channel_types
from . import _EDF
from .._formats import _MNE
from .._formats.MNE import MNE
logger = logging.getLogger(__name__)


class BrainVision(EEG):
    _type = "BrainVision"

    __slots__ = ["_FILE_CACHE",
                 "_mne",
                 "_data_file",
                 "_marker_file"
                 ]

    __specialFields = {"RecordingDuration",
                       "RecordingType",
                       "MEGChannelCount",
                       "MEGREFChannelCount",
                       "ECOGChannelCount",
                       "SEEGChannelCount",
                       "EEGChannelCount",
                       "EOGChannelCount",
                       "ECGChannelCount",
                       "EMGChannelCount",
                       "MiscChannelCount",
                       "TriggerChannelCount"}

    def __init__(self, rec_path=""):
        super().__init__()

        self._FILE_CACHE = None
        self.mne = MNE()
        self._data_file = None
        self._marker_file = None

        if rec_path:
            self.setRecPath(rec_path)

    ################################
    # reimplementation of virtuals #
    ################################
    @classmethod
    def _isValidFile(cls, file: str) -> bool:
        """
        Virtual function that checks if file is valid one

        Parameters
        ----------
        file: str
            path to file to test

        Returns
        -------
        bool:
            True if file is valid for current class
        """
        if os.path.isfile(file) and file.endswith(".vhdr"):
            if os.path.basename(file).startswith("."):
                logger.warning('{}: file {} is hidden'
                               .format(cls.formatIdentity(),
                                       file))
            MNE.test_raw(file, ".vhdr")
            return True
        return False

    def _loadFile(self, path: str) -> None:
        """
        Virtual function that load file at given path

        Parameters
        ----------
        path: str
            path to file to load
        """
        if path != self._FILE_CACHE:
            self.clearCache()

            self._ext = ".vhdr"
            self.mne.load_raw(path, self._ext)

            base = path[:-len(self._ext)]

            # Loading channels information
            self.load_channels(base)
            self.count_channels()
            self.load_events(base)
            self.load_electrodes(base)

            self._marker_file = None
            self._data_file = None
            with open(path, "r") as f:
                for line in f.readlines():
                    line = line.strip()
                    if line.startswith(';'):
                        continue
                    res = re.match("DataFile=([\\w. -]+)", line)
                    if res:
                        self._data_file = res.group(1).strip()
                        continue
                    res = re.match("MarkerFile=([\\w. -]+)", line)
                    if res:
                        self._marker_file = res.group(1).strip()
                        continue
                    if self._marker_file and self._data_file:
                        break

            if self.setManufacturer(self._ext, _MNE.MANUFACTURERS):
                self.resetMetaFields()
                self.setupMetaFields(_EDF.metafields)
                self.testMetaFields()

    def _load_channels(self) -> pandas.DataFrame:
        return self.mne.load_channels()

    def _load_events(self) -> pandas.DataFrame:
        return self.mne.load_events(stim_channels=channel_types["TRIG"])

    def _load_electrodes(self) -> pandas.DataFrame:
        return self.mne.load_electrodes()

    def _getAcqTime(self) -> datetime:
        """
        Virtual function that returns acquisition time, i.e.
        time corresponding to the first data of file

        Returns
        -------
        datetime
            datetime of acquisition of current scan
        """
        return self.mne.CACHE.info["meas_date"].replace(tzinfo=None)

    def dump(self) -> dict:
        """
        Virtual function that created adictionary of all meta-data
        associated with current file

        Returns
        -------
        dict:
            dictionary with parced values from current scan header,
            all data must be of basic python class: str, int, float,
            date, time, datetime
        """
        d = dict(self.mne.CACHE.info)
        return d

    def _getField(self, field: list, prefix: str = ""):
        """
        Virtual function that retrives the field value
        from recording metadata. field is garanteed to be
        non-empty

        Parameters
        ----------
        field: list(str)
            list of nested values (or just one element)
            giving position of field to retrieve
        prefix: str
            prefix indicating the transformation function
            to call on retrieved value

        Returns
        -------
            retrieved value or None if field not found

        Raises
        ------
        TypeError:
            if field value is not applicable to prefix
            function
        KeyError:
            if prefix function is not defined
        """
        res = None
        try:
            if field[0] in self.__specialFields:
                res = self._adaptMetaField(field[0])
            else:
                res = retrieveFormDict(field, self.mne.CACHE.info,
                                       fail_on_not_found=True,
                                       fail_on_last_not_found=True)
        except Exception:
            logger.warning("{}: Could not parse '{}'"
                           .format(self.recIdentity(), field))
            res = None
        return res

    def recNo(self):
        return self.index

    def recId(self):
        return os.path.splitext(self.currentFile(True))[0]

    def isCompleteRecording(self):
        return True

    def _getSubId(self) -> str:
        """
        Virtual function
        Returns subject id as defined in metadata

        Returns
        -------
        str:
            string representing Id of current subject as
            defined in header or None if such information
            is not defined
        """
        return None

    def _getSesId(self) -> str:
        """
        Virtual function
        Returns session id as defined in metadata

        Returns
        -------
        str:
            string representing Id of current session as
            defined in header or None if such information
            is not defined
        """
        return ""

    def _adaptMetaField(self, field):
        if field.endswith("ChannelCount"):
            field = field[:-len("ChannelCount")]
            return self._channels_count.get(field, 0)
        if field == "RecordingDuration":
            return self.mne.getDuration()
        if field == "RecordingType":
            if self.mne.isContinious():
                return "continuous"
            else:
                return "epoched"
        return None

    def _copy_bidsified(self, directory: str, bidsname: str, ext: str) -> None:
        """
        Virtual function that copies bidsified data files to
        its destinattion.

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

        out_base = os.path.join(directory, bidsname)
        f_in = open(self.currentFile(), "r")
        f_out = open(out_base + ext, "w")
        for line in f_in.readlines():
            ln = line.strip()
            if ln.startswith(";"):
                f_out.write(line)
                continue
            res = re.match("DataFile=([\\w. -]+)", ln)
            if res:
                if self._data_file:
                    print("DataFile={}".format(bidsname + ".eeg"), file=f_out)
                else:
                    logger.warning("{}: Missing data file"
                                   .format(self.recIdentity()))
                    f_out.write(line)
                continue
            res = re.match("MarkerFile=([\\w. -]+)", ln)
            if res:
                if self._data_file:
                    print("MarkerFile={}".format(bidsname + ".vmrk"),
                          file=f_out)
                else:
                    logger.warning("{}: Missing marker file"
                                   .format(self.recIdentity()))
                    f_out.write(line)
                continue
            f_out.write(line)
        f_in.close()
        f_out.close()

        if self._data_file:
            f = os.path.join(self._recPath, self._data_file)
            shutil.copy2(f, out_base + ".eeg")

        if self._marker_file:
            f_in = open(os.path.join(self._recPath, self._marker_file), "r")
            f_out = open(out_base + ".vmrk", "w")
            for line in f_in.readlines():
                ln = line.strip()
                if ln.startswith(";"):
                    f_out.write(line)
                    continue
                res = re.match("DataFile=([\\w. -]+)", ln)
                if res:
                    if self._data_file:
                        print("DataFile={}".format(bidsname + ".eeg"),
                              file=f_out)
                    else:
                        logger.warning("{}: Missing data file"
                                       .format(self.recIdentity()))
                        f_out.write(line)
                    continue
                f_out.write(line)
            f_in.close()
            f_out.close()

        dest_base = out_base.rsplit("_", 1)[0]

        if self.TableChannels is not None and\
                not self.TableChannels.index.empty:
            active = self._chan_BIDS.GetActive()
            columns = self.TableChannels.columns

            for col in active:
                if col not in columns:
                    self._chan_BIDS.Activate(col, False)
            active = [col for col in active
                      if col in columns
                      and self.TableChannels[col].notna().any()]

            self.TableChannels.to_csv(dest_base + "_channels.tsv",
                                      columns=active,
                                      sep="\t", na_rep="n/a",
                                      header=True, index=True)
            self._chan_BIDS.DumpDefinitions(dest_base + "_channels.json")

        if self.TableEvents is not None and\
                not self.TableEvents.index.empty:
            active = self._task_BIDS.GetActive()
            columns = self.TableEvents.columns

            for col in active:
                if col not in columns:
                    self._task_BIDS.Activate(col, False)
            active = [col for col in active
                      if col in columns
                      and self.TableEvents[col].notna().any()]

            self.TableEvents.to_csv(dest_base + "_events.tsv",
                                    columns=active,
                                    sep="\t", na_rep="n/a",
                                    header=True, index=True)
            self._task_BIDS.DumpDefinitions(dest_base + "_events.json")

        if self.TableElectrodes is not None and\
                not self.TableElectrodes.index.empty:
            active = self._elec_BIDS.GetActive()
            columns = self.TableElectrodes.columns

            for col in active:
                if col not in columns:
                    self._elec_BIDS.Activate(col, False)
            active = [col for col in active
                      if col in columns
                      and self.TableElectrodes[col].notna().any()]

            self.TableElectrodes.to_csv(dest_base + "_events.tsv",
                                        columns=active,
                                        sep="\t", na_rep="n/a",
                                        header=True, index=True)
            self._elec_BIDS.DumpDefinitions(dest_base + "_events.json")

    def copyRawFile(self, destination: str) -> str:
        """
        Virtual function to Copy raw (non-bidsified) file
        to destination.
        Destination is an existing writable directory

        Parameters
        ----------
        destination: str
            output folder to copied files

        Returns
        -------
        str:
            path to copied file
        """
        shutil.copy2(self.currentFile(), destination)
        if self._data_file:
            f = os.path.join(self._recPath, self._data_file)
            shutil.copy2(f, destination)
        if self._marker_file:
            f = os.path.join(self._recPath, self._marker_file)
            shutil.copy2(f, destination)

        base = os.path.splitext(self.currentFile(True))[0]
        dest_base = os.path.join(destination, base)
        if self.TableChannels is not None:
            self.TableChannels.to_csv(dest_base + "_channels.tsv",
                                      sep="\t", na_rep="n/a",
                                      header=True, index=True)
        if self.TableEvents is not None:
            self.TableEvents.to_csv(dest_base + "_events.tsv",
                                    sep="\t", na_rep="n/a",
                                    header=True, index=True)
        if self.TableElectrodes is not None:
            self.TableElectrodes.to_csv(dest_base + "_electrodes.tsv",
                                        sep="\t", na_rep="n/a",
                                        header=True, index=True)
        return os.path.join(destination, self.currentFile(True))
