###############################################################################
# dummy.py provide the dummy class used for emulate virtual class and abstarct
# functions for baseModule class if needed module is not in system
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

import logging
import datetime

from ..base import baseModule

logger = logging.getLogger(__name__)


class dummy(baseModule):

    classes = {}

    def __init__(self):
        """
        dummy class used for replacement of subclasses of baseModule
        in case if needed module not installed.

        class dictionary must be filled by file format: dependancy
        for all missing modules

        It will alwais throw an ModuleNotFoundError
        """
        logger.critical("Trying to initialise dummy class. "
                        "May indicate missing dependances")
        raise ModuleNotFoundError(str(self.classes))

    @classmethod
    def _isValidFile(cls, file: str) -> bool:
        """
        Simulation of _isValidFile function from baseModule
        Always returns False
        """
        return False

    def _loadFile(cls, file: str) -> bool:
        raise NotImplementedError

    def _getAcqTime(self) -> datetime:
        raise NotImplementedError

    def dump(self) -> dict:
        raise NotImplementedError

    def _getField(self):
        raise NotImplementedError

    def recNo(self):
        raise NotImplementedError

    def recId(self):
        raise NotImplementedError

    def isCompleteRecording(self) -> bool:
        raise NotImplementedError

    def _getSubId(self) -> str:
        raise NotImplementedError

    def _getSesId(self) -> str:
        raise NotImplementedError
