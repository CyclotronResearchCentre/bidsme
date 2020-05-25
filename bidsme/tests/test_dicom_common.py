###############################################################################
# test_dicom_common.py defines unit tests for common.py functions
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
import pydicom
from datetime import datetime, time, date

from Modules._dicom_common import isValidDICOM
from Modules._dicom_common import retrieveFromDataset
from Modules._dicom_common import getTag
from Modules._dicom_common import DICOMtransform
from Modules._dicom_common import decodeValue
from Modules._dicom_common import extractStruct
from Modules._dicom_common import combineDateTime


class TestValidation(unittest.TestCase):
    def test(self):
        self.assertTrue(isValidDICOM("tests/data/testDICOM_01.dcm"))
        self.assertTrue(isValidDICOM("tests/data/testDICOM_01.dcm", "MR"))
        self.assertFalse(isValidDICOM("tests/data/testDICOM_01.dcm", "PT"))

        self.assertFalse(isValidDICOM(__file__))


class TestDataRetrieval(unittest.TestCase):
    def testTag(self):
        self.assertEqual(getTag("(0008, 0030)"), (0x8, 0x30))
        self.assertIsNone(getTag("abc def"))

    def testTransform(self):
        for VR in ("FL", "FD", "SL", "SS", "SV", "UL", "US", "UV"):
            self.assertEqual(decodeValue(123, VR), 123)
        self.assertEqual(decodeValue("123.4", "DS"), 123.4)
        self.assertEqual(decodeValue("123", "IS"), 123)

        for VR in ("AE", "CS", "LO", "LT", "SH", "ST", "UC", "UR", "UT", "UI"):
            self.assertEqual(decodeValue("  abc \0 ", VR), "abc")

        self.assertEqual(decodeValue("Test", "PN"), "Test")
        self.assertEqual(decodeValue("123Y", "AS"), 123)
        self.assertEqual(decodeValue("123", "AS"), 123)

        self.assertIsNone(decodeValue("", "TM"))
        self.assertEqual(decodeValue("122345", "TM"), time(12, 23, 45))
        self.assertEqual(decodeValue("122345.123", "TM"),
                         time(12, 23, 45, 123000))
        self.assertEqual(decodeValue("122345", "TM", True),
                         "12:23:45")

        self.assertIsNone(decodeValue("", "DA"))
        self.assertEqual(decodeValue("19920324", "DA"), date(1992, 3, 24))
        self.assertEqual(decodeValue("19920324", "DA", True),
                         "1992-03-24")

        self.assertIsNone(decodeValue("", "DT"))
        self.assertEqual(decodeValue("19920324122345", "DT"),
                         datetime(1992, 3, 24, 12, 23, 45))
        self.assertEqual(decodeValue("19920324122345.123", "DT"),
                         datetime(1992, 3, 24, 12, 23, 45, 123000))
        self.assertEqual(decodeValue("19920324122345+0100", "DT"),
                         datetime(1992, 3, 24, 13, 23, 45))
        self.assertEqual(decodeValue("19920324122345", "DT", True),
                         "1992-03-24T12:23:45")
        self.assertEqual(decodeValue("19920324+0100", "DT"),
                         datetime(1992, 3, 24, 1))
        self.assertEqual(decodeValue("122345", "DT"),
                         datetime(1900, 1, 1, 12, 23, 45))

        for VR in ("AT", "SQ", "UN"):
            self.assertIsNone(decodeValue(0, VR))

        for VR in ("OB", "OD", "OF", "OL", "OV", "OW"):
            self.assertIsNone(decodeValue(0, VR))

        with self.assertRaises(ValueError):
            decodeValue(0, "XX")

        self.assertIsNone(DICOMtransform(None))

    def testRetrieve(self):
        ds = pydicom.dcmread("tests/data/testDICOM_01.dcm")

        self.assertEqual(retrieveFromDataset(["Modality"], ds), "MR")
        self.assertEqual(retrieveFromDataset(["(0008, 0060)"], ds), "MR")
        self.assertEqual(retrieveFromDataset(["ImageType"], ds),
                         ['ORIGINAL', 'PRIMARY', 'M_FFE', 'M', 'FFE'])
        self.assertEqual(retrieveFromDataset(["ImageType", "3"], ds), "M")
        self.assertEqual(retrieveFromDataset(["(0008, 1111)",
                                              "0",
                                              "(0008, 0005)"], ds),
                         "ISO_IR 100")

        self.assertIsNone(retrieveFromDataset(["ABC"],
                                              ds,
                                              fail_on_not_found=False))
        self.assertIsNone(retrieveFromDataset(["ABC"],
                                              ds,
                                              fail_on_not_found=True,
                                              fail_on_last_not_found=False))
        with self.assertRaises(KeyError):
            retrieveFromDataset(["ABC"], ds)
        with self.assertRaises(KeyError):
            retrieveFromDataset(["(0008, 1111)", "0", "ABC"], ds,
                                fail_on_not_found=True)
        self.assertIsNone(retrieveFromDataset(["ImageType", "9"],
                                              ds,
                                              fail_on_not_found=False))
        self.assertIsNone(retrieveFromDataset(["ImageType", "9"],
                                              ds,
                                              fail_on_not_found=True,
                                              fail_on_last_not_found=False))
        with self.assertRaises(KeyError):
            retrieveFromDataset(["ImageType", "9"], ds)

        exp = extractStruct(ds)
        self.assertEqual(exp["ImageType"],
                         ['ORIGINAL', 'PRIMARY', 'M_FFE', 'M', 'FFE'])

        self.assertEqual(combineDateTime(ds, "Study"),
                         datetime(2001, 1, 1, 11, 33, 22))
        self.assertIsNone(combineDateTime(ds, "Acquisition"))
        ds.add(pydicom.DataElement("AcquisitionDateTime",
                                   "DT",
                                   "19920304112233"))
        self.assertEqual(combineDateTime(ds, "Acquisition"),
                         datetime(1992, 3, 4, 11, 22, 33))

        del ds["StudyTime"]
        self.assertIsNone(combineDateTime(ds, "Study"))
