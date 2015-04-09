#!/usr/bin/python
__author__ = 'joshsmith'

from base import *

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

class RetryTest(SanitiseTest):

    def test_can_set_trust_source(self):
        s = self.minimal_object()
        s.trust_source = True

class LogFileTest(SanitiseTest):

    def test_correct_name_given_to_log_folder(self):
        s = self.minimal_object()
        s.set_logs('folder_name')
        log_folder = os.path.join(s.illegal_log_dir, 'folder_name')
        log_file_pattern = os.path.join(log_folder, "[0-9]{4}-[0-9]{4}.log")
        self.assertTrue(re.match(log_file_pattern, s.log_files[0]))


if __name__ == '__main__':
    unittest.main()