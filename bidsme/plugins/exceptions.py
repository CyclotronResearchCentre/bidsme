###############################################################################
# exceptions.py defines exceptions used by plugins
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


from bidsme.exceptions import CoinException
"""
List of generic Plugin and individual plugin functions
exceptions
"""


class PluginError(CoinException):
    """
    Generic plugin error
    """
    base = 100
    code = 0


class PluginNotFoundError(PluginError):
    """
    Raises if plugin file not found
    """
    code = 1


class PluginModuleNotFoundError(PluginError):
    """
    Raises if no plugin modules found in plugin file
    """
    code = 2


class InitEPError(PluginError):
    """
    Raises if an error happens during the plugin initialisation
    """
    base = 100
    code = 0


class SubjectEPError(PluginError):
    """
    Raises if an error happens during the Subject adjustement
    """
    base = 110
    code = 0


class SessionEPError(PluginError):
    """
    Raises if an error happens during the Session adjustement
    """
    base = 120
    code = 0


class SequenceEPError(PluginError):
    """
    Raises if an error happens during the Sequence adjustement
    """
    base = 130
    code = 0


class RecordingEPError(PluginError):
    """
    Raises if an error happens during the Recording adjustement
    """
    base = 140
    code = 0


class FileEPError(PluginError):
    """
    Raises if an error happens during the post-copy file adjustement
    """
    base = 150
    code = 0


class SequenceEndEPError(PluginError):
    """
    Raises if an error happens during the post-sequence adjustement
    """
    base = 160
    code = 0


class SessionEndEPError(PluginError):
    """
    Raises if an error happens during the post-session adjustement
    """
    base = 170


class SubjectEndEPError(PluginError):
    """
    Raises if an error happens during the post-subject adjustement
    """
    base = 180


class FinaliseEPError(PluginError):
    """
    Raises if an error happens during the finalisation adjustement
    """
    base = 190
    code = 0
