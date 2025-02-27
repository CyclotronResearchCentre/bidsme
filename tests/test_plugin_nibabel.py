import unittest
import os
import logging
import shutil
import nibabel
import json

import numpy as np

from bidsme.Modules.MRI import NIFTI

from bidsme.plugins.tools import Nibabel as plNibabel

data_path = os.path.dirname(__file__)


class TestConvert3Dto4D(unittest.TestCase):
    log_info = "bidsme.plugins.tools.Nibabel"
    num_files = 10
    data_path = os.path.join(data_path, "data", "plugins", "nibabel_concat")

    @classmethod
    def tearDownClass(cls):
        if os.path.isdir(cls.data_path):
            shutil.rmtree(cls.data_path)

    def setUp(self):
        if os.path.isdir(self.data_path):
            shutil.rmtree(self.data_path)
        os.mkdir(self.data_path)

        # Creating test data
        for i in range(1, self.num_files + 1):
            data = np.diag([i] * 3).astype('int8')
            aff = np.diag([1 + i % 2] * 4)
            img = nibabel.Nifti1Image(data, aff)
            img.header.set_slope_inter(1 + i % 2, 0)
            img_path = os.path.join(self.data_path,
                                    "data_{:02d}.nii".format(i))
            nibabel.save(img, img_path)
            img_path = os.path.join(self.data_path,
                                    "data_{:02d}.json".format(i))
            slope, inter = img.header.get_slope_inter()
            meta = {"index": i, "data": float(data[0, 0]) * slope + inter,
                    "slope": img.header.get_slope_inter(),
                    "dtype": img.get_data_dtype().name}
            with open(img_path, "w") as f:
                json.dump(meta, f)

    @staticmethod
    def get_index(fname):
        index = fname.rsplit("_", 1)[1]
        index = int(index.split(".", 1)[0])
        return index

    def test_select_files(self):
        f_list = plNibabel._select_files_scandir(self.data_path)
        self.assertEqual(len(f_list), self.num_files)
        for i, f in enumerate(f_list):
            self.assertEqual(i + 1, self.get_index(f))

        rec = NIFTI(self.data_path)
        # reversing to ensure that there's no sorting in selection
        rec.files.reverse()
        # Adding fake file to ensure no non-existing files will be selected
        rec.files.append("test_11.nii")
        f_list = plNibabel._select_files_list(self.data_path, rec.files)
        self.assertEqual(len(f_list), self.num_files)
        for i, f in enumerate(f_list):
            self.assertEqual(self.num_files - i, self.get_index(f))

    def test_concat(self):
        # testing skipping too much files
        with self.assertLogs(level=logging.WARN) as cm:
            res = plNibabel.Convert3Dto4D(self.data_path, None,
                                          skip=self.num_files)
        self.assertEqual(cm.output,
                         ["WARNING:{}:No files to concat"
                          .format(self.log_info)
                          ])
        self.assertEqual(res, "")

        res = plNibabel.Convert3Dto4D(self.data_path, None, keep=1)
        self.assertEqual(res, os.path.join(self.data_path, "data_01.nii"))

        # No slope recalculation, taking only pair elements
        rec = NIFTI(self.data_path)
        files = rec.files[0::2]
        res = plNibabel.Convert3Dto4D(self.data_path, files,
                                      check_affines=True)
        self.assertEqual(res, os.path.join(self.data_path, "data_01.nii"))

        for i in range(1, self.num_files + 1):
            img_path = os.path.join(self.data_path,
                                    "data_{:02d}.nii".format(i))
            js_path = os.path.join(self.data_path,
                                   "data_{:02d}.json".format(i))

            if img_path == res:
                with open(js_path) as f:
                    js = json.load(f)
                img = nibabel.load(img_path)

                # Checking scaling
                self.assertEqual(img.dataobj.slope, js["slope"][0])
                self.assertEqual(img.dataobj.inter, js["slope"][1])
                # Checking dimentions
                data = img.get_fdata()
                self.assertEqual(data.shape, (3, 3, self.num_files // 2))
                # Checking data
                self.assertEqual(data[0, 0, 0], js["data"])
                self.assertEqual(img.get_data_dtype(), js["dtype"])
                continue

            # Not merged files
            if i % 2 == 0:
                self.assertTrue(os.path.isfile(img_path))
                self.assertTrue(os.path.isfile(js_path))
            # Merged files
            else:
                self.assertFalse(os.path.isfile(img_path))
                self.assertFalse(os.path.isfile(js_path))

    def test_concat_rescale(self):
        # Slope recalculation, taking all files
        keep = 5
        rec = NIFTI(self.data_path)
        with self.assertLogs(level=logging.WARN) as cm:
            res = plNibabel.Convert3Dto4D(self.data_path, rec,
                                          check_affines=False, keep=keep)
        self.assertEqual(cm.output,
                         ["WARNING:{}:"
                          "Concatenation of images of different scale "
                          "or dtypes. Will recalculate scale for all files."
                          .format(self.log_info)
                          ])
        self.assertEqual(res, os.path.join(self.data_path, "data_01.nii"))

        for i in range(1, self.num_files + 1):
            img_path = os.path.join(self.data_path,
                                    "data_{:02d}.nii".format(i))
            js_path = os.path.join(self.data_path,
                                   "data_{:02d}.json".format(i))

            if img_path == res:
                with open(js_path) as f:
                    js = json.load(f)
                img = nibabel.load(img_path)

                # Checking scaling, must be recalculated!
                self.assertNotEqual(img.dataobj.slope, js["slope"][0])
                self.assertNotEqual(img.dataobj.inter, js["slope"][1])
                # Checking dimentions
                data = img.get_fdata()
                self.assertEqual(data.shape, (3, 3, keep))
                # Checking data, must be approximately equal
                self.assertAlmostEqual(data[0, 0, 0], js["data"], places=1)
                self.assertEqual(img.get_data_dtype(), js["dtype"])
                continue

            # Merged files
            elif i <= keep:
                self.assertFalse(os.path.isfile(img_path))
                self.assertFalse(os.path.isfile(js_path))
            else:
                self.assertTrue(os.path.isfile(img_path))
                self.assertTrue(os.path.isfile(js_path))
