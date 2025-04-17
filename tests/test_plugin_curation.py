import unittest
import os
import logging
import shutil
import glob

from bidsme.plugins.tools import General
from bidsme.bidsMeta import BidsSession

data_path = os.path.dirname(__file__)
data_path = os.path.join(data_path, "data", "plugins", "curation")


class TestCuration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        BidsSession.loadSubjectFields(
                os.path.join(data_path, "participants.json"))

    def setUp(self):
        sub_dirs = glob.glob(os.path.join(data_path, "sub-*"))
        for sub_dir in sub_dirs:
            shutil.rmtree(sub_dir)

    def gen_paths(self, path, session, acqs):
        path = os.path.join(path, session.getPath(True), "MRI")
        for i, acq in enumerate(acqs):
            pth = os.path.join(path, "{:03d}-{}".format(i, acq))
            os.makedirs(pth, exist_ok=True)

    def test_load_list(self):
        res = General.LoadCurationList(data_path, "black_list",
                                       modalities=False)
        self.assertEqual(res, {"sub-ABC001": ["ses-"]})

        res = General.LoadCurationList(data_path, "white_list",
                                       modalities=True)
        self.assertIn("MRI", res)
        self.assertIn("default", res["MRI"])
        self.assertIn("sub-ABC001", res["MRI"])

    def test_check(self):
        log_info = "INFO:bidsme.plugins.tools.General"
        w_list = General.LoadCurationList(data_path, "white_list")

        # Matching acquisitions
        acqs = ["acq001", "acq002", "acq003", "acq004", "acq005"]
        session = BidsSession("sub-ABC001", "ses-01")
        self.gen_paths(data_path, session, acqs)

        with self.assertLogs(level=logging.INFO) as cm:
            self.assertTrue(General.CheckPrepared(data_path, w_list, session))
        self.assertEqual(cm.output,
                         ["{}:{}/{}/MRI: Comparing acquisitions "
                          "with white list".format(log_info,
                                                   session.subject,
                                                   session.session)
                          ]
                         )
        shutil.rmtree(os.path.join(data_path, session.subject))

        acqs = ["acq001", "acq002", "acq003", "acq004", "acq005"]
        session = BidsSession("sub-ABC002", "ses-01")
        self.gen_paths(data_path, session, acqs)
        with self.assertLogs(level=logging.ERROR):
            self.assertFalse(General.CheckPrepared(data_path, w_list, session))
        shutil.rmtree(os.path.join(data_path, session.subject))

        # Matching first default
        acqs = ["acq001", "acq002", "acq003", "acq004"]
        session = BidsSession("sub-ABC004", "ses-01")
        self.gen_paths(data_path, session, acqs)

        with self.assertLogs(level=logging.INFO) as cm:
            self.assertTrue(General.CheckPrepared(data_path, w_list, session,
                                                  ["defaultX", "default"]))
        self.assertEqual(cm.output,
                         ["{}:{}/{}/MRI: Comparing acquisitions "
                          "with default list".format(log_info,
                                                     session.subject,
                                                     session.session),
                          "{}:{}/{}/MRI: Matched default list".format(
                                                              log_info,
                                                              session.subject,
                                                              session.session)
                          ]
                         )
        shutil.rmtree(os.path.join(data_path, session.subject))

        acqs = ["acq001", "acq002", "acq003", "acq004", "acq005"]
        session = BidsSession("sub-ABC004", "ses-01")
        self.gen_paths(data_path, session, acqs)

        with self.assertLogs(level=logging.ERROR):
            self.assertFalse(General.CheckPrepared(data_path, w_list, session,
                                                   ["defaultX", "default"]))
        shutil.rmtree(os.path.join(data_path, session.subject))
        self.assertTrue(General.CheckPrepared(data_path, w_list, session, []))

        # Testing subject and session passed directly
        self.gen_paths(data_path, session, acqs)
        with self.assertLogs(level=logging.ERROR):
            self.assertFalse(General.CheckPrepared(data_path, w_list, None,
                                                   ["defaultX", "default"],
                                                   session.subject,
                                                   session.session))
        shutil.rmtree(os.path.join(data_path, session.subject))
        self.assertTrue(General.CheckPrepared(data_path, w_list, None, [],
                                              session.subject,
                                              session.session))

        # Testing no subject/session
        self.gen_paths(data_path, session, acqs)
        with self.assertLogs(level=logging.ERROR):
            self.assertFalse(General.CheckPrepared(data_path, w_list, None,
                                                   ["defaultX", "default"]))

        shutil.rmtree(os.path.join(data_path, session.subject))
        self.assertTrue(General.CheckPrepared(data_path, w_list, None, []))

    def test_cleanup(self):
        log_info = "INFO:bidsme.plugins.tools.General"
        w_list = General.LoadCurationList(data_path, "white_list")
        r_list = General.LoadCurationList(data_path, "to_remove")

        acqs = ["acq001", "acq002", "extra", "acq003", "acq004", "acq005"]
        session = BidsSession("sub-ABC001", "ses-01")
        self.gen_paths(data_path, session, acqs)
        prefix = "{}/{}/MRI".format(session.subject, session.session)

        with self.assertLogs(level=logging.ERROR):
            self.assertFalse(General.CheckPrepared(data_path, w_list, session))
        with self.assertLogs(level=logging.INFO) as cm:
            General.CleanupPrepared(data_path, r_list, session)
        self.assertEqual(cm.output,
                         ["{}:Removing 002-extra from {}"
                          .format(log_info, prefix)])
        self.assertTrue(General.CheckPrepared(data_path, w_list, session))
        shutil.rmtree(os.path.join(data_path, session.subject))

        session = BidsSession("sub-ABC002", "ses-01")
        General.CleanupPrepared(data_path, r_list, session)

        acqs = ["acq001", "acq002", "extra", "acq003", "acq004", "acq005"]
        session = BidsSession("sub-ABC001", "ses-01")
        self.gen_paths(data_path, session, acqs)
        with self.assertLogs(level=logging.ERROR):
            self.assertFalse(General.CheckPrepared(data_path, w_list, session))
        General.CleanupPrepared(data_path, r_list)
        self.assertTrue(General.CheckPrepared(data_path, w_list, session))
        shutil.rmtree(os.path.join(data_path, session.subject))


if __name__ == '__main__':
    unittest.main()
