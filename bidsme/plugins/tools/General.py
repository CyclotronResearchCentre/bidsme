###############################################################################
# General.py contains general tools, that can be used in user plugins
# general tools do not require additional modules installation
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
import logging

logger = logging.getLogger(__name__)


def CheckSeries(path: str,
                expected_series: list,
                strict: bool=True,
                complete: bool=True,
                order: bool=True,
                level: int=logging.ERROR) -> bool:
    """
    Tool for checking the series in the prepared dataset
    to be conformed with passed list. It may be used
    in preparation step in SessionEndEP, or in process/bidsify
    steps in SessioEP.

    Function returns true if all series in given path are in given list.

    Parameters:
    -----------
    path: str
        path to the folder to check, including the data type sub-folder,
        expected to exist
    expected_series: list
        list of expected series Ids (without series number) in expected order
    strict: bool
        if true, check will fail if several series in folder corresponds
        to same series in list
    complete: bool
        if true, fails if not all series in given list found in path
    order: bool
        if true, fails if series in given path are out of order given
        in list, order=True implies strict=True
    level: int
        defines in what logging cathegory error messages will be
        reported (set to logging.NOTSET to silence)

    Example:
    --------
    # In SessionEndEP, given
    #   preparefolder is the path to prepared dataset
    #   session is the BidsSession object passed to SessionEndEP
    #   series is a dictionary with session name as key, and list
    #       of series as values
    path = os.path.join(preparefolder, session.getPath(True), "MRI")
    if not dry_run:
        if not CheckSeries(path, series[session.session]):
            logger.error("{}:{} Series do not match expectation."
            .format(session.subject, session.session))
    """

    if order:
        strict = True

    passed = True
    series = sorted(os.listdir(path))
    series = [s.split("-", 1)[1] for s in series]
    matches = dict.fromkeys(series, -1)

    logger.debug("Found series: {}".format(series))
    logger.debug("Matching against: {}".format(expected_series))

    for ind, s in enumerate(series):
        print(matches)
        offset = matches[s] + 1
        if s not in expected_series[offset:]:
            logger.log(level, "Invalid serie [{}] {}".format(ind, s))
            passed = False
            continue

        expected_index = expected_series.index(s, offset)
        if strict:
            matches[s] = expected_index

        if order:
            if ind != expected_index:
                logger.log(level,
                           "Serie [{}] {}, expected at {}"
                           .format(ind, s, expected_index))
                passed = False
                continue

    if complete:
        matches = dict.fromkeys(expected_series, -1)
        for ind, s in enumerate(expected_series):
            if s not in series[matches[s] + 1:]:
                logger.log(level, "Expected series [{}] {} not found"
                           .format(ind, s))
                passed = False
                continue
            matches[s] = series.index(s)

    return passed
