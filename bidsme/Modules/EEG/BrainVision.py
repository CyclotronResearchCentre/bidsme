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

import pandas

from datetime import datetime

from ..common import action_value, retrieveFormDict
from .EEG import EEG, channel_types
from . import _EDF
from .._formats import MNE, _MNE
logger = logging.getLogger(__name__)


class BrainVision(EEG):
    _type = "BrainVision"

    __slots__ = ["_FILE_CACHE",
                 "_mne",
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

            if self.setManufacturer(self._ext, _MNE.MANUFACTURERS):
                self.resetMetaFields()
                self.setupMetaFields(_EDF.metafields)
                self.testMetaFields()

    def _load_channels(self) -> pandas.DataFrame:
        return self.mne.load_channels()

    def _load_events(self) -> pandas.DataFrame:
        return self.mne.load_events(stim_channels=channel_types["TRIG"])

    def _getAcqTime(self) -> datetime:
        """
        Virtual function that returns acquisition time, i.e.
        time corresponding to the first data of file

        Returns
        -------
        datetime
            datetime of acquisition of current scan
        """
        return self.mne.CACHE.info["meas_date"]

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
