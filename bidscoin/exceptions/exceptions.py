#############################################################################
# exceptions defines standard exception classes expected to occure during
# eegBidsCreator execution
#############################################################################
# Copyright (c) 2018-2019, University of Liège
# Author: Nikita Beliy
# Owner: Liege University https://www.uliege.be
# Version: 0.77
# Maintainer: Nikita Beliy
# Email: Nikita.Beliy@uliege.be
# Status: developpement
#############################################################################
# This file is part of eegBidsCreator
# eegBidsCreator is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# eegBidsCreator is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with eegBidsCreator.  If not, see <https://www.gnu.org/licenses/>.
############################################################################


class CoinException(Exception):
    """
    Base class for other exceptions
    code will serve as return code of programm
    """
    base = 0
    code = 1
