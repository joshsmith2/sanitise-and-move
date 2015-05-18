#!/usr/bin/python

from base import *
import unittest
import time

def is_empty(directory):
    contents = len(os.listdir(directory))
    is_empty = True
    if contents > 0:
        is_empty = False
    return is_empty

class FileTransferTest(SanitiseTest):

    def check_files_moved_to_dest(self):
        self.assertTrue(is_empty(self.hidden))
        self.assertTrue(is_empty(self.problem_files))
        self.assertFalse(is_empty(self.dest))

    def test_do_not_move_files_not_in_a_directory(self):
        orphan_file_path = os.path.join(self.to_archive, 'orphan.txt')
        with open(orphan_file_path, 'w') as orphan_file:
            orphan_file.write("NO MOVEY FILEY")

        sp.check_call(self.minimal_command)

        self.assertTrue(os.path.exists(orphan_file_path))
        assert not os.path.exists(os.path.join(self.dest, 'orphan.txt'))
        assert not os.listdir(os.path.join(self.source, 'Logs'))

    def test_clean_files_leave_source_and_get_to_dest_safely(self):
        container_path = os.path.join(self.to_archive, 'new_dir')
        os.mkdir(container_path)
        content_path = os.path.join(container_path, 'file_to_transfer.txt')
        with open(content_path, 'w') as content:
            content.write("Fast and bulbous")

        sp.check_call(self.minimal_command)

        self.assertTrue(os.path.exists(os.path.join(self.dest, 'new_dir')))
        self.assertFalse(os.path.exists(os.path.join(self.source,
                                                     'Problem Files',
                                                     'new_dir')))
        self.check_files_moved_to_dest()

    # Transfer files without changing the modification time, md5, name etc.
    def test_file_gets_there_intact(self):
        full_container = os.path.join(self.to_archive, 'full_container')
        os.mkdir(full_container)
        test_file_source = os.path.join(self.tests_dir, 'test_file')
        test_file_dest = os.path.join(self.to_archive,
                                      'full_container',
                                      'test_file')
        shutil.copyfile(test_file_source, test_file_dest)
        correct_md5 = swisspy.get_md5(os.path.join(full_container,
                                                   'test_file'))
        correct_mod_time = swisspy.get_mod_time(os.path.join(full_container,
                                                             'test_file'))

        s = self.minimal_object()
        main(s)

        test_file_after = os.path.join(self.dest, 'full_container', 'test_file')
        observed_md5 = swisspy.get_md5(test_file_after)
        observed_mod_time = swisspy.get_mod_time(test_file_after)

        self.assertEqual(observed_md5, correct_md5)
        self.assertEqual(observed_mod_time, correct_mod_time)
        self.check_files_moved_to_dest()

    # Do not transfer any existing same files
    def test_same_files_not_transferred(self):
        same_file_dir = os.path.join(self.source,
                                     'To Archive',
                                     'same_file')
        os.mkdir(same_file_dir)
        test_file_source = os.path.join(self.tests_dir, 'test_file')
        test_file_dest = os.path.join(self.dest, 'same_file')

        shutil.copy(test_file_source, same_file_dir)
        shutil.copytree(same_file_dir, test_file_dest)

        self.assertTrue(os.path.exists(os.path.join(self.dest,
                                                    'same_file',
                                                    'test_file')))

        sp.check_call(self.minimal_command)

        self.assertFalse(self.in_problem_files('same_file'))
        expected_logs = ["1 files already have up-to-date copies " +\
                         "in the archive, and were therefore not transferred."]
        self.check_in_logs('same_file', expected_logs)

    # Log problem files without renaming them
    def test_log_bad_files(self):
        bad_dir = os.path.join(self.to_archive, 'bad')
        bad_subdir_names = ['***', '"strings??', 'white\tspace\n',
                            'multi', 'multi*', 'multi?']
        clean_subdir_names = ['___', '_strings__', 'multi', 'multi_',
                              'multi_(1)', 'white space']
        bad_sub_dirs = [os.path.join(bad_dir, bsn) for bsn in bad_subdir_names]
        clean_sub_dirs = [os.path.join(bad_dir, csn) for csn in clean_subdir_names]

        os.mkdir(bad_dir)
        for bsd in bad_sub_dirs:
            os.mkdir(bsd)

        sp.check_call(self.minimal_command)

        self.assertTrue(self.in_problem_files('bad'))
        self.assertFalse(self.in_dest('bad'))

        expected_logs = ["bad has been moved to"]
        illegal_message = "Illegal characters found in file   : bad/"
        change_message = "Suggested change                   : bad/"
        illegal_messages = [illegal_message + b for b in bad_subdir_names]
        change_messages = [change_message + c for c in clean_subdir_names]
        expected_logs.extend(illegal_messages)
        expected_logs.extend(change_messages)
        self.check_in_logs("bad", expected_logs)

    #Rename files if asked
    def test_rename_bad_files(self):
        bad_dir = os.path.join(self.to_archive, 'bad')
        bad_subdir_names = ['***', '"strings??', 'white\tspace\n',
                            'multi', 'multi*', 'multi?',]
        clean_subdir_names = ['___', '_strings__', 'multi', 'multi_',
                              'multi_(1)', 'white space',]
        bad_sub_dirs = [os.path.join(bad_dir, bsn) for bsn in bad_subdir_names]
        os.mkdir(bad_dir)
        for bsd in bad_sub_dirs:
            os.mkdir(bsd)

        s = self.minimal_object()
        main(s)

        self.assertFalse(self.in_problem_files('bad'))
        self.assertTrue(self.in_dest('bad'))

        expected_logs = ["Finished sanitising bad."]
        illegal_message = "Changed from: bad/"
        change_message = "Changed to:   bad/"
        illegal_messages = [illegal_message + b for b in bad_subdir_names]
        change_messages = [change_message + c for c in clean_subdir_names]
        expected_logs.extend(illegal_messages)
        expected_logs.extend(change_messages)
        self.check_in_logs("bad", expected_logs)

        for f in [os.path.join(self.dest, 'bad', c) for c in clean_subdir_names]:
            self.assertTrue(os.path.exists(f), f + " does not exist")

    # Add trailing spaces to renaming
    def test_remove_trailing_spaces(self):
        spaces_dir = os.path.join(self.to_archive, 'spaces')
        os.mkdir(spaces_dir)
        swisspy.make_file(spaces_dir, 'file with trailing space ')
        swisspy.make_file(spaces_dir, 'file with trailing spaces   ')
        os.mkdir(os.path.join(spaces_dir, 'dir with trailing space '))

        s = self.minimal_object()
        main(s)

        self.assertTrue(self.in_dest('spaces'))
        changed = ['file with trailing space', 'file with trailing spaces',
                   'dir with trailing space']
        changed_paths = [os.path.join(self.dest, 'spaces', c) for c in changed]
        for c in changed_paths:
            self.assertTrue(os.path.exists(c), c + " does not exist")

    def test_rename_flag_works(self):
        spaces_dir = os.path.join(self.to_archive, 'spaces')
        os.mkdir(spaces_dir)
        swisspy.make_file(spaces_dir, 'file with trailing space ')
        swisspy.make_file(spaces_dir, 'file with trailing spaces   ')
        os.mkdir(os.path.join(spaces_dir, 'dir with trailing space '))

        self.minimal_command.append('-d')
        sp.check_call(self.minimal_command)

        self.assertTrue(self.in_dest('spaces'))
        changed = ['file with trailing space', 'file with trailing spaces',
                   'dir with trailing space']
        changed_paths = [os.path.join(self.dest, 'spaces', c) for c in changed]
        for c in changed_paths:
            self.assertTrue(os.path.exists(c), c + " does not exist")

    def test_nested_directories_tranfer_ok(self):
        dirs_to_create = []
        root = 'banhammer_20501'
        dirs_to_create.append(root)
        for i in range(4):
            child = os.path.join(root, 'child_job_60060_' + str(i))
            dirs_to_create.append(child)
            for j in range(4):
                grandchild = os.path.join(child, 'grandchild_job_' + str(j))
                dirs_to_create.append(grandchild)
        for d in dirs_to_create:
            path = os.path.join(self.to_archive, d)
            os.mkdir(path)
        s=self.minimal_object()
        main(s)
        self.check_files_moved_to_dest()
        for d in dirs_to_create:
            dest_path = os.path.join(self.dest, d)
            self.assertTrue(os.path.exists(dest_path))


