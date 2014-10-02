#!/usr/bin/python

import unittest
import os
import inspect
import shutil
import subprocess as sp
import time


class FileTransferTest(unittest.TestCase):

    def setUp(self):
        # Variables
        self.current_running_path = os.path.abspath(inspect.stack()[0][1])
        self.current_running_dir = os.path.dirname(self.current_running_path)

        # A dictionary containing all paths which need to be created for the test
        self.source_dir_name = 'test_source/'
        self.dest_dir_name = 'test_dest/'
        self.log_dir_name = 'test_logs/'

        self.test_dirs = {
            'source': os.path.join(self.current_running_dir, self.source_dir_name),
            'dest': os.path.join(self.current_running_dir, self.dest_dir_name),
            'log': os.path.join(self.current_running_dir, self.log_dir_name),
            }

        self.root_script_dir = os.path.dirname(self.current_running_dir)
        self.command_path = os.path.abspath(os.path.join(self.root_script_dir,
                                                    'sanitise-and-move.py'
        ))

        #Construct a list to run the sanitisePaths command using Popen
        self.minimal_command = [self.command_path,
                           '-q',
                           '-t', self.test_dirs['source'],
                           '-p', self.test_dirs['dest'],
                           '-r', os.path.join(self.test_dirs['log'],'renamed'),
                           '-l', os.path.join(self.test_dirs['log'], 'syslogs')
        ]

        self.create_dir_structure()

    def tearDown(self):
        for dir in self.test_dirs:
            try:
                shutil.rmtree(self.test_dirs[dir])
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

    def create_dir_structure(self):
        for d_name in self.test_dirs:
            self.make_dir_if_not_exists(self.test_dirs[d_name])
        for d in ['.Hidden', 'To Archive', 'Problem Files', 'Logs']:
            self.make_dir_if_not_exists(os.path.join(self.test_dirs['source'], d))
        for d in ['syslogs','renamed']:
            self.make_dir_if_not_exists(os.path.join(self.test_dirs['log'], d))

    def test_do_not_move_files_not_in_a_directory(self):
        orphan_file_path = os.path.join(self.test_dirs['source'],'To Archive', 'orphan.txt')
        with open(orphan_file_path, 'w') as orphan_file:
            orphan_file.write("NO MOVEY FILEY")

        sp.call(self.minimal_command)

        assert os.path.exists(orphan_file_path)
        assert not os.path.exists(os.path.join(self.test_dirs['dest'], 'orphan.txt'))
        assert not os.listdir(os.path.join(self.test_dirs['source'], 'Logs'))

    def test_clean_files_get_to_dest_safely(self):
        container_path = os.path.join(self.test_dirs['source'], 'To Archive', 'new_dir')
        os.mkdir(container_path)
        content_path = os.path.join(container_path, 'file_to_transfer.txt')
        with open(content_path, 'w') as content:
            content.write("Fast and bulbous")

        sp.call(self.minimal_command)

        assert os.path.exists(os.path.join(self.test_dirs['dest'], 'new_dir'))


    # Transfer files without changing the modification time, md5, name etc.

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