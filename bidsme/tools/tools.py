###############################################################################
# tools.py contains a set of various convinience functions
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
import re
import glob
import logging

import pandas
import json

logger = logging.getLogger(__name__)


def lsdirs(folder: str, wildcard: str = '*'):
    """
    Gets all directories in a folder, ignores files

    :param folder:      The full pathname of the folder
    :param wildcard:    Simple (glob.glob) shell-style wildcards.
                        Foldernames starting with a dot are special cases that
                        are not matched by '*' and '?' patterns.") wildcard
    :return:            Iterable filter object with all directories in a folder
    """

    if wildcard:
        folder = os.path.join(folder, wildcard)
    return [fname for fname in sorted(glob.glob(folder))
            if os.path.isdir(fname)]


def cleanup_value(label, prefix=""):
    """
    Converts a given label to a cleaned-up label
    that can be used as a BIDS label.
    Remove leading and trailing spaces;
    removes all non ASCII alphanumeric characters,
    for example "Joe's reward_task" changes to "Joesrewardtask"

    If prefix is specified, it will be added to final result.
    If prefix is present in initial field, it is removed, for ex:
    "task-Joe's reward_task" changes to "task-Joesrewardtask"
    if prefix is "task-"

    :param label:   The given label
    :param prefix:  Specified prefix
    :return:        The cleaned-up / BIDS-valid labe
    """

    if label is None:
        return label
    label = label.strip()
    if prefix and label.startswith(prefix):
        label = label[len(prefix):]
    if label == "":
        return label
    return prefix + re.sub(r'[^a-zA-Z0-9]', '', label, re.ASCII)


def match_value(val, regexp, force_str=False):
    if force_str:
        val = str(val).strip()
        regexp = regexp.strip()
        return re.fullmatch(regexp, val) is not None

    if isinstance(regexp, str):
        val = str(val).strip()
        regexp = regexp.strip()
        return re.fullmatch(regexp, val) is not None
    return val == regexp


def change_ext(filename, new_ext):
    base, ext = os.path.splitext(filename)
    if ext == ".gz":
        base, ext = os.path.splitext(base)
    return base + "." + new_ext


def check_type(name: str, cls: type, val: object) -> object:
    """
    Checks if passed value is of type.

    Parameters:
    -----------
    name: str
        name of variable
    cls: type
        type to test
    val: object
        object to test

    Returns:
    --------
    object
        Succesfully tested object

    Raises:
    -------
    TypeError:
        if test is unsuccesful
    """
    if isinstance(val, cls):
        return val
    else:
        raise TypeError("{}: {} expected, {} recieved"
                        .format(name, cls, type(val)))


def checkTsvDefinitions(df: pandas.DataFrame, definitions: str) -> bool:
    """
    Checks if sidecar json file with tsv fields definitions
    contains same columns as dataframe

    Parameters
    ----------
    df: pandas.DataFrame
        dataframe to check
    definitions: str
        path to json sidecar file

    Returns
    -------
    bool
        True if columns in sidecar describe columns in dataframe
    """
    base = os.path.basename(definitions)
    base = os.path.splitext(base)[0]
    with open(definitions, "r") as f:
        df_definitions = json.load(f)
    if len(df_definitions) != len(df.columns):
        logger.error("{}.tsv contains {} columns, while "
                     "sidecar contain {} definitions"
                     .format(base,
                             len(df.columns),
                             len(df_definitions)))
        return False
    for col in df.columns:
        if col not in df_definitions:
            logger.error("{}.tsv contains undefined "
                         "column '{}'"
                         .format(base, col))
            return False
    return True


def skipEntity(entity: str,
               ent_list: list = [],
               ent_serie: pandas.Series = None,
               ent_path: str = "") -> bool:
    """
    Checks if given entity (i.e. sub Id or ses Id)
    are found in given list, serie or folder and so
    should be skipped

    Parameters
    ----------
    entity: str
        name of entity to check, including prefix,
        e.g. sub-001, empty ("" or None) are always
        skipped
    ent_list: list
        list of authorised names
    ent_serie: pandas.Series
        serie of blacklisted names
    ent_path: str
        path to the directorie containing sub-directories
        of blacklisted names
    """
    if not entity:
        return True
    if ent_list:
        if entity not in ent_list:
            logger.debug("{} not in list".format(entity))
            return True
    if ent_serie is not None:
        if entity in ent_serie.values:
            logger.debug("{} in tsv".format(entity))
            return True
    if ent_path:
        if os.path.isdir(os.path.join(ent_path, entity)):
            logger.debug("{} dir exists".format(entity))
            return True
    return False
