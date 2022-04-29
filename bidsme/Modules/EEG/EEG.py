###############################################################################
# EEG.py provides the base class for EEG recordings, all EEG classes should
# inherit from this class
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
import pandas
from abc import abstractmethod

from bidsme.bidsMeta import BIDSfieldLibrary
from bidsme.tools import paths

from ..base import baseModule
from . import _EEG


logger = logging.getLogger(__name__)

channel_kinds = {
        "MEG": ["MEGGRADAXIAL", "MEGMAG", "MEGGRADPLANAR", "MEGOTHER"],
        "MEGREF": ["MEGREFGRADAXIAL", "MEGREFMAG", "MEGREFGRADPLANAR"],
        "ECOG": ["ECOG"],
        "SEEG": ["SEEG"],
        "EEG": ["EEG", "DBS"],
        "EOG": ["EOG", "VEOG", "HEOG"],
        "ECG": ["ECG"],
        "EMG": ["EMG"],
        "Trigger": ["TRIG"],
        "Misc": ["MISC"]
    }

channel_types = {
        # EEG channels
        "AUDIO": [],
        "TEMP": [],
        "SYSCLOCK": [],
        "TRIG": [],
        "REF": [],
        "EEG": [],
        "EOG": [],
        "ECG": [],
        "EMG": [],
        "GSR": [],
        "HEOG": [],
        "VEOG": [],
        "MISC": [],
        "EYEGAZE": [],
        "PUPIL": [],
        "RESP": [],

        # Additional iEEG channels
        "SEEG": [],
        "ECOG": [],
        "DBS": [],
        "PD": [],
        "ADC": [],
        "DAC": [],

        # Additional MEG channels
        "MEGMAG": [],
        "MEGGRADAXIAL": [],
        "MEGGRADPLANAR": [],
        "MEGREFMAG": [],
        "MEGREFGRADAXIAL": [],
        "MEGREFGRADPLANAR": [],
        "MEGOTHER": [],
        "HLU": [],
        "FITERR": [],
        "OTHER": [],

        # Channels to ignore
        "__ignore__": [],
        "__bad__": []
        }


