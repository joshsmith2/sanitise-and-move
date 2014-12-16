#!/usr/bin/python

import unittest
import os
import inspect
from sanitiseandmove import *
import argparse

class FileTransferTest(unittest.TestCase):

    def setUp(self):
        # Variables
        self.current_path = os.path.abspath(inspect.stack()[0][1])
        self.current_dir = os.path.dirname(self.current_path)
        self.test_dir = os.path.join(self.current_dir, 'tests')

        # A dictionary containing all paths which need to be created for the test
        self.source_dir_name = 'test_source'
        self.dest_dir_name = 'test_dest'
        self.log_dir_name = 'test_logs'

        self.source = os.path.join(self.test_dir, self.source_dir_name)

        self.dest = os.path.join(self.test_dir, self.dest_dir_name) # Local
        #self.dest = os.path.join("/Volumes/HGSL-Archive/josh_test/",
        #                         self.dest_dir_name)
        self.log = os.path.join(self.test_dir, self.log_dir_name)
        self.rootdirs = [self.source, self.log, self.dest]

        self.source_subfolders = ['.Hidden', 'To Archive', 'Problem Files', 'Logs']
        self.log_subfolders = ['syslogs','renamed']

        self.root_script_dir = self.current_dir
        self.command_path = os.path.abspath(os.path.join(self.root_script_dir,
                                                         'sanitiseandmove.py'
        ))
        self.rename_log_dir = os.path.join(self.log, 'renamed')
        self.syslog_dir = os.path.join(self.log, 'syslogs')

        #Construct a list to run the sanitisePaths command using Popen
        self.minimal_command = [self.command_path,
                               '-q',
                               '-t', self.source,
                               '-p', self.dest,
                               '-r', self.rename_log_dir,
                               '-l', self.syslog_dir,]
        self.rename_command = self.minimal_command[:]
        self.rename_command.append('-d')

        for root_dir in self.rootdirs:
            self.make_dir_if_not_exists(root_dir)
        for folder in self.source_subfolders:
            setattr(self,
                    folder,
                    os.path.join(self.source, folder))
            self.make_dir_if_not_exists(getattr(self, folder))

        for folder in self.log_subfolders:
            setattr(self,
                    folder,
                    os.path.join(self.log, folder))
            self.make_dir_if_not_exists(getattr(self, folder))

    def tearDown(self):
        for dir in self.rootdirs:
            try:
                shutil.rmtree(dir)
            except OSError as e:
                error_number = e[0]
                if error_number == 2: #File doesn't exist
                    pass
                else:
                    print str(e)
                    raise

    def check_in_logs(self, folder, messages):
        self.get_log_contents(folder)
        for m in messages:
            self.assertTrue(m in '\n'.join(self.log_contents))

    def minimal_object(self):
        """Create and return a sanitisation object which will work, with
        minimal, default arguments."""
        return Sanitisation(self.dest,
                            target=self.source,
                            rename_log_dir=self.rename_log_dir,
                            logstash_dir = self.syslog_dir,
                            rename=True,
                            test_suite=True,
                            )

    def in_problem_files(self, folder):
        folder_in_pf = False
        problem_dir = os.path.join(self.source, 'Problem Files', folder)
        if os.path.exists(problem_dir):
            folder_in_pf = True
        return folder_in_pf

    def in_dest(self, folder):
        folder_in_dest = False
        dest_dir = os.path.join(self.dest, folder)
        if os.path.exists(dest_dir):
            folder_in_dest = True
        return folder_in_dest

    def get_log_contents(self, folder_name):
        log_dir = os.path.join(self.source, 'Logs')
        for log_file in os.listdir(os.path.join(log_dir, folder_name)):
            log_path = os.path.join(log_dir, folder_name, log_file)
            with open(log_path, 'r') as lp:
                self.log_contents = lp.readlines()

    def make_dir_if_not_exists(self, dir):
        try:
            os.mkdir(dir)
        except OSError as e:
            error_number = e[0]
            if error_number == 17:  # File exists
                pass
            else:
                raise

