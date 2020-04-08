###############################################################################
# MRI.py provides the base class for MRI recordings
# All MRI classes should inherit from this class
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


import os
import shutil
import logging
from tools import tools

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

    def _copy_bidsified(self, directory: str, bidsname: str, ext: str) -> None:
        """
        Copies bidsified data files to its destinattion.

        Additionally, if modality is dwi (diffusion MRI),
        look for file of same name and extentions bvec and
        bval, and copies it. Will show a warning if such files
        not found.

        Parameters
        ----------
        directory: str
            destination directory where files should be copies,
            including modality folder. Assured to exists.
        bidsname: str
            bidsified name without extention
        ext: str
            extention of the data file
        """
        bids_base = os.path.join(directory, bidsname)
        shutil.copy2(self.currentFile(),
                     bids_base + ext)

        if self.Modality() == "dwi":
            bvec = tools.change_ext(self.currentFile(), "bvec")
            if os.path.isfile(bvec):
                shutil.copy2(bvec,
                             bids_base + ".bvec")
            else:
                logger.warning("{} missing bvec file for diffusion recording"
                               .format(self.recIdentity()))
            bval = tools.change_ext(self.currentFile(), "bval")
            if os.path.isfile(bval):
                shutil.copy2(bval,
                             bids_base + ".bval")
            else:
                logger.warning("{} missing bval file for diffusion recording"
                               .format(self.recIdentity()))
