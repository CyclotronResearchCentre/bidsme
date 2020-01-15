import logging

from ..base import baseModule

logger = logging.getLogger(__name__)

mri_meta_recommended = [
        # Scanner hardware
        "Manufacturer", "ManufacturersModelName", "DeviceSerialNumber",
        "StationName", "SoftwareVersions",
        "MagneticFieldStrength", "ReceiveCoilName",
        "ReceiveCoilActiveElements",
        "GradientSetType", "MRTransmitCoilSequence",
        "MatrixCoilMode", "CoilCombinationMethod",
        # Sequence Specifics
        "PulseSequenceType", "ScanningSequence", "SequenceVariant",
        "ScanOptions", "SequenceName", "PulseSequenceDetails",
        "NonlinearGradientCorrection",
        # In-Plane Spatial Encoding
        "NumberShots", "ParallelReductionFactorInPlane",
        "ParallelAcquisitionTechnique", "PartialFourier",
        "PartialFourierDirection", "PhaseEncodingDirection",
        "EffectiveEchoSpacing", "TotalReadoutTime",
        # Timing Parameters
        "EchoTime", "InversionTime", "SliceTiming",
        "SliceEncodingDirection", "DwellTime",
        # RF & Contrast
        "FlipAngle", "MultibandAccelerationFactor",
        # Slice Acceleration
        "MultibandAccelerationFactor",
        # Anatomical landmarks
        "AnatomicalLandmarkCoordinates",
        # Institution information
        "InstitutionName", "InstitutionAddress", "InstitutionalDepartmentName",
        ]


class MRI(baseModule):
    _module = "MRI"

    bidsmodalities = {
            "anat": ("acq", "ce", "rec", "mod", "run"),
            "func": ("task", "acq", "ce", "dir", "rec", "run", "echo"),
            "dwi": ("acq", "dir", "run"),
            "fmap": ("acq", "ce", "dir", "run"),
            "beh": ("task")
            }

    def __init__(self):
        super().__init__()
        self.metaFields = {key: None for key in
                           mri_meta_recommended
                           }
