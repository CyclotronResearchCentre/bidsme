import unittest
import os
import logging
import shutil
import glob

from bidsme.main import init
from bidsme.Modules import baseModule
from bidsme.Modules.common import retrieveFormDict
from bidsme.bidsMeta import BidsSession
from bidsme.Modules.exceptions import CharacteristicError

data_path = os.path.dirname(__file__)
data_path = os.path.join(data_path, "data", "plugins", "curation")


class testModule(baseModule):
    _module = "TEST"
    _type = "testModule"

    def __init__(self):
        super().__init__()

        self._HEADER_CACHE = None
        self._FILE_CACHE = ""
        self._header_file = ""

    @classmethod
    def _isValidFile(cls, file: str) -> bool:
        return True

    def _loadFile(self, path: str) -> None:
        self._FILE_CACHE = {}

    def _getAcqTime(self):
        return None

    def dump(self):
        return ""

    def _getField(self, field: list):
        return retrieveFormDict(field, self._HEADER_CACHE,
                                fail_on_last_not_found=False)

    def _recNo(self):
        return None

    def _recId(self):
        return None

    def isCompleteRecording(self):
        return True

    def _getSubId(self):
        return "unknown"

    def _getSesId(self):
        return "unknown"


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
