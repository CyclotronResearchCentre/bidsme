###############################################################################
# test_nifti_common.py defines unit tests for _nifti_common.py functions
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

from Modules._nifti_common import isValidNIFTI
from Modules._nifti_common import getEndType
from Modules._nifti_common import parceNIFTIheader_1
# from Modules._nifti_common import parceNIFTIheader_2


class TestValidation(unittest.TestCase):
    def test(self):
        self.assertTrue(isValidNIFTI("tests/data/nifti1.nii"))
        self.assertTrue(isValidNIFTI("tests/data/nifti1.hdr"))
        self.assertFalse(isValidNIFTI("tests/data/nifti1.img"))
        self.assertFalse(isValidNIFTI("tests/data/testDICOM_01.dcm"))


class TestDataRetrieval(unittest.TestCase):
    def testType(self):
        end, tfile = getEndType("tests/data/nifti1.nii")
        self.assertEqual(end, ">")
        self.assertEqual(tfile, "n+1")

        end, tfile = getEndType("tests/data/nifti1.hdr")
        self.assertEqual(end, ">")
        self.assertEqual(tfile, "ni1")

        end, tfile = getEndType("tests/data/nifti1_le.nii")
        self.assertEqual(end, "<")
        self.assertEqual(tfile, "n+1")

    def testData_1(self):
        res = parceNIFTIheader_1("tests/data/nifti1.nii", ">")
        self.assertEqual(res["descrip"], "FSL3.2beta")
        self.assertEqual(res["cal_max"], 255.)
        self.assertEqual(res["cal_min"], 0.)
        self.assertEqual(res["dim"], (3, 91, 109, 91, 1, 1, 1, 1))

        res = parceNIFTIheader_1("tests/data/nifti1_le.nii", "<")
        self.assertEqual(res["descrip"], "TE=30;Time=160456.680")
        self.assertEqual(res["quatern_c"], -0.9933918714523315)
        self.assertEqual(res["scl_slope"], 4.007570266723633)
