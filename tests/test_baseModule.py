import unittest
import os
import logging

from bidsme.bidsMeta import BidsSession
from bidsme.Modules.exceptions import CharacteristicError
from tests.testModule import testModule

data_path = os.path.dirname(__file__)
data_path = os.path.join(data_path, "data", "plugins", "curation")


class TestMetadata(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        BidsSession.loadSubjectFields(
                os.path.join(data_path, "participants.json"))

    def setUp(self):
        # self.log = init()
        self.rec = testModule()
        self.rec.setBidsSession(BidsSession("sub-001", "ses-test"))

    def testCharecteristic(self):
        self.assertEqual(self.rec.getCharecteristic("subject"),
                         "sub-001")

        self.assertEqual(self.rec.getCharecteristic("session"),
                         "ses-test")

        self.rec.series_no = 999
        self.assertEqual(self.rec.getCharecteristic("serieNumber"), 999)
        self.rec.series_id = "RecordingId"
        self.assertEqual(self.rec.getCharecteristic("serie"), "RecordingId")

        self.rec.files = ["abc", "def", "hij"]
        self.rec.index = 1
        self.assertEqual(self.rec.getCharecteristic("index"), 2)
        self.assertEqual(self.rec.getCharecteristic("nfiles"), 3)
        self.assertEqual(self.rec.getCharecteristic("filename"), "def")

        self.rec.suffix = "suffix"
        self.assertEqual(self.rec.getCharecteristic("suffix"), "suffix")
        self.assertEqual(self.rec.getCharecteristic("modality"), "__unknown__")
        self.assertEqual(self.rec.getCharecteristic("module"), "TEST")

        log_info = "WARNING:bidsme.Modules.base"
        with self.assertLogs(level=logging.WARN) as cm:
            self.assertEqual(self.rec.getCharecteristic("placeholder"),
                             "<<placeholder>>")
        self.assertEqual(cm.output,
                         ["{}:{}: Placehoder found"
                          .format(log_info, self.rec.recIdentity())
                          ])

        self.assertIsNone(self.rec.getCharecteristic("None"))

        with self.assertRaises(CharacteristicError):
            self.rec.getCharecteristic("xxx")

    def testCharecteristicPrefix(self):
        self.rec.labels = {"l001": "v001",
                           "l002": "v002",
                           "l003": "v003"}
        self.rec.custom = {"c001": "v001",
                           "c002": "v002",
                           "c003": "v003"}
        self.rec.getBidsSession().sub_values = {"s001": "v001",
                                                "s002": "v002",
                                                "s003": "v003"}
        self.assertEqual(self.rec.getCharecteristic("bids:l001"), "v001")
        self.assertEqual(self.rec.getCharecteristic("custom:c002"), "v002")
        self.assertEqual(self.rec.getCharecteristic("sub_tsv:s003"), "v003")
        # Rec values are not implemented!
        # self.assertEqual(self.rec.getCharecteristic("rec_tsv:r001", "v001"))
        self.rec.files = ["test-1111.nii"]
        self.rec.index = 0
        self.assertEqual(self.rec.getCharecteristic("fname:test"), "1111")
        self.assertIsNone(self.rec.getCharecteristic("fname:fail"))
        self.rec.files = ["_test-1111.nii"]
        self.assertEqual(self.rec.getCharecteristic("fname:test"), "1111")
        self.rec.files = [" test-1111.nii"]
        self.assertIsNone(self.rec.getCharecteristic("fname:test"))
        self.rec.files = [" te:st-1111.nii"]
        self.assertIsNone(self.rec.getCharecteristic("fname:te:st"))

        # Increments
        self.assertEqual(self.rec.getCharecteristic("increment:test"), "1")
        self.assertEqual(self.rec.getCharecteristic("increment1:test"), "2")
        self.assertEqual(self.rec.getCharecteristic("increment2:test"), "03")
        self.assertEqual(self.rec.getCharecteristic("increment2:test1"), "01")

        with self.assertRaises(CharacteristicError):
            self.rec.getCharecteristic("increment:")

        with self.assertRaises(CharacteristicError):
            self.rec.getCharecteristic("abc:def")

    def testgetField(self):
        self.rec._HEADER_CACHE = {"f001": " text\t",
                                  "f002": 3.14,
                                  "f003": None,
                                  "l004": [1, 2, 3],
                                  "d005": {"a": 4, "b": 5}
                                  }

        # Missing metadata, or retrieved None
        self.assertIsNone(self.rec.getField("xxx"))
        self.assertIsNone(self.rec.getField("f003"))

        # Present data, retrieving value
        self.assertEqual(self.rec.getField("f001"), "text")
        self.assertEqual(self.rec.getField("f002"), 3.14)
        self.assertEqual(self.rec.getField("l004"), [1, 2, 3])

        # Testing actions
        # No action applied for empty result
        self.assertIsNone(self.rec.getField("test:f003"))
        # Action applied on not None default vakue
        self.assertEqual(self.rec.getField("xxx", default=3), 3)

        # Order of actions
        self.assertEqual(self.rec.getField("scale1:round:f002"), 30)
        # Applied to lists and dicts
        self.assertEqual(self.rec.getField("str:l004"), ["1", "2", "3"])
        self.assertEqual(self.rec.getField("str:d005"), {"a": "4", "b": "5"})

    def testAttribute(self):
        self.rec._HEADER_CACHE = {"f001": "text"}
        self.rec.setAttribute("f001", "text2")
        self.assertEqual(self.rec.getAttribute("f001"), "text2")
        self.rec.resetAttribute("f001")
        self.assertEqual(self.rec.getAttribute("f001"), "text")

    def testDynamicField(self):
        self.rec._HEADER_CACHE = {"f001": 9}

        # Non-string fields
        self.assertEqual(self.rec.getDynamicField(3), 3)
        self.assertEqual(self.rec.getDynamicField(""), "")

        # Raw returns
        self.assertEqual(self.rec.getDynamicField("<f001>", raw=True), 9)
        self.assertEqual(self.rec.getDynamicField("<f001>"), "9")
        self.assertEqual(self.rec.getDynamicField("<f001>a", raw=True), "9a")
        self.assertEqual(self.rec.getDynamicField("<f001>a"), "9a")

        # Cleanup of values
        self.assertEqual(self.rec.getDynamicField(":<f001>_"), "9")
        self.assertEqual(self.rec.getDynamicField(":<f001>_",
                                                  cleanup=False), ":9_")

        # Characteristics
        self.assertEqual(self.rec.getDynamicField("<<subject>>"), "sub001")
        with self.assertRaises(CharacteristicError):
            self.rec.getDynamicField("<<subjectX>>")

        # Missing metadata warnings
        log_info = "DEBUG:bidsme.Modules.base"
        with self.assertLogs(level=logging.DEBUG) as cm:
            self.assertIsNone(self.rec.getDynamicField("<f002>", raw=True,
                                                       warning=False))
        self.assertEqual(cm.output,
                         ["{}:{}: Can't get attribute 'f002' from '<f002>'"
                          .format(log_info, self.rec.recIdentity())
                          ])

        log_info = "WARNING:bidsme.Modules.base"
        with self.assertLogs(level=logging.WARN) as cm:
            self.assertIsNone(self.rec.getDynamicField("<f002>", raw=True,
                                                       warning=True))
        self.assertEqual(cm.output,
                         ["{}:{}: Can't get attribute 'f002' from '<f002>'"
                          .format(log_info, self.rec.recIdentity())
                          ])

        # Testing multiple substitutions
        self.assertEqual(self.rec.getDynamicField("<f001>_<<subject>>",
                                                  cleanup=False),
                         "9_sub-001")
        self.assertEqual(self.rec.getDynamicField("<f002>_<<subject>>",
                                                  cleanup=False),
                         "<f002>_sub-001")


if __name__ == '__main__':
    unittest.main()