#    def create_dir_structure(self):
#        for d_name in self.test_dirs:
#            self.make_dir_if_not_exists(self.test_dirs[d_name])
#        for d in self.:
#
#        for d in ['syslogs','renamed']:
#            self.make_dir_if_not_exists(os.path.join(self.log, d))

    def test_do_not_move_files_not_in_a_directory(self):
        orphan_file_path = os.path.join(self.source,'To Archive', 'orphan.txt')
        with open(orphan_file_path, 'w') as orphan_file:
            orphan_file.write("NO MOVEY FILEY")

        sp.call(self.minimal_command)

        self.assertTrue(os.path.exists(orphan_file_path))
        assert not os.path.exists(os.path.join(self.dest, 'orphan.txt'))
        assert not os.listdir(os.path.join(self.source, 'Logs'))

    def test_clean_files_leave_souce_and_get_to_dest_safely(self):
        container_path = os.path.join(self.source, 'To Archive', 'new_dir')
        os.mkdir(container_path)
        content_path = os.path.join(container_path, 'file_to_transfer.txt')
        with open(content_path, 'w') as content:
            content.write("Fast and bulbous")

        sp.call(self.minimal_command)

        self.assertTrue(os.path.exists(os.path.join(self.dest, 'new_dir')))
        self.assertFalse(os.path.exists(os.path.join(self.source,
                                                     'Problem Files',
                                                     'new_dir')))

    # Transfer files without changing the modification time, md5, name etc.
    def test_file_gets_there_intact(self):
        full_container = os.path.join(self.source,
                                      'To Archive',
                                      'full_container')
        os.mkdir(full_container)
        test_file_source = os.path.join(self.test_dir, 'test_file')
        test_file_dest = os.path.join(self.source,
                                      'To Archive',
                                      'full_container',
                                      'test_file')
        shutil.copyfile(test_file_source, test_file_dest)
        correct_md5 = swisspy.get_md5(os.path.join(full_container,
                                                   'test_file'))
        correct_mod_time = swisspy.get_mod_time(os.path.join(full_container,
                                                             'test_file'))
        os.mkdir(os.path.join(self.source,
                              'To Archive',
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
        test_file_source = os.path.join(self.test_dir, 'test_file')
        test_file_dest = os.path.join(self.dest, 'same_file')

        shutil.copy(test_file_source, same_file_dir)
        shutil.copytree(same_file_dir, test_file_dest)

        self.assertTrue(os.path.exists(os.path.join(self.dest,
                                                    'same_file',
                                                    'test_file')))

        sp.call(self.minimal_command)

        self.assertFalse(self.in_problem_files('same_file'))
        expected_logs = ["The following files already have up to date copies " +\
                         "in the archive, and were therefore not transferred:\n",
                         "\tsame_file/test_file\n"]
        self.check_in_logs('same_file', expected_logs)

    # Log problem files without renaming them
    def test_log_bad_files(self):
        bad_dir = os.path.join(self.source, 'To Archive', 'bad')
        bad_subdir_names = ['***', '"strings??', 'white\tspace\n',
                            'multi', 'multi*', 'multi?']
        clean_subdir_names = ['___', '_strings__', 'multi', 'multi_',
                              'multi_(1)', 'white space']
        bad_sub_dirs = [os.path.join(bad_dir, bsn) for bsn in bad_subdir_names]
        clean_sub_dirs = [os.path.join(bad_dir, csn) for csn in clean_subdir_names]

        os.mkdir(bad_dir)
        for bsd in bad_sub_dirs:
            os.mkdir(bsd)

        sp.call(self.minimal_command)

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
        bad_dir = os.path.join(self.source, 'To Archive', 'bad')
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
        spaces_dir = os.path.join(self.source, 'To Archive', 'spaces')
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
        spaces_dir = os.path.join(self.source, 'To Archive', 'spaces')
        os.mkdir(spaces_dir)
        swisspy.make_file(spaces_dir, 'file with trailing space ')
        swisspy.make_file(spaces_dir, 'file with trailing spaces   ')
        os.mkdir(os.path.join(spaces_dir, 'dir with trailing space '))

        self.minimal_command.append('-d')
        sp.call(self.minimal_command)

        self.assertTrue(self.in_dest('spaces'))
        changed = ['file with trailing space', 'file with trailing spaces',
                   'dir with trailing space']
        changed_paths = [os.path.join(self.dest, 'spaces', c) for c in changed]
        for c in changed_paths:
            self.assertTrue(os.path.exists(c), c + " does not exist")

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