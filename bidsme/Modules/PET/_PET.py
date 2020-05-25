###############################################################################
# _PET.py contains the BIDS-defined PET  modalities and met fields
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
        "pet": ("task", "acq", "rec", "run"),
        }


"""
following lists contains the names of bids metafields
for sidcar json.

    required designated mandatory fields
    recommended disignates recommended fields
    optional designates optional fields

    common designates fields used for all modalities
"""
required_common = [
        # Info section
        "Modality", "Manufacturer", "ManufacturersModelName",
        "Unit", "TracerName", "TracerRadionuclide",
        # Radiochem
        "InjectedRadioactivity", "InjectedRadioactivityUnit",
        "InjectedMass", "InjectedMassUnit", "SpecificRadioactivity",
        "SpecificRadioactivityUnit", "ModeOfAdministration",
        # Time
        "ScanStart", "InjectionStart", "TimeZero",
        "FrameTimesStart", "FrameTimesStartUnit",
        "FrameDuration", "FrameDurationUnit",
        # Recon
        "AcquisitionMode", "ImageDecayCorrected",
        "ImageDecayCorrectionTime", "ReconMatrixSize",
        "ImageVoxelSize", "ReconMethodName",
        "ReconMethodParameterLabels",
        "ReconMethodParameterUnit", "ReconMethodParameterValues",
        "ReconFilterType", "ReconFilterSize", "AttenuationCorrection",
        # Blood
        "PlasmaAvail", "MetaboliteAvail", "MetaboliteMethod",
        "MetaboliteRecoveryCorrectionApplied",
        "ContinuousBloodAvail", "ContinuousBloodDispersionCorrected",
        "BloodDiscreteAvail",
        ]
recommended_common = [
        # Info
        "BodyPart", "TracerRadLex", "TracerSNOMED",
        "TracerMolecularWeight", "TracerMolecularWeightUnit",
        "PharmaceuticalDoseUnit", "PharmaceuticalDoseRegimen",
        "PharmaceuticalDoseTime", "PharmaceuticalDoseTimeUnit",
        # Radiochem
        "InjectedMassPerWeightUnit", "SpecificRadioactivityMeasTime",
        "MolarActivity", "MolarActivityUnit", "MolarActivityMeasTime",
        "InfusionSpeed", "InfusionSpeedUnit", "InjectedVolume",
        "InjectedVolumeUnit", "Purity", "PurityUnit",
        # Time
        "ScanDate", "InjectionEnd",
        # Recon
        "DiameterFOV", "DiameterFOVUnit", "ImageOrientation",
        "ReconMethodImplementationVersion",
        "AttenuationCorrectionMethodReference",
        "ScaleFactor", "ScatterFraction", "DecayCorrectionFactor",
        "PromptRate", "RandomRate", "SinglesRate",
        # Blood
        "PlasmaFreeFraction", "PlasmaFreeFractionMethod",
        "ContinuousBloodWithdrawalRateUnit",
        "ContinuousBloodTubingType", "ContinuousBloodTubingLength",
        "ContinuousBloodTubingLengthUnits",
        "BloodDiscreteHaematocrit", "BloodDiscreteDensity",
        "BloodDiscreteDensityUnit",
        ]
optional_common = [
        # Info
        "Anaesthesia",
        "PharmaceuticalName",
        "PharmaceuticalDoseAmount",
        # Blood
        "ContinuousBloodDispersionConstant",
        "ContinuousBloodDispersionConstantUnits",
        ]

required_modality = {}

recommended_modality = {}

optional_modality = {}
