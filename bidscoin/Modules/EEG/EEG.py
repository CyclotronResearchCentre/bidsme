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

    bidsmodalities = {
            "eeg": ("task", "run")
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
    _elec_BIDS.AddField(
            name="name",
            longName="name of the electrode",
            description="REQUIRED. Name of the electrode")
    _elec_BIDS.AddField(
            name="x",
            longName="Recorded position along the x-axis",
            description="REQUIRED. Recorded position along the x-axis",
            units="mm")
    _elec_BIDS.AddField(
            name="y",
            longName="Recorded position along the y-ayis",
            description="REQUIRED. Recorded position along the y-ayis",
            units="mm")
    _elec_BIDS.AddField(
            name="z",
            longName="Recorded position along the z-azis",
            description="REQUIRED. Recorded position along the z-azis",
            units="mm")
    _elec_BIDS.AddField(
            name="type",
            longName="Type of the electrode",
            description="RECOMMENDED. Type of the electrode "
            "(e.g., cup, ring, clip-on, wire, needle)",
            activated=False
            )
    _elec_BIDS.AddField(
            name="material",
            longName="Material of the electrode",
            description="RECOMMENDED. Material of the electrode, "
            "e.g., Tin, Ag/AgCl, Gold",
            activated=False
            )
    _elec_BIDS.AddField(
            name="impedance",
            longName="Impedance of the electrode",
            description="RECOMMENDED. Impedance of the electrode in kOhm",
            units="kOhm",
            activated=False
            )

    _task_BIDS = BIDSfieldLibrary()
    _task_BIDS.AddField(
            name="onset",
            longName="Onset of the event",
            description="REQUIRED. Onset (in seconds) of the event measured "
            "from the beginning of the acquisition of the first volume "
            "in the corresponding task imaging data file. If any acquired "
            "scans have been discarded before forming the imaging data file, "
            "ensure that a time of 0 corresponds to the first image stored. "
            "In other words negative numbers in \"onset\" are allowed5.",
            units="seconds"
            )
    _task_BIDS.AddField(
            name="duration",
            longName="Duration of the event",
            description="REQUIRED. Duration of the event "
            "(measured from onset) in seconds. Must always be either "
            "zero or positive. A \"duration\" value of zero implies "
            "that the delta function or event is so short as to be "
            "effectively modeled as an impulse.",
            units="seconds"
            )
    _task_BIDS.AddField(
            name="sample",
            longName="Onset of the event according to the sampling scheme",
            description="OPTIONAL. Onset of the event according to the "
            "sampling scheme of the recorded modality (i.e., referring to "
            "the raw data file that the events.tsv file accompanies).",
            activated=False
            )
    _task_BIDS.AddField(
            name="trial_type",
            longName="Primary categorisation of each trial",
            description="OPTIONAL. Primary categorisation of each trial to "
            "identify them as instances of the experimental conditions. "
            "For example: for a response inhibition task, it could take "
            "on values \"go\" and \"no-go\" to refer to response initiation "
            "and response inhibition experimental conditions.",
            activated=False
            )
    _task_BIDS.AddField(
            name="response_time",
            longName="Response time measured in seconds",
            description="OPTIONAL. Response time measured in seconds. "
            "A negative response time can be used to represent preemptive "
            "responses and \"n/a\" denotes a missed response.",
            units="seconds",
            activated=False
            )
    _task_BIDS.AddField(
            name="stim_file",
            longName="Represents the location of the stimulus file",
            description="OPTIONAL. Represents the location of the stimulus "
            "file (image, video, sound etc.) presented at the given onset "
            "time. There are no restrictions on the file formats of the "
            "stimuli files, but they should be stored in the /stimuli "
            "folder (under the root folder of the dataset; with optional "
            "subfolders). The values under the stim_file column correspond "
            "to a path relative to \"/stimuli\". "
            "For example \"images/cat03.jpg\" will be translated to "
            "\"/stimuli/images/cat03.jpg\".",
            activated=False
            )
    _task_BIDS.AddField(
            name="value",
            longName="Marker value associated with the event",
            description="OPTIONAL. Marker value associated with the event "
            "(e.g., the value of a TTL trigger that was recorded at "
            "the onset of the event).",
            activated=False
            )
    _task_BIDS.AddField(
            name="HED",
            longName="Hierarchical Event Descriptor",
            description="OPTIONAL. Hierarchical Event Descriptor (HED) Tag. "
            "See Appendix III for details.",
            activated=False
            )

    def __init__(self):
        super().__init__()
        self.metaFields = {key: None for key in
                           eeg_meta
                           }
