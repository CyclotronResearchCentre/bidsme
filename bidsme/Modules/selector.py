###############################################################################
# selector.py provides the function for identify recordings and select
# the recording class accordingly
###############################################################################
# Copyright (c) 2019-2020, University of Liège
# Author: Nikita Beliy
# Owner: Liege University https://www.uliege.be
# Credits: [Marcel Zwiers]
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

from collections import OrderedDict

from . import MRI, EEG, PET

types_list = OrderedDict(
             {"MRI": (MRI.hmriNIFTI, MRI.bidsmeNIFTI,
                      MRI.jsonNIFTI, MRI.NIFTI,
                      MRI.DICOM),
              "PET": (PET.DICOM, PET.ECAT,
                      PET.bidsmeNIFTI,
                      PET.NIFTI),
              "EEG": (EEG.BrainVision,)}
             )


def select(folder: str, module: str = ""):
    """
    Returns first class for wich given folder is correct

    Parameters
    ----------
    folder: str
        folder to scan
    module: str
        restrict type of class
    """
    if module == "":
        for m in types_list:
            for cls in types_list[m]:
                if cls.isValidRecording(folder):
                    return cls
    else:
        for cls in types_list[module]:
            if cls.isValidRecording(folder):
                return cls
    return None


def selectFile(file: str, module: str = ""):
    """
    Returns first class for wich given file is correct

    Parameters
    ----------
    folder: str
        file to scan
    module: str
        restrict type of class
    """
    if module == "":
        for m in types_list:
            for cls in types_list[m]:
                if cls.isValidFile(file):
                    return cls
    else:
        for cls in types_list[module]:
            if cls.isValidFile(file):
                return cls
    return None


def selectByName(name: str, module: str = ""):
    """
    Returns first class with given name

    Parameters
    ----------
    name: str
        name of class
    module: str
        restrict type of class
    """
    if module == "":
        for m in types_list:
            for cls in types_list[m]:
                if cls.Type() == name:
                    return cls
    else:
        for cls in types_list[module]:
            if cls.Type() == name:
                return cls
    return None
