import logging

from ..base import baseModule

logger = logging.getLogger(__name__)

eeg_meta = [
        # Generic fields 
        "TaskName",
        "TaskDescription",
        "Instructions",
        # Institution information
        "InstitutionName", "InstitutionAddress", "InstitutionalDepartmentName",
        # Scanner hardware
        "Manufacturer", "ManufacturersModelName",
        "DeviceSerialNumber",
        "CapManufacturer", "CapManufacturersModelName",
        "SoftwareVersions",
        "CogAtlasID", "CogPOID",

        "EEGReference",
        "SamplingFrequency",
        "PowerLineFrequency",
        "SoftwareFilters",

        "EEGChannelCount", "ECGChannelCount", "EMGChannelCount", "EOGChannelCount",
        "MiscChannelCount",
        "TriggerChannelCount",

        "RecordingDuration",
        "RecordingType",
        "EpochLength",
        "HeadCircumference",
        "EEGPlacementScheme",
        "EEGGround",
        "HardwareFilters",
        "SubjectArtefactDescription",
        ]


class EEG(baseModule):
    _module = "EEG"

    bidsmodalities = {
            "eeg": ("task", "acq", "run")
            }

    def __init__(self):
        super().__init__()
        self.metaFields = {key: None for key in
                           eeg_meta
                           }