class EEG(baseModule):
    _module = "EEG"

    bidsmodalities = {
            "eeg": ("task", "acq", "run"),
            "meg": ("task", "acq", "run", "proc"),
            "ieeg": ("task", "acq", "run")
            }

    _chan_BIDS = BIDSfieldLibrary()
    _chan_BIDS.LoadDefinitions(os.path.join(paths.templates,
                                            "EEG_channels.json"))
    _elec_BIDS = BIDSfieldLibrary()
    _elec_BIDS.LoadDefinitions(os.path.join(paths.templates,
                                            "EEG_electrodes.json"))
    _task_BIDS = BIDSfieldLibrary()
    _task_BIDS.LoadDefinitions(os.path.join(paths.templates,
                                            "EEG_events.json"))

    __slots__ = ["TableChannels", "TableElectrodes", "TableEvents",
                 "_channels_count"]

    # Lists of EOG and Misc channels names
    def __init__(self):
        super().__init__()
        self.resetMetaFields()
        self.manufacturer = None

        self.TableChannels = None
        self.TableElectrodes = None
        self.TableEvents = None

        self._channels_count = dict.fromkeys(channel_kinds, 0)

    def resetMetaFields(self) -> None:
        """
        Resets currently defined meta fields dictionaries
        to None values
        """
        self.metaFields_req["__common__"] = {key: None for key in
                                             _EEG.eeg_meta_required_common}
        for mod in _EEG.eeg_meta_required_modality:
            self.metaFields_req[mod] = {key: None for key in
                                        _EEG.eeg_meta_required_modality[mod]}
        self.metaFields_rec["__common__"] = {key: None for key in
                                             _EEG.eeg_meta_recommended_common}
        for mod in _EEG.eeg_meta_recommended_modality:
            self.metaFields_rec[mod] = {key: None for key in
                                        _EEG.eeg_meta_recommended_modality[mod]
                                        }
        self.metaFields_opt["__common__"] = {key: None for key in
                                             _EEG.eeg_meta_optional_common}
        for mod in _EEG.eeg_meta_optional_modality:
            self.metaFields_opt[mod] = {key: None for key in
                                        _EEG.eeg_meta_optional_modality[mod]}

    def load_channels(self, base_name: str, ):
        """
        Loads channels data into TableChannels dataframe.
        If _channels.tsv is found together with loaded file,
        then data is loaded from this file, else virtual function
        _load_channels is used to extract channels info from
        data files.

        Parameters
        ----------
        base_name: str
            file path without extention
        """

        if os.path.isfile(base_name + "_channels.tsv"):
            self.TableChannels = pandas.read_csv(
                              base_name + "_channels.tsv",
                              sep="\t",
                              header=0,
                              index_col=["name"],
                              na_values="n/a")
        else:
            self.TableChannels = self._load_channels()
        if self.TableChannels is not None:
            # Checking columns validity
            if self.TableChannels.index.name != "name":
                logger.warning("{}: Index column is not 'name'"
                               .format(self.recIdentity()))
            for col_name in ("type", "units"):
                if col_name not in self.TableChannels.columns:
                    logger.warning("{}: Missing mandatory channel "
                                   "column '{}'"
                                   .format(self.recIdentity(), col_name))

            # Setting manual types
            if channel_types["__ignore__"]:
                self.TableChannels.drop(index=channel_types["__ignore__"],
                                        inplace=True, errors="ignore")
            for types, channels in channel_types.items():
                if types.startswith("__"):
                    if types == "__bad__"\
                            and "status" in self.TableChannels.columns:
                        chs = [ch for ch in channels
                               if ch in self.TableChannels.index]
                        if chs:
                            self.TableChannels.loc[chs, "status"] = "bad"
                    continue
                chs = [ch for ch in channels
                       if ch in self.TableChannels.index]
                if chs:
                    self.TableChannels.loc[chs, "type"] = types

    def count_channels(self) -> None:
        """
        Fills _channels_count field with count channels per type

        Must be called once after loading channels, and when channels
        are updated
        """
        if "type" not in self.TableChannels.columns:
            return

        counts = self.TableChannels["type"].value_counts()
        self._channels_count = dict.fromkeys(channel_kinds, 0)
        for ch, count in counts.items():
            found = False
            for kind, types in channel_kinds.items():
                if ch in types:
                    self._channels_count[kind] += count
                    found = True
            if not found:
                self._channels_count["Misc"] += count

    def load_events(self, base_name: str):
        """
        Loads events data into TableEvents dataframe.
        If _channels.tsv is found together with loaded file,
        then data is loaded from this file, else virtual function
        _load_channels is used to extract channels info from
        data files.

        Parameters
        ----------
        base_name: str
            file path without extention
        """

        if os.path.isfile(base_name + "_channels.tsv"):
            self.TableEvents = pandas.read_csv(
                              base_name + "_events.tsv",
                              sep="\t",
                              header=0,
                              index_col=["onset"],
                              na_values="n/a")
        else:
            self.TableEvents = self._load_events()
        if self.TableEvents is not None:
            # Checking columns validity
            if self.TableEvents.index.name != "onset":
                logger.warning("{}: Index column is not 'onset'"
                               .format(self.recIdentity()))
            for col_name in ("duration", "trial_type"):
                if col_name not in self.TableEvents.columns:
                    logger.warning("{}: Missing mandatory channel "
                                   "column '{}'"
                                   .format(self.recIdentity(), col_name))

    def load_electrodes(self, base_name: str) -> None:
        """
        Loads electrodes data into TableElectrodes dataframe.
        If _electrodes.tsv is found together with loaded file,
        then data is loaded from this file, else virtual function
        _load_electrodes is used to extract channels info from
        data files.

        Parameters
        ----------
        base_name: str
            file path without extention
        """
        if os.path.isfile(base_name + "_electrodes.tsv"):
            self.TableElectrodes = pandas.read_csv(
                              base_name + "_electrodes.tsv",
                              sep="\t",
                              header=0,
                              index_col=["name"],
                              na_values="n/a")
        else:
            self.TableElectrodes = self._load_electrodes()
        if self.TableElectrodes is not None:
            # Checking columns validity
            if self.TableElectrodes.index.name != "name":
                logger.warning("{}: Index column is not 'name'"
                               .format(self.recIdentity()))
            for col_name in ("x", "y", "z"):
                if col_name not in self.TableElectrodes:
                    logger.warning("{}: Missing mandatory channel "
                                   "column '{}'"
                                   .format(self.recIdentity(), col_name))

    def copyRawFile(self, destination: str) -> str:
        base = os.path.splitext(self.currentFile(True))[0]
        dest_base = os.path.join(destination, base)
        if self.TableChannels is not None:
            self.TableChannels.to_csv(dest_base + "_channels.tsv",
                                      sep="\t", na_rep="n/a",
                                      header=True, index=True,
                                      line_terminator="\n")
        if self.TableEvents is not None:
            self.TableEvents.to_csv(dest_base + "_events.tsv",
                                    sep="\t", na_rep="n/a",
                                    header=True, index=True,
                                    line_terminator="\n")
        if self.TableElectrodes is not None:
            self.TableElectrodes.to_csv(dest_base + "_electrodes.tsv",
                                        sep="\t", na_rep="n/a",
                                        header=True, index=True,
                                        line_terminator="\n")
        shutil.copy2(self.currentFile(), destination)
        return os.path.join(destination, self.currentFile(True))

    def _copy_bidsified(self, directory: str,
                        bidsname: str, ext: str) -> None:
        """
        Function that copies bidsified data files to
        its destinattion, with additional export of
        channels, events and coordinates.

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
        dest_base = os.path.join(directory, bidsname)

        shutil.copy2(self.currentFile(), dest_base + ext)

        dest_base = dest_base.rsplit("_", 1)[0]

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
                                      header=True, index=True,
                                      line_terminator="\n")
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
                                    header=True, index=True,
                                    line_terminator="\n")
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
                                        header=True, index=True,
                                        line_terminator="\n")
            self._elec_BIDS.DumpDefinitions(dest_base + "_events.json")

    @abstractmethod
    def _load_channels(self) -> pandas.DataFrame:
        """
        Virtual function that loads channel list from data file
        into Dataframe with passed list of columns

        Resulting DataFrame must have "name" as index, and contain
        columns "type" and "units"

        Returns
        -------
        DataFrame
        """
        raise NotImplementedError

    @abstractmethod
    def _load_electrodes(self) -> pandas.DataFrame:
        """
        Virtual function that loads electrodes list from data file
        into Dataframe with passed list of columns

        Resulting DataFrame must have "name" as index, and contain
        columns "x", "y" and "z"

        Returns
        -------
        DataFrame
        """
        raise NotImplementedError
