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

from ..base import baseModule
from bidsMeta import BIDSfieldLibrary
from tools import paths

logger = logging.getLogger(__name__)


eeg_meta_required_common = [
        "TaskName",
        "PowerLineFrequency",
        ]
eeg_meta_recommended_common = [
        "InstitutionName", "InstitutionAddress",
        "Manufacturer", "ManufacturersModelName",
        "SoftwareVersions",
        "TaskDescription",
        "Instructions",
        "CogAtlasID", "CogPOID",
        "DeviceSerialNumber",
        ]
eeg_meta_optional_common = []

eeg_meta_required_modality = {
        "eeg": ["EEGReference", "SamplingFrequency",
                "SoftwareFilters"],
        "meg": ["SamplingFrequency",
                "DewarPosition", "SoftwareFilters",
                "DigitizedLandmarks", "DigitizedHeadPoints"],
        "ieeg": ["iEEGReference", "SamplingFrequency",
                 "SoftwareFilters"]
        }

eeg_meta_recommended_modality = {
        "eeg": ["CapManufacturer", "CapManufacturersModelName",
                "EEGChannelCount", "ECGChannelCount",
                "EMGChannelCount", "EOGChannelCount",
                "MiscChannelCount", "TriggerChannelCount",
                "RecordingDuration", "RecordingType",
                "EpochLength", "HeadCircumference",
                "EEGPlacementScheme", "EEGGround",
                "HardwareFilters", "SubjectArtefactDescription"],
        "meg": ["MEGChannelCount", "MEGREFChannelCount",
                "EEGChannelCount", "ECOGChannelCount",
                "SEEGChannelCount", "EOGChannelCount",
                "ECGChannelCount", "EMGChannelCount",
                "MiscChannelCount", "TriggerChannelCount",
                "RecordingDuration", "RecordingType",
                "EpochLength", "ContinuousHeadLocalization",
                "HeadCoilFrequency", "MaxMovement",
                "SubjectArtefactDescription",
                "AssociatedEmptyRoom",
                "HardwareFilters"],
        "ieeg": ["DCOffsetCorrection", "HardwareFilters",
                 "ElectrodeManufacturer", "ElectrodeManufacturersModelName",
                 "ECOGChannelCount", "SEEGChannelCount",
                 "EEGChannelCount", "EOGChannelCount",
                 "ECGChannelCount", "EMGChannelCount",
                 "MiscChannelCount", "TriggerChannelCount",
                 "RecordingDuration", "RecordingType",
                 "EpochLength", "iEEGGround",
                 "iEEGPlacementScheme", "iEEGElectrodeGroups",
                 "SubjectArtefactDescription"]
        }

eeg_meta_optional_modality = {
        "meg": ["EEGPlacementScheme", "ManufacturersAmplifierModelName",
                "CapManufacturer", "CapManufacturersModelName",
                "EEGReference"],
        "ieeg": ["ElectricalStimulation", "ElectricalStimulationParameters"]
    }


class EEG(baseModule):
    _module = "EEG"

    bidsmodalities = {
            "eeg": ("task", "acq", "run"),
            "meg": ("task", "acq", "run", "proc"),
            "ieeg": ("task", "acq", "run")
            }

    _chan_BIDS = BIDSfieldLibrary()
    _chan_BIDS.LoadDefinitions(os.path.join(paths.installation,
                                            "bidsme",
                                            "Modules", "EEG",
                                            "_channels.json"))
    _elec_BIDS = BIDSfieldLibrary()
    _elec_BIDS.LoadDefinitions(os.path.join(paths.installation,
                                            "bidsme",
                                            "Modules", "EEG",
                                            "_electrodes.json"))
    _task_BIDS = BIDSfieldLibrary()
    _task_BIDS.LoadDefinitions(os.path.join(paths.installation,
                                            "bidsme",
                                            "Modules", "EEG",
                                            "_events.json"))

    __slots__ = ["TableChannels", "TableElectrodes", "TableEvents"]


    def __init__(self):
        super().__init__()
        self.resetMetaFields()
        self.manufacturer = None

        self.TableChannels = None
        self.TableElectrodes = None
        self.TableEvents = None

    def resetMetaFields(self) -> None:
        """
        Resets currently defined meta fields dictionaries
        to None values
        """
        self.metaFields_req["__common__"] = {key: None for key in
                                             eeg_meta_required_common}
        for mod in eeg_meta_required_modality:
            self.metaFields_req[mod] = {key: None for key in
                                        eeg_meta_required_modality[mod]}
        self.metaFields_rec["__common__"] = {key: None for key in
                                             eeg_meta_recommended_common}
        for mod in eeg_meta_recommended_modality:
            self.metaFields_rec[mod] = {key: None for key in
                                        eeg_meta_recommended_modality[mod]}
        self.metaFields_opt["__common__"] = {key: None for key in
                                             eeg_meta_optional_common}
        for mod in eeg_meta_optional_modality:
            self.metaFields_opt[mod] = {key: None for key in
                                        eeg_meta_optional_modality[mod]}


    
