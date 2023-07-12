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
        "pet": ("task", "trc", "rec", "run"),
        "ct": ("acq", "ce", "rec", "run"),
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
        "Manufacturer", "ManufacturersModelName",
        ]

recommended_common = [
        # Info
        "InstitutionName", "InstitutionAddress",
        "InstitutionalDepartmentName",
        "BodyPart",
        ]

optional_common = []

required_modality = {
        "pet": [
            # Infosection
            "Units",
            # Radiochemistry
            "TracerName", "TracerRadionuclide",
            "InjectedRadioactivity", "InjectedRadioactivityUnits",
            "InjectedMass", "InjectedMassUnits",
            "SpecificRadioactivity", "SpecificRadioactivityUnits",
            "ModeOfAdministration",
            # Time zero
            "TimeZero", "ScanStart", "InjectionStart", "FrameTimesStart",
            "FrameDuration"
            # Reconstruction
            "AcquisitionMode", "ImageDecayCorrected",
            "ImageDecayCorrectionTime",
            "ReconMethodName", "ReconMethodParameterLabels",
            "ReconMethodParameterUnits", "ReconMethodParameterValues",
            "ReconFilterType", "ReconFilterSize",
            "AttenuationCorrection",
            ],
        "ct": [
            "CTDIvol", "CTDIvolUnit",
            "DLP", "DLPUnit",
            "ScanLength", "ScanLengthUnit",
            "SSDE", "SSDEUnit",
            "TubeVoltage", "TubeCurrent", "SliceWidth",
            "Pitch", "ContrastBolusIngredient",
            "DiameterFOV", "ReconMatrixSize",
            "MethodName", "MethodParameterLabels", "MethodParameterUnits",
            "MethodParameterValues", "MethodImplementationVersion",
            "FilterType",
            ]
        }

recommended_modality = {
        "pet": [
            # Radiochemistry
            "TracerRadLex", "TracerSNOMED", "TracerMolecularWeight",
            "TracerMolecularWeightUnits",
            "InjectedMassPerWeight", "InjectedMassPerWeightUnits",
            "SpecificRadioactivityMeasTime",
            "MolarActivity", "MolarActivityUnits",
            "MolarActivityMeasTime",
            "InfusionRadioactivity",
            "InfusionStart", "InfusionSpeed", "InfusionSpeedUnits",
            "InjectedVolume", "Purity",
            # Pharmaceuticals
            "PharmaceuticalName", "PharmaceuticalDoseAmount",
            "PharmaceuticalDoseUnits", "PharmaceuticalDoseRegimen",
            "PharmaceuticalDoseTime",
            # Time
            "ScanDate", "InjectionEnd",
            # Reconstruction
            "ReconMethodImplementationVersion",
            "AttenuationCorrectionMethodReference",
            "ScaleFactor", "ScatterFraction", "DecayCorrectionFactor",
            "PromptRate", "RandomRate", "SinglesRate",
            ],
        "ct": [
            "DeviceSerialNumber", "StationName", "SoftwareVersions",
            ]
        }

optional_modality = {
        "pet": ["Anaesthesia"]
        }
