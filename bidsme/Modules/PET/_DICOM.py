###############################################################################
# _DICOM.py provides additional parameters for DICOM class
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

metafields = {
        "Unknown": {
            "Units": ("<Units>", None),
            "TracerName": ("<RadiopharmaceuticalInformationSequence/0/"
                           "Radiopharmaceutical>", None),
            "TracerRadionuclide": ("<RadiopharmaceuticalInformationSequence/0/"
                                   "RadionuclideCodeSequence/0/"
                                   "CodeMeaning>", None),
            "ModeOfAdministration": ("<RadiopharmaceuticalInformationSequence/"
                                     "0/RadiopharmaceuticalRoute>", None),
            "Modality": ("<Modality>", None),
            "SliceWidth": ("<SliceThickness>", None),
            "CTDIvol": ("<CTDIvol>", None),
            "TubeCurrent": ("<XRayTubeCurrent>", None),
            "DiameterFOV": ("<DataCollectionDiameter>", None),
            "ReconMatrixSize": (["<Rows>", "<Columns>"], None),
            "FilterType": ("<FilterType>", None),
            "Manufacturer": ("<Manufacturer>", None),
            "ManufacturersModelName": ("<ManufacturerModelName>", None),
            "StationName": ("<StationName>", None),
            "DeviceSerialNumber": ("<DeviceSerialNumber>", None),
            "SoftwareVersions": ("<SoftwareVersions>", None),
            "InstitutionName": ("<InstitutionName>", None),
            "InstitutionAddress": ("<InstitutionAddress>", None),
            "InstitutionalDepartmentName":
                ("<InstitutionalDepartmentName>", None)
            }
        }

manufacturers = {
        "siemens": "Siemens",
        "philips": "Philips"
        }
