#!/usr/bin/python
__author__ = 'joshsmith'

import unittest
from sanitiseandmove import *

class ObjectTest(unittest.TestCase):

    def setUp(self):
        pass
    def tearDown(self):
        pass

    def test_can_create_sanitise_object(self):
        test_object = Sanitisation()

if __name__ == '__main__':
    unittest.main(exit=False)