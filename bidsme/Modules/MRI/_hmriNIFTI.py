###############################################################################
# _hmriNIFTI.py provides additional parameters for hmriNIFTI class
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
            "Manufacturer": ("<Manufacturer>", None),
            "ManufacturersModelName": ("<ManufacturerModelName>", None),
            "DeviceSerialNumber": ("<DeviceSerialNumber>", None),
            "StationName": ("<StationName>", None),
            "SoftwareVersions": ("<SoftwareVersions>", None),
            "MagneticFieldStrength": ("<MagneticFieldStrength>", None),
            "ScanningSequence": ("<ScanningSequence>", None),
            "SequenceVariant": ("<SequenceVariant>", None),
            "ScanOptions": ("<ScanOptions>", ""),
            "EchoTime": ("<round10:scale-3:EchoTime>", None),
            "InversionTime": ("<round10:scale-3:InversionTime>", None),
            "FlipAngle": ("<FlipAngle>", None),
            "InstitutionName": ("<InstitutionName>", None),
            "InstitutionAddress": ("<InstitutionAddress>", None),
            "InstitutionalDepartmentName": ("<InstitutionalDepartmentName>",
                                            None),
            "RepetitionTime": ("<round10:scale-3:RepetitionTime>", None),
            "RepetitionTimeExitation": ("<round10:scale-3:RepetitionTime>", None),
            "TaskName": ("<<bids:task>>", None)
            },
        "Siemens": {
            "SequenceName": ("<SequenceName>", None),
            "PhaseEncodingDirection": ("<PhaseEncodingDirection>"
                                       "<PhaseEncodingSign>",
                                       None),
            }

        }

manufacturers = {
        "siemens": "Siemens",
        "philips": "Philips"
        }
