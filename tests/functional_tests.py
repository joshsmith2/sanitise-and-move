#!/usr/bin/python

import unittest
import os
import inspect
import shutil
import subprocess as sp
import swisspy


class FileTransferTest(unittest.TestCase):

    def setUp(self):
        # Variables
        self.current_path = os.path.abspath(inspect.stack()[0][1])
        self.current_dir = os.path.dirname(self.current_path)

        # A dictionary containing all paths which need to be created for the test
        self.source_dir_name = 'test_source/'
        self.dest_dir_name = 'test_dest/'
        self.log_dir_name = 'test_logs/'

        self.source = os.path.join(self.current_dir, self.source_dir_name)
        self.dest = os.path.join(self.current_dir, self.dest_dir_name)
        self.log = os.path.join(self.current_dir, self.log_dir_name)
        self.rootdirs = [self.source, self.log, self.dest]

        self.source_subfolders = ['.Hidden', 'To Archive', 'Problem Files', 'Logs']
        self.log_subfolders = ['syslogs','renamed']



        self.root_script_dir = os.path.dirname(self.current_dir)
        self.command_path = os.path.abspath(os.path.join(self.root_script_dir,
                                                    'sanitise-and-move.py'
        ))


        #Construct a list to run the sanitisePaths command using Popen
        self.minimal_command = [self.command_path,
                           '-q',
                           '-t', self.source,
                           '-p', self.dest,
                           '-r', os.path.join(self.log,'renamed'),
                           '-l', os.path.join(self.log, 'syslogs')
        ]

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

    def test_clean_files_get_to_dest_safely(self):
        container_path = os.path.join(self.source, 'To Archive', 'new_dir')
        os.mkdir(container_path)
        content_path = os.path.join(container_path, 'file_to_transfer.txt')
        with open(content_path, 'w') as content:
            content.write("Fast and bulbous")

        sp.call(self.minimal_command)

        self.assertTrue(os.path.exists(os.path.join(self.dest, 'new_dir')))


    # Transfer files without changing the modification time, md5, name etc.
    def test_file_gets_there_intact(self):
        full_container = os.path.join(self.source,
                                      'To Archive',
                                      'full_container')
        os.mkdir(full_container)
        test_file_source = os.path.join(self.current_dir, 'test_file')
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

        sp.call(self.minimal_command)

        test_file_after = os.path.join(self.dest, 'full_container', 'test_file')
        observed_md5 = swisspy.get_md5(test_file_after)
        observed_mod_time = swisspy.get_mod_time(test_file_after)

        self.assertEqual(observed_md5, correct_md5)
        self.assertEqual(observed_mod_time, correct_mod_time)

    # Delete .DS_Store files

    # Not transfer any existing same files

    # Error on any existing different files

    # Transfer any new files in existing directories

    # If the connection is broken, error nicely

    # Not be able to run twice on the same directory

    # Rename any files with blacklisted names, and log these properly.

    # Log files which want to be logged, put them into pf and do not transfer.

if __name__ == '__main__':
    unittest.main(exit=False)