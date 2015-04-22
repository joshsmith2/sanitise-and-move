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

        self.assertTrue(os.path.exists(log_folder))
        log_file_pattern = os.path.join(log_folder, "[0-9]{4}-[0-9]{4}.log")
        self.assertTrue(re.match(log_file_pattern, s.log_files[0]))

    def test_long_filenames_handled_correctly(self):
        free_hunnid = "12345678901234567890123456789012345678901234567890" \
                      "12345678901234567890123456789012345678901234567890" \
                      "12345678901234567890123456789012345678901234567890" \
                      "12345678901234567890123456789012345678901234567890" \
                      "12345678901234567890123456789012345678901234567890"
        s = self.minimal_object()
        s.set_logs(free_hunnid)

        log_folder = os.path.join(s.illegal_log_dir, free_hunnid)[:246]
        self.assertTrue(os.path.exists(log_folder))
        log_file_pattern = os.path.join(log_folder, ("[0-9]{4}-[0-9]{4}.log"))
        self.assertTrue(re.match(log_file_pattern, s.log_files[0]))

    def test_log_list_doesnt_print_empty_lists(self):
        temp_logfile = os.path.join(self.log, 'temp.txt')
        log_list("Bad header", [], log_files=[temp_logfile])
        log_list("Good header", ['jub', 'jub'], log_files=[temp_logfile])
        with open(temp_logfile, 'r') as f:
            log_contents = f.read()
        self.assertFalse("Bad header" in log_contents)
        self.assertTrue("Good header" in log_contents)


if __name__ == '__main__':
    unittest.main()