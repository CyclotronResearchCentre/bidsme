###############################################################################
# entry_points.py defines the list of accepted names of plug-in functions and
# associated exceptions
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


from . import exceptions

entry_points = {
        "InitEP": exceptions.InitEPError,
        "SubjectEP": exceptions.SubjectEPError,
        "SessionEP": exceptions.SessionEPError,
        "SequenceEP": exceptions.SequenceEPError,
        "RecordingEP": exceptions.RecordingEPError,
        "FileEP": exceptions.FileEPError,
        "SequenceEndEP": exceptions.SequenceEndEPError,
        "SessionEndEP": exceptions.SessionEndEPError,
        "SubjectEndEP": exceptions.SubjectEndEPError,
        "FinaliseEP": exceptions.FinaliseEPError
        }
