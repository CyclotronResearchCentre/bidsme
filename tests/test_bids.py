import unittest
import os

from bidscoin.bids import bidsversion, version


class TestBids(unittest.TestCase):

    def test_version(self):
        v = version()
        v_from_file = 0.0
        with open('version.txt') as fp:
            v_from_file = float(fp.read())
        self.assertEqual(v, v_from_file)

    def test_bids_version(self):
        bids_v = bidsversion()
        bids_v_from_file = ''
        with open('bidsversion.txt') as fp:
            bids_v_from_file = fp.read()
        self.assertEqual(bids_v, bids_v_from_file)


if __name__ == '__main__':
    unittest.main()
