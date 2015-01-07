#!/usr/bin/python

from base import *
import threading
import sys
import subprocess

class FileTransferTest(FunctionalTest):

    def test_do_not_move_files_not_in_a_directory(self):
        orphan_file_path = os.path.join(self.to_archive, 'orphan.txt')
        with open(orphan_file_path, 'w') as orphan_file:
            orphan_file.write("NO MOVEY FILEY")

        sp.check_call(self.minimal_command)

        self.assertTrue(os.path.exists(orphan_file_path))
        assert not os.path.exists(os.path.join(self.dest, 'orphan.txt'))
        assert not os.listdir(os.path.join(self.source, 'Logs'))

    def test_clean_files_leave_souce_and_get_to_dest_safely(self):
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
        os.mkdir(os.path.join(self.to_archive,
                              'empty_container'))

        s = self.minimal_object()
        main(s)

        test_file_after = os.path.join(self.dest, 'full_container', 'test_file')
        observed_md5 = swisspy.get_md5(test_file_after)
        observed_mod_time = swisspy.get_mod_time(test_file_after)

        self.assertEqual(observed_md5, correct_md5)
        self.assertEqual(observed_mod_time, correct_mod_time)

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
        expected_logs = ["The following files already have up to date copies " +\
                         "in the archive, and were therefore not transferred:\n",
                         "\tsame_file/test_file\n"]
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

    # Check a script being run again won't interrupt it
    def test_cannot_run_script_twice(self):
        large_file = os.path.join(self.tests_dir, 'test_file_large')
        dir_to_move_1 = os.path.join(self.to_archive, 'dir_1')
        dir_to_move_2 = os.path.join(self.to_archive, 'dir_2')
        os.mkdir(dir_to_move_1)
        os.mkdir(dir_to_move_2)

        shutil.copy(large_file, dir_to_move_1)
        shutil.copy(large_file, dir_to_move_2)

        self.assertTrue(os.path.exists(os.path.join(dir_to_move_1,
                                                    'test_file_large')))
        self.assertTrue(os.path.exists(os.path.join(dir_to_move_2,
                                                    'test_file_large')))

        s=self.minimal_object()
        thread_1 = threading.Thread(name='Thread 1', target=main, args=(s,))
        thread_1.start()

        self.assertTrue(exists_in(self.hidden, 'dir_1'))
        self.assertFalse(exists_in(self.hidden, 'dir_2'))
        self.assertTrue(exists_in(self.to_archive, 'dir_2'))
        self.assertFalse(exists_in(self.to_archive, 'dir_1'))





    # Delete .DS_Store files

    # Error on any existing different files

    # Transfer any new files in existing directories

    # If the connection is broken, error nicely

    # Not be able to run twice on the same directory

    # Delete successfully retried files from PF

    # Log files which want to be logged, put them into pf and do not transfer.

    # Remove resource forks properly



if __name__ == '__main__':
    unittest.main()