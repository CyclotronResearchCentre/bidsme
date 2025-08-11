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
            "ManufacturersModelName": "<ManufacturerModelName>",
            "EchoTime": "<round10:scale-3:EchoTime>",
            "InversionTime": "<round10:scale-3:InversionTime>",
            "RepetitionTime": "<round10:scale-3:RepetitionTime>",
            "RepetitionTimeExcitation": "<round10:scale-3:RepetitionTime>",
            },
        "Siemens": {
            "PhaseEncodingDirection": ("<PhaseEncodingDirection>"
                                       "<PhaseEncodingSign>"),
            "EchoTime1": ("<round10:scale-6:CSASeriesHeaderInfo/"
                          "MrPhoenixProtocol/alTE/0>"),
            "EchoTime2": ("<round10:scale-6:CSASeriesHeaderInfo/"
                          "MrPhoenixProtocol/alTE/1>"),
            "ReceiveCoilActiveElements": "<CSASeriesHeaderInfo/CoilString>",
            "DwellTime": "<scale-6:CSAImageHeaderInfo/RealDwellTime>",
            "PulseSequenceDetails": ("<CSASeriesHeaderInfo/MrPhoenixProtocol/"
                                     "tSequenceFileName>"),
            "ReceiveCoilName": ("<CSASeriesHeaderInfo/MrPhoenixProtocol/"
                                "sCoilSelectMeas/aRxCoilSelectData/0/"
                                "asList/0/sCoilElementID/tCoilID>")
            }
        }

manufacturers = {
        "siemens": "Siemens",
        "philips": "Philips"
        }