class TrustSourceTest(SanitiseTest):

    def test_trust_source_works_and_overwrites_files(self):
        # Make a directory twice, with two seperately created files
        def create_test_dir(to_write):
            os.mkdir(dir_to_move)
            with open (source_file, 'w') as f:
                f.write(to_write)

        dir_to_move = os.path.join(self.to_archive, 'Bunsen')
        source_file = os.path.join(dir_to_move, 'Berna.txt')
        dest_file = os.path.join(self.dest, 'Bunsen', 'Berna.txt')
        create_test_dir("BANGABANG")

        first_mod_time = os.path.getmtime(source_file)

        s = self.minimal_object()
        main(s)

        # Check that's moved the file
        self.assertFalse(os.path.exists(source_file))
        self.assertFalse(os.path.exists(dir_to_move))
        self.assertTrue(os.path.exists(dest_file))

        with open(dest_file, 'r') as f:
            dest_contents = f.readlines()

        self.assertTrue("BANGABANG" in dest_contents)
        time.sleep(1)

        create_test_dir("HANGABANG")
        second_mod_time = os.path.getmtime(source_file)

        self.assertTrue(second_mod_time > first_mod_time)

        t = self.minimal_object()
        t.trust_source = True
        main(t)

        dest_mod_time = os.path.getmtime(dest_file)
        with open(dest_file, 'r') as f:
            dest_contents = f.readlines()

        self.assertTrue("HANGABANG" in dest_contents)
        self.assertEqual(dest_mod_time, second_mod_time)

    def test_empty_directories_dont_overwrite_full_ones(self):

        def create_test_dir(to_write):
            os.mkdir(dir_to_move)
            with open (source_file, 'w') as f:
                f.write(to_write)

        dir_to_move = os.path.join(self.to_archive, 'test_dir')
        source_file = os.path.join(dir_to_move, 'Keepme.txt')
        dest_file = os.path.join(self.dest, 'test_dir', 'Keepme.txt')
        create_test_dir("VALUABLE_INFO")

        s = self.minimal_object()
        main(s)

        # Check that's moved the file
        self.assertFalse(os.path.exists(source_file))
        self.assertFalse(os.path.exists(dir_to_move))
        self.assertTrue(os.path.exists(dest_file))

        os.mkdir(dir_to_move)

        t = self.minimal_object()
        t.trust_source = True
        main(t)

        self.assertFalse(os.path.exists(dir_to_move))
        self.assertTrue(os.path.exists(dest_file))

    def test_transfer_fails_if_file_to_move_is_smaller_than_on_archive(self):
        dir_source = os.path.join(self.to_archive, 'a_dir')
        dir_dest = os.path.join(self.dest, 'a_dir')
        dir_problem = os.path.join(self.problem_files, 'a_dir')
        file_source = os.path.join(dir_source, 'a_file')
        file_dest = os.path.join(dir_dest, 'a_file')

        # Create dir to move
        os.mkdir(dir_source)
        with open(file_source, 'w') as f:
            f.write('1234567890')
        shutil.copytree(dir_source, dir_dest)

        self.assertTrue(os.path.exists(file_dest))

        # Now make the source smaller
        with open(file_source, 'w') as f:
            f.write('12345')

        s = self.minimal_object()
        s.trust_source = True
        self.assertRaises(IOError, main, s)

        # Check the source has gone
        self.assertFalse(os.path.exists(file_source))

        # Check the destination has not been overwritten, and the file has
        # been moved to pf.
        with open(file_dest, 'r') as f:
            file_contents = [l.strip() for l in f.readlines()]
        for c in file_contents:
            self.assertTrue('67890' in c)
        self.assertTrue(os.path.exists(dir_problem))

        # Check logs
        expected = ["The following 1 files already exist in " + dir_dest,
                    "the transfer was unable to continue.",
                    "Please version these files and attempt the upload again"]
        self.check_in_logs('a_dir', expected)

    def test_transfer_succeeds_if_file_to_move_is_larger_than_on_archive(self):
        dir_source = os.path.join(self.to_archive, 'a_dir')
        dir_dest = os.path.join(self.dest, 'a_dir')
        dir_problem = os.path.join(self.problem_files, 'a_dir')
        file_source = os.path.join(dir_source, 'a_file')
        file_dest = os.path.join(dir_dest, 'a_file')

        # Create dir to move
        os.mkdir(dir_source)
        with open(file_source, 'w') as f:
            f.write('12345')
        shutil.copytree(dir_source, dir_dest)

        self.assertTrue(os.path.exists(file_dest))

        # Now make the source smaller
        with open(file_source, 'w') as f:
            f.write('1234567890')

        s = self.minimal_object()
        s.trust_source = True
        main(s)

        # Check the source has gone
        self.assertFalse(os.path.exists(file_source))

        # Check the destination has been overwritten, and the file has
        # been moved to pf.
        with open(file_dest, 'r') as f:
            file_contents = [l.strip() for l in f.readlines()]
        for c in file_contents:
            self.assertTrue('67890' in c)
        self.assertFalse(os.path.exists(dir_problem))

        # Check logs
        expected = ["The following 1 files already exist in " + dir_dest,
                    "will be transferred since trust source is set."]
        self.check_in_logs('a_dir', expected)

    def test_trust_source_will_not_transfer_identical_preexisting_files(self):
        dir_source = os.path.join(self.to_archive, 'a_dir')
        dir_dest = os.path.join(self.dest, 'a_dir')
        dir_problem = os.path.join(self.problem_files, 'a_dir')
        file_source = os.path.join(dir_source, 'a_file')
        file_dest = os.path.join(dir_dest, 'a_file')

        # Create dir to move
        os.mkdir(dir_source)
        with open(file_source, 'w') as f:
            f.write('12345')
        shutil.copytree(dir_source, dir_dest)
        self.assertTrue(os.path.exists(file_dest))

        s = self.minimal_object()
        s.trust_source = True
        main(s)

        unwanted = ["files already exist in %s, but will be transferred"]
        self.check_in_logs('a_dir', unwanted, positive_test=False)
        wanted = ["1 files already have up-to-date copies"]
        self.check_in_logs('a_dir', wanted)





