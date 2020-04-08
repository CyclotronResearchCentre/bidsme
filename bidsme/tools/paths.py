###############################################################################
# paths.py contains a set of functions and definitions for standard
# file location and search for files in these locations
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
import sys
import logging

from tools import appdirs


logger = logging.getLogger(__name__)

user = os.getlogin()
app = os.path.splitext(os.path.basename(sys.argv[0]))[0]

local = os.getcwd()
installation = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "../.."))

heuristics = os.path.join(installation, "heuristics")

config = appdirs.user_data_dir(app, user)


def findFile(fname, *kargs):
    path = ""
    found = False
    if os.path.isabs(fname):
        if os.path.isfile(fname):
            logger.debug("File {} found".format(fname))
            return fname
        else:
            logger.debug("File {} not found".format(fname))
            return ""
    for p in kargs:
        path = os.path.join(p, fname)
        if os.path.isfile(path):
            logger.debug("File {} found in {}".format(fname, p))
            found = True
            break
        logger.debug("File {} not found in {}".format(fname, p))
    if found:
        return path
    else:
        return ""
