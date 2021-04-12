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
    __slots__ = ["df",             # dataframe
                 "index",          # name of index column
                 "_definitions",   # definitions of table columns
                 "_path",          # patho to folder of data table
                 "_name",          # name of the table
                 "_def_name",      # name of definitions file
                 "_dupl_name",     # name of duplicates file
                 ]

    def __init__(self, table:str,
                 index: str = "",
                 definitionsFile:str = "",
                 duplicatedFile:str = "",
                 checkDefinitions:bool = True):
        """
        Load tsv bids table into dataframe

        Parameters:
        -----------
        table: str
            path to tsv file, if not existing, an empty Dataframe
            will be created using given definitions
        index: str
            name of index column
        definitions: str
            path to json file with column definitions, if not given,
            the default one based on table path is used
        duplicatedFile: str
            name of file containing duplicates, if not given
            default __<name>.tsv is used.
            If such file is found an exception will be raised
        checkDefinitions: bool
            if True raises keyError if definitions mismatch table columns,
            if False adapt table columns to match definitions
        """

        self._path, self._name = os.path.split(table)
        self._def_name = change_ext(self._name, "json")

        if not duplicatedFile:
            self._dupl_name = "__" + self._name
        else:
            self._dupl_name = duplicatedFile

        if os.path.isfile(os.path.join(self._path, self._dupl_name)):
            logger.error("{}: Found unmerged file with duplicated values"
                         .format(self._name))
            raise FileExistsError(self._dupl_name)

        if not definitionsFile:
            definitionsFile = os.path.join(self._path, self._def_name)
            if not os.path.isfile(definitionsFile):
                logger.error("{}: Unable to find definitions file"
                             .format(self._name))
                raise FileNotFoundError(definitionsFile)

        with open(definitionsFile, "r") as f:
            self._definitions = json.load(f)

        # loading table
        self.df = None
        self.index = index
        if os.path.isfile(table):
            self.df = pandas.read_csv(table, sep="\t", header=0,
                                      na_values="n/a")

            if self.index:
                if self.index not in self.df.columns:
                    logger.error("{}: Index column {} not found in table"
                                 .format(self._name, self.index))
                    raise KeyError(self.index)

            # columns in table but not in definitions
            mismatch = [c for c in self.df.columns
                        if c not in self._definitions
                        and c != self.index]
            if mismatch:
                if checkDefinitions:
                    logger.error("{}: Extra columns {} in table"
                                 .format(self._name, mismatch))
                    raise KeyError(mismatch)
                else:
                    self.df.drop(mismatch, axis="columns", inplace=True)

            # columns in definition but not in table
            mismatch = [c for c in self._definitions
                        if c not in self.df.columns]
            if mismatch:
                if checkDefinitions:
                    logger.error("{}: Columns {} not found in table"
                                 .format(self._name, mismatch))
                    raise KeyError(mismatch)
                else:
                    for c in mismatch:
                        self.df[c] = None
        else:
            columns = self._definitions.keys()
            if index and index not in columns:
                columns = [index] + list(columns)
            self.df = pandas.DataFrame(columns=columns)

    def getTablePath(self) -> str:
        """
        Returns path to table file
        """
        return os.path.join(self._path, self._name)

    def getDefinitionsPath(self) -> str:
        """
        Returns path to definitions file
        """
        return os.path.join(self._path, self._def_name)

    def getDuplicatesPath(self):
        """
        Returns path to duplicated table file
        """
        return os.path.join(self._path, self._dupl_name)

    def getIndexes(self, selection=None, to_list=False):
        """
        Returns index column values
        If index is not defined, the dataframe index is used
        """
        if selection is None:
            df = self.df
        else:
            df = self.df[selection]

        if self.index:
            res = df[self.index]
        else:
            res = df.index.to_series()

        if to_list:
            res = res.to_list()
        return res

    def append(self, other: pandas.DataFrame,
               sort=True):
        """
        Append other dataframe to this one

        Both dataframes must have same columns
        """
        if not self.df.columns.equals(other.columns):
            logger.error("{}: Appending dataframes with mismatched columns {}"
                         .format(self._name,
                                 self.df.columns.difference(other.columns)))
            raise KeyError(self.df.columns.difference(other.columns))

        df_res = pandas.concat([self.df, other], join="inner",
                               keys=("original", "other"),
                               names=("stage", "ID"))
        if self.index and sort:
            df_res.sort_values(by=[self.index], inplace=True)
        self.df = df_res

    def drop_duplicates(self):
        """
        Removes duplicated values from table
        """

        self.df = self.df.drop_duplicates()

    def check_duplicates(self, columns=None, keep=False):
        """
        Returns indexes of duplicated values on given columns

        If columns is None, and index column is defined, 
        duplicated indexes are reported
        """

        if columns is None and self.index:
            dupl = self.df.duplicated(self.index, keep)
        else:
            dupl = self.df.duplicated(columns, keep)

        return dupl

    def save_table(self, append=False, selection=None,
                   useDuplicates=False):
        """
        Save current table to file
        """
        if useDuplicates:
            path = os.path.join(self._path, self._dupl_name)
        else:
            path = os.path.join(self._path, self._name)

        if selection is not None:
            to_save = self.df[selection]
        else:
            to_save = self.df

        if append:
            self.write_data(path, to_save, "a")
        else:
            self.write_data(path, to_save, "w")
            if not useDuplicates:
                with open(os.path.join(self._path, self._def_name), "w") as f:
                    json.dump(self._definitions, f, indent=2)

    @staticmethod
    def write_data(path:str, data=pandas.DataFrame, mode:str = "w") -> None:
        """
        Writes data dataframe to table at path following BIDS format:
        tab separated, null values as 'n/a', and with header

        If writing is in append mode 'a', header is not written

        Parameters:
        -----------
        path: str
            path to the file to be written
        data: pandas.DataFrame
            dataframe to be written
        mode: str
            Python write mode, default ‘w’. If 'a' (append)
            header will be not written
        """

        if mode == "a":
            header = False
        else:
            header = True

        data.to_csv(path, mode=mode,
                    sep="\t", na_rep="n/a",
                    index=False, header=header,
                    line_terminator="\n")
