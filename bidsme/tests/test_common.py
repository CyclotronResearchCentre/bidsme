###############################################################################
# test_common.py defines unit tests for common.py functions
###############################################################################
# Copyright (c) 2019-2020, University of Liège
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

import unittest
from Modules import exceptions

from Modules.common import action_value
from Modules.common import retrieveFormDict


class TestActionValue(unittest.TestCase):
    def testEmpty(self):
        self.assertEqual(action_value("2", ""), "2")
        self.assertEqual(action_value(2, ""), 2)

    def testInt(self):
        self.assertEqual(action_value("2", "int"), 2)
        self.assertEqual(action_value("2", "int"), 2)
        self.assertEqual(action_value(2, "int"), 2)
        self.assertEqual(action_value(2.5, "int"), 2)
        with self.assertRaises(TypeError):
            action_value(None, "int")
        with self.assertRaises(ValueError):
            action_value("2.5", "int")

    def testFloat(self):
        self.assertEqual(action_value("2", "float"), 2)
        self.assertEqual(action_value("2.5", "float"), 2.5)
        self.assertEqual(action_value(2, "float"), 2)
        self.assertEqual(action_value(2.5, "float"), 2.5)
        with self.assertRaises(TypeError):
            action_value(None, "float")
        with self.assertRaises(ValueError):
            action_value("a2.5", "float")

    def testString(self):
        self.assertEqual(action_value("abc", "str"), "abc")
        self.assertEqual(action_value(2, "str"), "2")
        self.assertEqual(action_value(None, "str"), "None")

    def testFormat(self):
        self.assertEqual(action_value("abc", "format"), "abc")
        self.assertEqual(action_value("abc", "format >8"), "     abc")
        self.assertEqual(action_value(3, "format >8"), "       3")
        self.assertEqual(action_value(3.555, "format >.0f"), "4")

    def testScale(self):
        self.assertEqual(action_value(3, "scale2"), 300)
        self.assertEqual(action_value(3, "scale-2"), 0.03)
        with self.assertRaises(TypeError):
            action_value("3", "scale2")
        with self.assertRaises(ValueError):
            action_value(3, "scale-2.5")
        with self.assertRaises(ValueError):
            action_value(3, "scale")

    def testMult(self):
        self.assertEqual(action_value(3, "mult2"), 6)
        self.assertEqual(action_value(3, "mult-2.5"), -7.5)
        with self.assertRaises(ValueError):
            action_value(3, "mult")
        with self.assertRaises(TypeError):
            action_value("3", "mult2")

    def testDiv(self):
        self.assertEqual(action_value(6, "div2"), 3)
        self.assertEqual(action_value(-7.5, "div-2.5"), 3)
        with self.assertRaises(ValueError):
            action_value(3, "div")
        with self.assertRaises(TypeError):
            action_value("3", "div2")

    def testRound(self):
        self.assertEqual(action_value(6, "round2"), 6)
        self.assertEqual(action_value(-7.5, "round2"), -7.5)
        self.assertEqual(action_value(7.1234, "round2"), 7.12)
        self.assertEqual(action_value(7.1234, "round"), 7)
        self.assertTrue(isinstance(action_value(7.1234, "round"), int))
        self.assertTrue(isinstance(action_value(7.1234, "round0"), float))
        with self.assertRaises(TypeError):
            action_value("3", "round2")

    def testInvalid(self):
        self.assertRaises(exceptions.InvalidActionError,
                          action_value, 0, "abcde")


class TestRetrieveFromDict(unittest.TestCase):

    d = {"a": "val1",
         "b": ["list1", "list2"],
         "d": {"d1": "vald1",
               "d2": ["listd11", "listd12"]},
         "e": [{"e1": "vale1",
                "e2": ["vale21", "vale22", "vale23"],
                }]
         }

    def testRetrievalSuccess(self):
        self.assertEqual(retrieveFormDict(["a"], self.d), "val1")
        self.assertEqual(retrieveFormDict(["b", 0], self.d), "list1")
        self.assertEqual(retrieveFormDict(["d", "d1"], self.d), "vald1")
        self.assertEqual(retrieveFormDict(["d", "d2", 0], self.d), "listd11")
        self.assertEqual(retrieveFormDict(["e", 0, "e2", 2], self.d), "vale23")

    def testRetrievalFail(self):
        self.assertIsNone(retrieveFormDict(["e", 0, "e2", 8], self.d,
                                           fail_on_last_not_found=False))
        self.assertIsNone(retrieveFormDict(["f"], self.d,
                                           fail_on_last_not_found=False))
        with self.assertRaisesRegex(KeyError, ": key error 0"):
            retrieveFormDict([0, 0], self.d)
        self.assertIsNone(retrieveFormDict([0, 0], self.d,
                          fail_on_not_found=False))
        with self.assertRaisesRegex(KeyError, ": key error 10"):
            retrieveFormDict(["e", 10], self.d)
        self.assertIsNone(retrieveFormDict(["e", 10], self.d,
                          fail_on_not_found=False))


if __name__ == '__main__':
    unittest.main()
