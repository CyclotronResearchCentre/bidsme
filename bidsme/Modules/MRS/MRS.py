###############################################################################
# MRS.py provides the base class for Magnetic Resonance Spectroscopy recordings
# All MRS classes should inherit from this class
###############################################################################
# Copyright (c) 2019-2024, University of Liège
# Author: Nikita Beliy
# Owner: Liege University https://www.uliege.be
# Credits: [Nikita Beliy]
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

logger = logging.getLogger(__name__)


class MRS(baseModule):
    _module = "MRS"
    _schema_mod = "mrs"
    _schema_data_types = ["mrs", "task"]

    def __init__(self):
        super().__init__()
