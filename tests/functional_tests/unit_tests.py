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

class RetryTests(SanitiseTest):

    def test_can_set_trust_source(self):
        s = self.minimal_object()
        s.trust_source = True

    def test_same_file_in_source_and_dest_does_not_move(self):
        s = self.minimal_object()
        file_name = 'source_file.txt'
        dir_name = 'same'

        source_dir = os.path.join(self.to_archive, dir_name)
        dest_dir = os.path.join(self.dest, dir_name)
        log_dir = os.path.join(self.logs, dir_name)
        source_file = os.path.join(source_dir, file_name)
        dest_file = os.path.join(dest_dir, file_name)

        os.mkdir(source_dir)
        os.mkdir(log_dir)
        swisspy.make_file(source_dir, file_name)
        shutil.copytree(source_dir, dest_dir)

        self.assertTrue(os.path.exists(source_file))

        # Make log file manually (this usually done by the script outside of
        # the retry function
        s.log_files = [os.path.join(log_dir, '0000-0000.log')]

        return_value = s.retry_transfer(source_file, dest_file, [])

        # Return value should be none, as there's nothing to be done.
        self.assertFalse(return_value)
        self.assertFalse(os.path.exists(source_file))
        self.assertTrue(os.path.exists(dest_file))


    def test_retrying_a_file_only_in_dest_errors(self):
        s = self.minimal_object()
        file_name = 'source_file.txt'
        dir_name = 'same'

        source_dir = os.path.join(self.to_archive, dir_name)
        dest_dir = os.path.join(self.dest, dir_name)
        log_dir = os.path.join(self.logs, dir_name)
        source_file = os.path.join(source_dir, file_name)
        dest_file = os.path.join(dest_dir, file_name)

        os.mkdir(dest_dir)
        os.mkdir(log_dir)
        swisspy.make_file(dest_dir, file_name)

        s.log_files = [os.path.join(log_dir, '0000-0000.log')]

        s.retry_transfer(source_file, dest_file, [])

        expected_logs = [ file_name + "/" + dir_name + " does not exist. Look " \
                         "for it at "]
        self.check_in_logs(dir_name, expected_logs)

    def test_more_than_one_error_retried(self):
        self.assertFalse(True, "Write test!")

    def test_retrying_file_does_not_change_mod_date(self):
        self.assertFalse(True, "Write test!")



if __name__ == '__main__':
    unittest.main()