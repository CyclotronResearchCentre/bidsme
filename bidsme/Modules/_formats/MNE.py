###############################################################################
# MNE.py provides an implementation of mne interface for EEG modalities
###############################################################################
# Copyright (c) 2019-2020, University of Liège
# Author: Nikita Beliy
# Owner: Liege University https://www.uliege.be
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

import logging
from pandas import DataFrame
import mne
from mne.io.constants import FIFF


from . import _MNE

logger = logging.getLogger(__name__)


class MNE(object):
    __slots__ = ["_CACHE"]

    def __init__(self):
        self._CACHE = None
        self._ext = ""

    @staticmethod
    def load_raw(self, file: str, ext: str) -> mne.BaseRaw:
        """
        load raw mne file

        Parameters
        ----------
        file: str
            path to file to load
        ext: str
            extension of file, will determine loader,
            if not set, extension used in _ext used

        mne.BaseRaw
            loaded raw file
        """
        return _MNE.reader[ext](file, preload=False)

    def load_events(self,
                    columns: list = [],
                    stim_channels: list = []) -> DataFrame:
        """
        loads events present in annotations and put them into DataFrame

        Parameters:
        ----------
        columns: list of str
            list of columns to create
            columns onset, duration, trial_type, sample and value
            are created automatically
        stim_channels: list of str
            list of channels used as markers

        Returns:
        --------
        DataFrame
            resulting dataframe
        """
        column_base = {"onset", "duration", "trial_type", "sample", "value"}
        columns = column_base.update(columns)
        sfreq = self._CACHE.info['sfreq']
        first_time = self._CACHE.first_time
        first_samp = self._CACHE.first_samp

        evts = self._CACHE.annotations
        n_evts = len(evts)

        d_evts = {key: [None] * n_evts for key in column_base}

        for idx, ev in enumerate(evts):
            d_evts["onset"][idx] = ev["onset"] - first_time
            d_evts["duration"][idx] = ev["duration"]
            d_evts["trial_type"][idx] = ev["description"]
            d_evts["sample"][idx] = int(ev["onset"] * sfreq)

        df = DataFrame(d_evts, columns=columns)

        for ch in self._CACHE.info["chs"]:
            if ch["ch_name"] not in stim_channels and ch["kind"] != "sitm":
                continue
            evts = mne.find_events(self._CACHE, stim_channel=ch["ch_name"])
            n_evts = len(n_evts)

            d_evts = {key: [None] * n_evts for key in column_base}
            for idx, ev in enumerate(evts):
                d_evts["onset"] = (ev['onset'] - first_samp) / sfreq
                d_evts["duration"] = 0
                d_evts["trial_type"] = ch["ch_name"]
                d_evts["value"] = ev[2]
                d_evts["sample"] = ev["onset"] - first_samp
            df = df.append(DataFrame(d_evts, columns=columns))

        df.set_index('onset', inplace=True)
        df.sort_index(inplace=True, na_position="first")
        return df

    def load_channels(self,
                      columns: list = [],
                      bad_channels: list = []) -> DataFrame:
        """
        loads channels from raw and put them into DataFrame

        Parameters:
        ----------
        columns: list of str
            list of columns to create
            name, type, status, low_cutoff, high_cutoff, units
            and sampling_frequency are created automatically
        bad_channels: list of str
            list of channels marked as bad

        Returns:
        --------
        DataFrame
            resulting dataframe
        """
        column_base = {"name", "type", "status", "low_cutoff", "high_cutoff",
                       "units", "sampling_frequency"}
        columns = column_base.update(columns)

        n_channels = len(self._CACHE.info['chs'])
        d_chs = {key: [None] * n_channels for key in column_base}

        for idx, ch in enumerate(self._CACHE.info['chs']):
            d_chs["name"][idx] = ch["ch_name"]
            ch_type = mne.io.pick.channel_type(self._CACHE.info, idx)
            if ch_type in ('mag', 'ref_meg', 'grad'):
                ch_type = _MNE.COIL_TYPES_MNE.get(ch['coil_type'], ch_type)
            d_chs["type"][idx] = _MNE.CHANNELS_TYPE_MNE_BIDS.get(ch_type)

            if ch["ch_name"] in self._CACHE.info['bads']\
                    or ch["ch_name"] in bad_channels:
                d_chs["status"][idx] = "bad"
            else:
                d_chs["status"][idx] = "good"
            d_chs["low_cutoff"][idx] = self._CACHE.info["highpass"]
            d_chs["high_cutoff"][idx] = self._CACHE.info["lowpass"]

            if self._CACHE._orig_units:
                d_chs["units"][idx] = self._CACHE._orig_units\
                        .get(ch["ch_name"])
            d_chs["sampling_frequency"][idx] = self._CACHE.info["sfreq"]

        df = DataFrame(d_chs, columns=columns)
        df.set_index('name', inplace=True)

        return df

    def load_electrodes(self,
                        columns: list=[]) -> DataFrame:
        """
        loads hannels coordinates fron raw and put them into DataFrame

        Parameters:
        ----------
        columns: list of str
            list of columns to create
            name, x, y, z are created automatically

        Returns:
        --------
        DataFrame
            resulting dataframe
        """

        if self._CACHE.info['dig'] is None:
            # raw file don't have coordinate info
            return None

        column_base = {"name", "x", "y", "z"}
        columns = column_base.update(columns)
        n_channels = len(self._CACHE.info['chs'])
        d_chs = {key: [None] * n_channels for key in column_base}

        for ch in self._CACHE.info['chs']:
            d_chs["name"][idx] = ch['ch_name']
            if mne.utils._check_ch_locs([ch]):
                d_chs["x"][idx] = ch['loc'][0]
                d_chs["y"][idx] = ch['loc'][1]
                d_chs["z"][idx] = ch['loc'][2]
            else:
                d_chs["x"][idx] = None
                d_chs["y"][idx] = None
                d_chs["z"][idx] = None

        df = DataFrame(d_chs, columns=columns)
        df.set_index('name', inplace=True)

        return df

    def load_coordinates(self) -> dict:
        """
        retrieves reference frame from raw file

        Returns:
        --------
        dict
        """
        coords = dict() 
        dig = self._CACHE.info['dig']

        if not dig:
            return coords

        orient = _MNE.ORIENTATION.get(self._ext, 'n/a')
        unit = _MNE.UNITS.get(self._ext, 'n/a')
        manufacturer = _MNE.MANUFACTURERS.get(self._ext, 'n/a')


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


    def _mne_adaptMetaField(self, field):
        res = None
        if field == "RecordingDuration":
            return self._CACHE.times[-1]
        if field == "RecordingType":
            if isinstance(self._CACHE, mne.io.BaseRaw):
                return "continuous"
            elif isinstance(self._CACHE, mne.Epochs):
                return "epoched"
            return None
        if field == "MEGChannelCount":
            return len([ch for ch in self._CACHE.info['chs']
                       if ch['kind'] == FIFF.FIFFV_MEG_CH])
        if field == "MEGREFChannelCount":
            return len([ch for ch in self._CACHE.info['chs']
                       if ch['kind'] == FIFF.FIFFV_REF_MEG_CH])
        if field == "ECOGChannelCount":
            return len([ch for ch in self._CACHE.info['chs']
                       if ch['kind'] == FIFF.FIFFV_ECOG_CH])
        if field == "SEEGChannelCount":
            return len([ch for ch in self._CACHE.info['chs']
                       if ch['kind'] == FIFF.FIFFV_SEEG_CH])
        if field == "EEGChannelCount":
            return len([ch for ch in self._CACHE.info['chs']
                       if ch['kind'] == FIFF.FIFFV_EEG_CH])
        if field == "EOGChannelCount":
            return len([ch for ch in self._CACHE.info['chs']
                       if ch['kind'] == FIFF.FIFFV_EOG_CH])
        if field == "ECGChannelCount":
            return len([ch for ch in self._CACHE.info['chs']
                       if ch['kind'] == FIFF.FIFFV_ECG_CH])
        if field == "EMGChannelCount":
            return len([ch for ch in self._CACHE.info['chs']
                       if ch['kind'] == FIFF.FIFFV_EMG_CH])
        if field == "MiscChannelCount":
            return len([ch for ch in self._CACHE.info['chs']
                       if ch['kind'] == FIFF.FIFFV_MISC_CH])
        if field == "TriggerChannelCount":
            return len([ch for ch in self._CACHE.info['chs']
                       if ch['kind'] == FIFF.FIFFV_STIM_CH])
        return res
