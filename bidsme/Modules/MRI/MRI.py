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

from . import _MRI

logger = logging.getLogger(__name__)


class MRI(baseModule):
    _module = "MRI"

    bidsmodalities = _MRI.modalities

    def __init__(self):
        super().__init__()
        self.resetMetaFields()

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

    def resetMetaFields(self) -> None:
        """
        Resets currently defined meta fields dictionaries
        to None values
        """
        self.metaFields_req["__common__"] = {
                key: None for key in
                _MRI.required_common}
        for mod in _MRI.required_modality:
            self.metaFields_req[mod] = {
                key: None for key in
                _MRI.required_modality[mod]}
        self.metaFields_rec["__common__"] = {
                key: None for key in
                _MRI.recommended_common}
        for mod in _MRI.recommended_modality:
            self.metaFields_rec[mod] = {
                key: None for key in
                _MRI.recommended_modality[mod]}
        self.metaFields_opt["__common__"] = {
                key: None for key in
                _MRI.optional_common}
        for mod in _MRI.optional_modality:
            self.metaFields_opt[mod] = {
                key: None for key in
                _MRI.optional_modality[mod]}
