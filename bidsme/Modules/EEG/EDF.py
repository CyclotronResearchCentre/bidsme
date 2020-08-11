###############################################################################
# EDF.py provides an implementation of EDF class of EEG subclass
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
import mne
import json
import pandas
from mne.io.constants import FIFF

from datetime import datetime

from ..common import action_value, retrieveFormDict
from .EEG import EEG
from ..formats import _MNE
from ..formats import MNE

logger = logging.getLogger(__name__)


class EDF(EEG, MNE):
    _type = "BrainVision"

    __slots__ = ["_FILE_CACHE",
                 "_sub_info", "_rec_info",
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

        EEG.__init__(self)
        MNE.__init__(self)

        self._FILE_CACHE = None

        self._sub_info = list()
        self._ses_info = list()

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
        if os.path.isfile(file) and file.endswith(".edf"):
            if os.path.basename(file).startswith("."):
                logger.warning('{}: file {} is hidden'
                               .format(cls.formatIdentity(),
                                       file))

            cls.load_raw(file, ".edf")
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

            self._ext = ".edf"
            self._CACHE = self.load_raw(
                    path, self._ext,
                    eog=self.eog_channels,
                    misc=self.misc_channels)

            base = self.path[:-len(self._ext)]

            # Loading channels information
            if os.path.isfile(base + "_channels.tsv"):
                self.TableChannels = pandas.DataFrame\
                        .read_csv(base + "_channels.tsv",
                                  sep="\t",
                                  header=0,
                                  index=["name"],
                                  na_values="n/a")
            else:
                self.TableChannels = self.load_channels(
                        columns=self._chan_BIDS.getActive())
            if self.TableChannels is not None:
                for col_name in ("name", "type", "units"):
                    if col_name not in self.TableChannels.columns:
                        logger.warning("{}: Missing mandatory channel column {}"
                                       .format(self.recIdentity(), col_name))

            # mne do not retrieve subject and recording info
            with open(path, "rb") as f:
                f.seek(8)
                res = f.read(80).decode("ascii").strip()
                self._sub_info = res.split(" ")
                res = f.read(80).decode("ascii").strip()
                self._rec_info = res.split(" ")

            if self.setManufacturer(self._ext, _MNE.MANUFACTURERS):
                self.resetMetaFields()
                self.setupMetaFields(_MNE.metafields)
                self.testMetaFields()

    def _getAcqTime(self) -> datetime:
        """
        Virtual function that returns acquisition time, i.e.
        time corresponding to the first data of file

        Returns
        -------
        datetime
            datetime of acquisition of current scan
        """
        return self._CACHE.info["meas_date"]

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
        d = dict(self._CACHE.info)
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
                res = retrieveFormDict(field, self._CACHE.info,
                                       fail_on_not_found=True,
                                       fail_on_last_not_found=True)
        except Exception:
            logger.warning("{}: Could not parse '{}'"
                           .format(self.recIdentity(), field))
            res = None
        return res

    def recNo(self) -> int:
        """
        Virtual function returning current serie number
        (i.e. numero of scan in session).
        recNo together with recId must uniquely
        identify serie within session

        Returns
        -------
        int:
            Number of current serie, or 0 if not defined
        """
        return self.index

    def recId(self) -> str:
        """
        Virtual function returning current serie id
        (i.e. name of scan in session).
        recNo together with recId must uniquely
        identify serie within session

        Returns
        -------
        str:
            The Id string of current serie
        """
        if len(self._rec_info) >= 3 and self._rec_info[0] == "Startdate":
            return self._rec_info[2]
        return os.path.splitext(self.currentFile(True))[0]

    def isCompleteRecording(self) -> bool:
        """
        Virtual function.
        Returns True if current recording is complete,
        False overwise.

        Returns
        -------
        bool:
            True if scan is complete, False otherwise
        """
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
        if len(self._sub_info) > 0:
            return self._sub_info[0]
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
        return self._mne_adaptMetaField(field)

    def copyRawFile(self, destination: str) -> None:
        base = os.path.splitext(self.currentFile(True))[0]
        dest_base = os.path.join(destination, base)

        # Copiyng header
        shutil.copy2(self.currentFile(), destination)

        dig = self._CACHE.info['dig']

        orient = _MNE.ORIENTATION.get(self._ext, 'n/a')
        unit = _MNE.UNITS.get(self._ext, 'n/a')
        manufacturer = _MNE.MANUFACTURERS.get(self._ext, 'n/a')

        if dig:
            # exporting coord system
            coords = dict()
            landmarks = {d['ident']: d for d in dig
                         if d['kind'] == FIFF.FIFFV_POINT_CARDINAL}
            if landmarks:
                if FIFF.FIFFV_POINT_NASION in landmarks:
                    coords['NAS'] = landmarks[FIFF.FIFFV_POINT_NASION]['r']\
                            .tolist()
                if FIFF.FIFFV_POINT_LPA in landmarks:
                    coords['LPA'] = landmarks[FIFF.FIFFV_POINT_LPA]['r']\
                            .tolist()
                if FIFF.FIFFV_POINT_RPA in landmarks:
                    coords['RPA'] = landmarks[FIFF.FIFFV_POINT_RPA]['r']\
                            .tolist()

            hpi = {d['ident']: d for d in dig
                   if d['kind'] == FIFF.FIFFV_POINT_HPI}
            if hpi:
                for ident in hpi.keys():
                    coords['coil%d' % ident] = hpi[ident]['r'].tolist()

            coord_frame = set([dig[ii]['coord_frame']
                              for ii in range(len(dig))])
            if len(coord_frame) > 1:
                raise ValueError('All HPI, electrodes, and fiducials '
                                 'must be in the '
                                 'same coordinate frame. Found: "{}"'
                                 .format(coord_frame))
            coordsystem_desc = _MNE.COORD_FRAME_DESCRIPTIONS\
                .get(coord_frame[0], "n/a")
            fid_json = {
                'CoordinateSystem': coord_frame[0],
                'CoordinateUnits': unit,
                'CoordinateSystemDescription': coordsystem_desc,
                'Coordinates': coords,
                'LandmarkCoordinateSystem': orient,
                'LandmarkCoordinateUnits': unit
                }
            json.dump(dest_base + "_coordsystem.json", fid_json)

            # exporting electrodes
            elec = self._elec_BIDS.GetTemplate()
            with open(dest_base + "_electrodes.tsv", "w") as f:
                f.write(self._elec_BIDS.GetHeader() + "\n")
                for ch in self._CACHE.info['chs']:
                    elec["name"] = ch['ch_name']
                    if mne.utils_check_ch_locs([ch]):
                        elec["x"] = ch['loc'][0]
                        elec["y"] = ch['loc'][1]
                        elec["z"] = ch['loc'][2]
                    else:
                        elec["x"] = None
                        elec["y"] = None
                        elec["z"] = None
                    f.write(self._elec_BIDS.GetLine(elec) + "\n")
            self._elec_BIDS.DumpDefinitions(dest_base + "_electrodes.json")

        # exporting channels
        channels = self._chan_BIDS.GetTemplate()
        with open(dest_base + "_channels.tsv", "w") as f:
            f.write(self._chan_BIDS.GetHeader() + "\n")
            for idx, ch in enumerate(self._CACHE.info['chs']):
                channels["name"] = ch["ch_name"]
                ch_type = mne.io.pick.channel_type(self._CACHE.info, idx)
                if ch_type in ('mag', 'ref_meg', 'grad'):
                    ch_type = _MNE.COIL_TYPES_MNE.get(ch['coil_type'], ch_type)
                channels["type"] = _MNE.CHANNELS_TYPE_MNE_BIDS.get(ch_type)
                if ch["ch_name"] in self._CACHE.info['bads']:
                    channels["status"] = "bad"
                else:
                    channels["status"] = "good"
                channels["low_cutoff"] = self._CACHE.info["highpass"]
                channels["high_cutoff"] = self._CACHE.info["lowpass"]

                if self._CACHE._orig_units:
                    channels["units"] = self._CACHE._orig_units\
                            .get(channels["name"])
                channels["sampling_frequency"] = self._CACHE.info["sfreq"]
                f.write(self._chan_BIDS.GetLine(channels) + "\n")
            self._chan_BIDS.DumpDefinitions(dest_base + "_channels.json")

        # exporting markers
        events = self._chan_BIDS.GetTemplate()
        with open(dest_base + "_events.tsv", "w") as f:
            sfreq = self._CACHE.info['sfreq']
            first_time = self._CACHE.first_time
            evts = self._CACHE.annotations
            f.write(self._task_BIDS.GetHeader() + "\n")
            events = self._task_BIDS.GetTemplate()
            for ev in evts:
                events["onset"] = ev["onset"] - first_time
                events["duration"] = ev["duration"]
                events["trial_type"] = ev["description"]
                events["sample"] = int(events["onset"] * sfreq)
                f.write(self._task_BIDS.GetLine(events) + "\n")

            # stimulus channels
            first_samp = self._CACHE.first_samp
            for ch in self._CACHE.info["chs"]:
                if ch["kind"] != "sitm":
                    continue
                evts = mne.find_events(self._CACHE, stim_channel=ch["ch_name"])
                for ev in evts:
                    events["onset"] = (ev['onset'] - first_samp) / sfreq
                    events["duration"] = 0
                    events["trial_type"] = ch["ch_name"]
                    events["value"] = ev[2]
                    events["sample"] = ev["onset"] - first_samp
                    f.write(self._task_BIDS.GetLine(events) + "\n")
            self._task_BIDS.DumpDefinitions(dest_base + "_events.json")
