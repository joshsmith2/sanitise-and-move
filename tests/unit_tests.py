#!/usr/bin/python
__author__ = 'joshsmith'

import os
import unittest
# Import sanitiseandmove
try:
    from sanitiseandmove import *
except ImportError:
    sam_dirname = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(sam_dirname)
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

class IgnoringClashesTest(unittest.TestCase):

    def test_can_set_trust_source(self):
        s = Sanitisation('/tmp', trust_source=True)
        self.assertTrue(s.trust_source)

if __name__ == '__main__':
    unittest.main()
