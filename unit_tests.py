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
        test_object = Sanitisation("/tmp", test_suite=True)
        self.assertTrue(test_object.case_sens == False)

class RenamingTest(unittest.TestCase):

    def test_whitespace_gets_stripped_from_end(self):
        input = "Pang   "
        desired="Pang"
        output = sanitise(input)['out_string']

        self.assertEqual(output, desired)

    def test_if_whitespace_becomes_a_trailing_space_it_gets_trimmed(self):
        input = "Strapping\tBadjam\n"
        desired = "Strapping Badjam"
        output = sanitise(input)['out_string']

        self.assertEqual(output, desired)

if __name__ == '__main__':
    unittest.main()