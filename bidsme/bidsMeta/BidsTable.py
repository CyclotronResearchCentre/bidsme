###############################################################################
# BidsMeta.py defines class that provides interface to bids tsv tables
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

import os
import logging
import pandas
import json
from tools.tools import change_ext


logger = logging.getLogger(__name__)


class BidsTable(object):
    __slots__ = ["df", "duplicates",
                 "definitions",
                 "tablePath", "duplicatesPath"]

    def __init__(self, table:str,
                 definitionsFile:str = None,
                 duplicatedFile:str = None,
                 checkDefinitions:bool = True):
        """
        Load tsv bids table int dataframe

        Parameters:
        -----------
        table: str
            path to tsv file, if not existing, an empty Dataframe
            will be created using given definitions
        definitions: str or None
            path to json file with column definitions, if not given,
            the default one based on table path is used
        duplicatedFile: str or None
            name of file containing duplicates, if not given
            default __<name>.tsv is used.
            If such file is found an exception will be raised
        checkDefinitions: bool
            if True raises keyError if definitions mismatch table columns,
            if False adapt table columns to match definitions
        """

        pth, base = os.path.split(table)

        if definitionsFile is None:
            fname = change_ext(base, ".json")
            definitionsFile = os.path.join(pth, fname)

        if duplicatedFile is None:
            duplicatedFile = os.path.join(pth, "__" + fname)

        if os.path.isfile(duplicatedFile):
            logger.error("Found unmerged file with duplicated values")
            raise FileExistsError(duplicatedFile)
        self.duplicatesPath = duplicatedFile

        self.df = None
        self.tablePath = table
        if os.path.isfile(table):
            self.df = pandas.read_csv(table, sep="\t", header=0,
                                      na_values="n/a")
            with open(definitionsFile, "r") as f:
                self.definitions = json.read(f)
