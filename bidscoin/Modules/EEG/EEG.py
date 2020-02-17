import logging

from ..base import baseModule
from bidsMeta import BIDSfieldLibrary

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

        "EEGChannelCount", "ECGChannelCount", "EMGChannelCount",
        "EOGChannelCount",
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

    __slost__ = ["_chanValues", "_elecValues"]

    bidsmodalities = {
            "eeg": ("task", "acq", "run")
            }

    _chan_BIDS = BIDSfieldLibrary()
    _chan_BIDS.AddField(
            name="name",
            longName="Channel name",
            description="REQUIRED. Channel name (e.g., FC1, Cz)"
            )
    _chan_BIDS.AddField(
            name="type",
            longName="Type of channel",
            description="REQUIRED. Type of channel; "
            "MUST use the channel types listed below."
            )
    _chan_BIDS.AddField(
            name="units",
            longName="Physical unit of the data values",
            description="REQUIRED. Physical unit of the data values "
            "recorded by this channel in SI units."
            )
    _chan_BIDS.AddField(
            name="description",
            longName="Free-form text description of the channel",
            description="OPTIONAL. Free-form text description of the channel, "
            "or other information of interest.",
            activated=False
            )
    _chan_BIDS.AddField(
            name="sampling_frequency",
            longName="Sampling rate of the channel",
            description="OPTIONAL. Sampling rate of the channel in Hz.",
            units="Hz",
            activated=False
            )
    _chan_BIDS.AddField(
            name="reference",
            longName="Name of the reference electrode(s)",
            description="OPTIONAL. Name of the reference electrode(s).",
            activated=False
            )
    _chan_BIDS.AddField(
            name="low_cutoff",
            longName="Frequencies used for the high-pass filter",
            description="OPTIONAL. Frequencies used for the high-pass filter "
            "applied to the channel in Hz. If no high-pass filter applied, "
            "use n/a.",
            units="Hz",
            activated=False
            )
    _chan_BIDS.AddField(
            name="high_cutoff",
            longName="Frequencies used for the low-pass filter",
            description="OPTIONAL. Frequencies used for the low-pass filter "
            "applied to the channel in Hz. If no low-pass filter applied, "
            "use n/a. Note that hardware anti-aliasing in A/D conversion "
            "of all EEG electronics applies a low-pass filter; specify its "
            "frequency here if applicable.",
            units="Hz",
            activated=False
            )
    _chan_BIDS.AddField(
            name="notch",
            longName="Frequencies used for the notch filter",
            description="OPTIONAL. Frequencies used for the notch filter "
            "applied to the channel, in Hz. If no notch filter applied, "
            "use n/a.",
            units="Hz",
            activated=False
            )
    _chan_BIDS.AddField(
            name="status",
            longName="Data quality observed on the channel",
            description="OPTIONAL. Data quality observed on the channel "
            "(good/bad). A channel is considered bad if its data quality "
            "is compromised by excessive noise. Description of noise type "
            "SHOULD be provided in [status_description].",
            levels={"good": "acceptable noise level",
                    "bad": "excessive noise level"},
            activated=False
            )
    _chan_BIDS.AddField(
            name="status_description",
            longName="Free-form text description of noise or artifact",
            description="OPTIONAL. Free-form text description of noise or "
            "artifact affecting data quality on the channel. It is meant "
            "to explain why the channel was declared bad in [status].",
            activated=False
            )

    _elec_BIDS = BIDSfieldLibrary()

    def __init__(self):
        super().__init__()
        self.metaFields = {key: None for key in
                           eeg_meta
                           }
