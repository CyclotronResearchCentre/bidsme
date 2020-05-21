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

from datetime import datetime, time

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
            rec.acqTime()
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

        self.assertEqual(recording._getField(["RequestAttributesSequence",
                                              "0",
                                              "RequestedProcedureID"]),
                         "0000154779")
        self.assertEqual(recording._getField(["ImageType"]),
                         ["ORIGINAL", "PRIMARY", "M_FFE", "M", "FFE"])
        self.assertEqual(recording._getField(["ImageType", "3"]), "M")
        self.assertEqual(recording._getSubId(), "11788759296811")
        self.assertEqual(recording._getSesId(), "")
        self.assertIsNone(recording._adaptMetaField(""))

        self.assertIsNone(Modules.MRI.DICOM._DICOM__transform(None))
        self.assertEqual(
                Modules.MRI.DICOM._DICOM__decodeValue("12Y", "AS"), 12)
        self.assertEqual(
                Modules.MRI.DICOM._DICOM__decodeValue("12", "AS"), 12)
        self.assertEqual(
                Modules.MRI.DICOM._DICOM__decodeValue("121100.123", "TM"),
                time(12, 11, 0, 123000))
        self.assertEqual(Modules.MRI.DICOM._DICOM__decodeValue(
            "121100.123", "TM", True), "12:11:00.123000")
        self.assertIsNone(Modules.MRI.DICOM._DICOM__decodeValue("", "DT"))
        self.assertEqual(
                Modules.MRI.DICOM._DICOM__decodeValue("20070511113322", "DT"),
                datetime(2007, 5, 11, 11, 33, 22))
        self.assertEqual(
                Modules.MRI.DICOM._DICOM__decodeValue("20070511113322", "DT",
                                                      True),
                "2007-05-11T11:33:22")
        self.assertEqual(
                Modules.MRI.DICOM._DICOM__decodeValue("20070511113322.1",
                                                      "DT"),
                datetime(2007, 5, 11, 11, 33, 22, 100000))
        self.assertEqual(
                Modules.MRI.DICOM._DICOM__decodeValue("20070511113322+0100",
                                                      "DT"),
                datetime(2007, 5, 11, 12, 33, 22))
        self.assertEqual(
                Modules.MRI.DICOM._DICOM__decodeValue("20070511",
                                                      "DT"),
                datetime(2007, 5, 11, 0, 0, 0))
        self.assertEqual(
                Modules.MRI.DICOM._DICOM__decodeValue("070511",
                                                      "DT"),
                datetime(1900, 1, 1, 7, 5, 11))
        for VR in ("AT", "SQ", "UN",
                   "OB", "OD", "OF", "OL", "OV", "OW"):
            self.assertIsNone(
                    Modules.MRI.DICOM._DICOM__decodeValue("aaa", VR))
        with self.assertRaises(ValueError):
            Modules.MRI.DICOM._DICOM__decodeValue("aaa", "XX")

        recording.loadNextFile()
        self.assertEqual(recording.acqTime(),
                         datetime(2007, 5, 11, 11, 33, 22))
