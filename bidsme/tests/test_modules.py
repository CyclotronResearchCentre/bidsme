###############################################################################
# test_modules.py defines unit tests for Modules classes
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

from datetime import datetime

import Modules


class TestModules(unittest.TestCase):
    def testSelection(self):
        self.assertEqual(Modules.select("tests/data"),
                         Modules.MRI.DICOM)
        self.assertEqual(Modules.select("tests/data", "MRI"),
                         Modules.MRI.DICOM)
        self.assertIsNone(Modules.select("tests/data", "EEG"),
                          Modules.MRI.DICOM)

        self.assertEqual(Modules.selectFile("tests/data/testDICOM_01.dcm"),
                         Modules.MRI.DICOM)
        self.assertEqual(Modules.selectFile("tests/data/testDICOM_01.dcm",
                                            "MRI"),
                         Modules.MRI.DICOM)
        self.assertIsNone(Modules.selectFile("tests/data/testDICOM_01.dcm",
                          "EEG"))
        self.assertIsNone(Modules.selectFile("tests/data/testDICOM_03.dcm"))
        with self.assertRaises(KeyError):
            Modules.selectFile("tests/data/testDICOM_01.dcm",
                               "NonExisting")

        self.assertEqual(Modules.selectByName("DICOM"), Modules.MRI.DICOM)
        self.assertEqual(Modules.selectByName("DICOM", "MRI"),
                         Modules.MRI.DICOM)
        self.assertIsNone(Modules.selectByName("DICOM", "EEG"))

    def testVirtual(self):
        rec = Modules.base.baseModule()
        with self.assertRaises(NotImplementedError):
            rec._isValidFile("aaa")
        with self.assertRaises(NotImplementedError):
            rec._loadFile("aaa")
        with self.assertRaises(NotImplementedError):
            rec._getAcqTime()
        with self.assertRaises(NotImplementedError):
            rec.dump()
        with self.assertRaises(NotImplementedError):
            rec._getField("aaa")
        with self.assertRaises(NotImplementedError):
            rec.recNo()
        with self.assertRaises(NotImplementedError):
            rec.recId()
        with self.assertRaises(NotImplementedError):
            rec.isCompleteRecording()
        with self.assertRaises(NotImplementedError):
            rec._getSubId()
        with self.assertRaises(NotImplementedError):
            rec._getSesId()

    def testDICOM(self):
        self.assertFalse(Modules.MRI.DICOM._isValidFile("tests/data/"))
        self.assertTrue(
                Modules.MRI.DICOM._isValidFile("tests/data/testDICOM_01.dcm")
                )
        self.assertFalse(
                Modules.MRI.DICOM._isValidFile("tests/data/testDICOM_03.dcm")
                )

        recording = Modules.MRI.DICOM("tests/data/")
        self.assertEqual(recording.Type(), "DICOM")

        self.assertEqual(recording.acqTime(), datetime(2007, 5, 11,
                                                       11, 33, 22))
        self.assertEqual(recording._getSubId(), "11788759296811")
        self.assertEqual(recording._getSesId(), "")

        self.assertIsNone(recording._adaptMetaField("test"))

        recording.dump()
        recording.clearCache()
        recording.dump()
        tmp = recording.files
        recording.files = []
        recording.clearCache()
        self.assertEqual(recording.dump(), "No defined files")
        recording.files = tmp
        recording.loadFile(0)

        self.assertEqual(recording.recNo(), 601)
        self.assertEqual(recording.recId(), "unknown")
        self.assertTrue(recording.isCompleteRecording())

        recording.copyRawFile("tests/out")
        recording.copyRawFile("tests/out")

        recording._modality = "dwi"
        recording._copy_bidsified("tests/data/", "bidsified", "dcm")