class RetryTest(SanitiseTest):

    def test_failed_files_are_retried(self):
        directory = os.path.join(self.to_archive, 'sendme')
        os.mkdir(directory)
        _file = os.path.join(directory, 'sendy.txt')
        with open(_file, 'w') as f:
            f.write("Willies.")

        s = self.minimal_object()
        s.pass_dir = '/dev/null'
        file_path = os.path.join('sendme', 'sendy.txt')
        #Create log directory (usually handled by script)
        s.set_logs('sendme')
        self.assertRaises(IOError, s.move_files, self.to_archive, self.dest,
                          [file_path])

        messages = ["RETRY %s: sendme/sendy.txt" % str(i) for i in range(1,4)]
        self.check_in_logs('sendme', messages)

    def test_three_failures_leads_to_an_error_message(self):
        directory = os.path.join(self.to_archive, 'sendme')
        os.mkdir(directory)
        _file = os.path.join(directory, 'sendy.txt')
        with open(_file, 'w') as f:
            f.write("Willies.")

        s = self.minimal_object()
        s.pass_dir = '/dev/null'
        file_path = os.path.join('sendme', 'sendy.txt')
        #Create log directory (usually handled by script)
        s.set_logs('sendme')
        self.assertRaises(IOError, s.move_files, self.to_archive, self.dest,
                          [file_path])
        unwanted = ["Files transferred:"]
        self.check_in_logs('sendme', unwanted, positive_test=False)

        wanted = ["FAILURE: The following file failed to transfer after 3 "
                  "attempts:",
                  "The error was"]
        self.check_in_logs('sendme', wanted)

    def test_exits_after_first_error(self):
        directory = os.path.join(self.to_archive, 'sendme')
        os.mkdir(directory)
        files = [os.path.join(directory, 'file_{0}.txt'.format(i)) for i in range(1,4)]
        for _file in files:
            with open(_file, 'w') as f:
                f.write("Willies.")

        s = self.minimal_object()
        s.pass_dir = '/dev/null'
        #Create log directory (usually handled by script)
        s.set_logs('sendme')
        self.assertRaises(IOError, s.move_files, self.to_archive, self.dest,
                          files)
        unwanted = ["Files transferred:", "file_2"]
        self.check_in_logs('sendme', unwanted, positive_test=False)

        wanted = ["FAILURE: The following file failed to transfer after 3 "
                  "attempts:",
                  "The error was"]
        self.check_in_logs('sendme', wanted)


if __name__ == '__main__':
    unittest.main()