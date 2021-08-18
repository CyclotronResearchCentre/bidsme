###############################################################################
# _MRI.py contains the BIDS-defined MRI  modalities and met fields
###############################################################################
# Copyright (c) 2019-2020, University of Liège
# Author: Nikita Beliy
# Owner: Liege University https://www.uliege.be
# Credits: [Nikita Beliy]
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

"""
modalities dictionary contains a name of modality
(as defined as bids modality folder) as key, and
tuple of entities names for corresponding modslity
as value
"""
modalities = {
        "anat": ("acq", "ce", "rec", "run", "mod"),
        "func": ("task", "acq", "ce", "dir", "rec", "run", "echo"),
        "dwi": ("acq", "dir", "run"),
        "fmap": ("acq", "ce", "dir", "run"),
        # MPM modalities
        "mpm_anat": ("acq", "ce", "rec", "run", "echo", "flip", "mt", "part"),
        "mpm_RB1COR": ("acq", "ce", "dir", "run"),
        "mpm_TB1EPI": ("echo", "flip", "acq", "ce", "dir", "run"),
        # MP2RAGE modalities
        "mp2rage_anat": ("inv", "acq", "ce", "rec", "run", "mod"),
        "mp2rage_TB1TFL": ("acq", "ce", "dir", "run")
        }


"""
following lists contains the names of bids metafields
for sidcar json.

    required designated mandatory fields
    recommended disignates recommended fields
    optional designates optional fields

    common designates fields used for all modalities
"""
required_common = []
recommended_common = [
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
        "MRAcquisitionType",
        "MTState", "MTOffsetFrequency", "MTPulseBandwidth",
        "MTNumberOfPulses", "MTPulseShape", "MTPulseDuration",
        "SpoilingState", "SpoilingType", "SpoilingRFPhaseIncrement",
        "SpoilingGradientMoment", "SpoilingGradientDuration",
        # In-Plane Spatial Encoding
        "NumberShots", "ParallelReductionFactorInPlane",
        "ParallelAcquisitionTechnique", "PartialFourier",
        "PartialFourierDirection", "PhaseEncodingDirection",
        "EffectiveEchoSpacing", "TotalReadoutTime",
        # Timing Parameters
        "EchoTime", "InversionTime", "SliceTiming",
        "RepetitionTimeExcitation",
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
optional_common = []

required_modality = {
        "func": ["RepetitionTime", "TaskName"],
        "fmap": ["IntendedFor"],
        # MPM modalities
        "mpm_anat": ["MTState"],
        "mpm_RB1COR": ["RepetitionTimeExcitation", "IntendedFor"],
        "mpm_TB1EPI": ["MixingTime", "RepetitionTimeExcitation",
                       "IntendedFor"],
        # MP2RAGE modalities
        "mp2rage_TB1TFL": ["IntendedFor"]
        }

recommended_modality = {
        "func": ["NumberOfVolumesDiscardedByScanner",
                 "NumberOfVolumesDiscardedByUser",
                 "DelayTime",
                 "AcquisitionDuration",
                 "DelayAfterTrigger",
                 "Instructions",
                 "TaskDescription",
                 "CogAtlasID",
                 "CogPOID"],
        "fmap": ["EchoTime1", "EchoTime2", "Units",
                 ]
        }

optional_modality = {
        "anat": ["ContrastBolusIngredient"],
        }
