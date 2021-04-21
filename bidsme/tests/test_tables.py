###############################################################################
# test_tables.py defines unit tests for BidsMeta.Bidstable class
###############################################################################
# Copyright (c) 2019-2021, University of Liège
# Author: Nikita Beliy
# Owner: Liege University https://www.uliege.be
# Credits: [Nikita Beliy]
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
import unittest

import pandas

from bidsMeta import BidsTable


class TestBidstable(unittest.TestCase):
    def setUp(self):
        self.tablePath = os.path.join("tests", "output", "table.tsv")
        self.duplPath = os.path.join("tests", "output", "__table.tsv")
        self.defPath = os.path.join("tests", "output", "table.json")

    def testLoading(self):
        if os.path.isfile(self.duplPath):
            os.remove(self.duplPath)
        if os.path.isfile(self.defPath):
            os.remove(self.defPath)
        if os.path.isfile(self.tablePath):
            os.remove(self.tablePath)

        with self.assertRaises(FileNotFoundError):
            BidsTable(self.tablePath)

        with self.assertRaises(Exception):
            BidsTable(self.tablePath, definitionsFile=self.tablePath)

        BidsTable(self.tablePath,
                  index="index_col2",
                  definitionsFile=os.path.join(
                      "tests", "data",
                      "table_definitions.json"))

    def testStandartPaths(self):
        Table = BidsTable(self.tablePath,
                          index="index_col",
                          definitionsFile=os.path.join(
                              "tests", "data",
                              "table_definitions.json"))

        self.assertEqual(Table.getTablePath(),
                         os.path.join("tests", "output", "table.tsv"))
        self.assertEqual(Table.getDefinitionsPath(),
                         os.path.join("tests", "output", "table.json"))
        self.assertEqual(Table.getDuplicatesPath(),
                         os.path.join("tests", "output", "__table.tsv"))

    def testAppending(self):
        Table = BidsTable(self.tablePath,
                          index="index_col",
                          definitionsFile=os.path.join(
                              "tests", "data",
                              "table_definitions.json"))

        d = {"index_col": [1, 2, 3],
             "col_1": ["a", None, "c"]}
        df = pandas.DataFrame(d)
        with self.assertRaises(KeyError):
            Table.append(df)

        d = {"index_col": [1, 2, 3, 1],
             "col_1": ["a", None, "c", "a"],
             "col_2": ["a", None, "a", "a"],
             "col_3": ["a", None, "c", "a"],
             }
        df = pandas.DataFrame(d)
        Table.append(df)

        Table.save_table()
        self.assertTrue(os.path.isfile(Table.getTablePath()))
        self.assertTrue(os.path.isfile(Table.getDefinitionsPath()))

    def testDuplicates(self):
        Table = BidsTable(self.tablePath)

        dupl = Table.check_duplicates()
        self.assertTrue(dupl.any())

        Table.drop_duplicates()
        dupl = Table.check_duplicates()
        self.assertFalse(dupl.any())

        dupl = Table.check_duplicates(columns=["col_2"], keep="first")
        self.assertTrue(dupl.any())

        Table.save_table(selection=dupl, useDuplicates=True)
        self.assertTrue(os.path.isfile(Table.getDuplicatesPath()))

        with self.assertRaises(FileExistsError):
            BidsTable(self.tablePath)
        os.remove(Table.getDuplicatesPath())

    def testIndexesTable(self):
        t = BidsTable(self.tablePath, index="index_col",
                      duplicatedFile="__test.tsv")
        dupl = t.check_duplicates(keep="first")
        self.assertEqual(dupl.to_list(), [False, True, False, False])

        dupl = t.check_duplicates(columns=["col_2"], keep="first")
        print(t.df)

        with self.assertRaises(KeyError):
            BidsTable(self.tablePath, index="col__")

        self.assertEqual(t.getIndexes(to_list=True), [1, 1, 2, 3])
        t.drop_duplicates()
        self.assertEqual(t.getIndexes(to_list=True), [1, 2, 3])

        dupl = t.check_duplicates(columns=["col_2"], keep=False)
        self.assertEqual(t.getIndexes(to_list=True,
                                      selection=dupl),
                         [1, 3])

        t = BidsTable(self.tablePath)
        self.assertEqual(t.getIndexes(to_list=True),
                         [0, 1, 2, 3])

        t.save_table(append=True)

    def testDefinitions(self):
        with self.assertRaises(KeyError):
            Table = BidsTable(self.tablePath,
                              index="index_col",
                              definitionsFile=os.path.join(
                                  "tests", "data",
                                  "table_definitions_2.json"))

        with self.assertRaises(KeyError):
            Table = BidsTable(self.tablePath,
                              index="index_col",
                              definitionsFile=os.path.join(
                                  "tests", "data",
                                  "table_definitions_3.json"))

        Table = BidsTable(self.tablePath, index="index_col",
                          checkDefinitions=False,
                          definitionsFile=os.path.join(
                              "tests", "data",
                              "table_definitions_3.json"))
        self.assertEqual(Table.df.columns.to_list(),
                         ["index_col", "col_1",
                         "col_2", "col_3", "col_4"])

        Table = BidsTable(self.tablePath, index="index_col",
                          checkDefinitions=False,
                          definitionsFile=os.path.join(
                              "tests", "data",
                              "table_definitions_2.json"))
        self.assertEqual(Table.df.columns.to_list(),
                         ["index_col",
                         "col_2", "col_3"])


if __name__ == "__main__":
    unittest.main()
