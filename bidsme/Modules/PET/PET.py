###############################################################################
# PET.py provides the base class for PET recordings
# All PET classes should inherit from this class
###############################################################################
# Copyright (c) 2019-2020, University of Liège
# Author: Nikita Beliy
# Owner: Liege University https://www.uliege.be
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


import logging

from ..base import baseModule

from . import _PET

logger = logging.getLogger(__name__)


class PET(baseModule):
    _module = "PET"

    bidsmodalities = _PET.modalities

    def __init__(self):
        super().__init__()
        self.resetMetaFields()
        self.manufacturer = None

    def resetMetaFields(self) -> None:
        """
        Resets currently defined meta fields dictionaries
        to None values
        """
        self.metaFields_req["__common__"] = {
                key: None for key in
                _PET.required_common}
        for mod in _PET.required_modality:
            self.metaFields_req[mod] = {
                key: None for key in
                _PET.required_modality[mod]}
        self.metaFields_rec["__common__"] = {
                key: None for key in
                _PET.recommended_common}
        for mod in _PET.recommended_modality:
            self.metaFields_rec[mod] = {
                key: None for key in
                _PET.recommended_modality[mod]}
        self.metaFields_opt["__common__"] = {
                key: None for key in
                _PET.optional_common}
        for mod in _PET.optional_modality:
            self.metaFields_opt[mod] = {
                key: None for key in
                _PET.optional_modality[mod]}
