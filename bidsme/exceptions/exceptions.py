###############################################################################
# exceptions.py defines generic exceptions used by BIDSme
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
import traceback
import logging

logger = logging.getLogger(__name__)


class CoinException(Exception):
    """
    Base class for other exceptions
    code will serve as return code of programm
    """
    base = 0
    code = 1


def ReportError(err: Exception) -> int:
    if isinstance(err, CoinException):
        code = err.base + err.code
    else:
        code = 1
    exc_type, exc_value, exc_traceback = os.sys.exc_info()
    tr = traceback.extract_tb(exc_traceback)
    for line in tr:
        logger.error("{}({}) in {}: "
                     .format(line[0], line[1], line[2]))
    logger.error("{}:{}: {}".format(code, exc_type.__name__, exc_value))

    return code
