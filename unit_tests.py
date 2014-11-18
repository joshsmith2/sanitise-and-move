#!/usr/bin/python
__author__ = 'joshsmith'

import unittest
from sanitiseandmove import *

class ObjectTest(unittest.TestCase):

    def setUp(self):
        pass
    def tearDown(self):
        pass

    def test_can_create_sanitise_object_with_correct_defaults(self):
        test_object = Sanitisation("/tmp")
        self.assertTrue(test_object.case_sens == False)

if __name__ == '__main__':
    unittest.main(exit=False)