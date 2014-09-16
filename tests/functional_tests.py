#!/usr/bin/python

import unittest
import os
import inspect
import shutil
import subprocess as sp
import time


class FileTransferTest(unittest.TestCase):

    def setUp(self):
        td = self.init_vars()['test_dirs']
        self.create_dir_structure(td)

    def tearDown(self):
        td = self.init_vars()['test_dirs']
        for dir in td:
            try:
                shutil.rmtree(td[dir])
            except OSError as e:
                error_number = e[0]
                if error_number == 2: #File doesn't exist
                    pass
                else:
                    print str(e)
                    raise


    def init_vars(self):
        current_running_path = os.path.abspath(inspect.stack()[0][1])
        current_running_dir = os.path.dirname(current_running_path)

        # A dictionary containing all paths which need to be created for the test
        source_dir_name = 'test_source/'
        dest_dir_name = 'test_dest/'
        log_dir_name = 'test_logs/'

        test_dirs = {
            'source': os.path.join(current_running_dir, source_dir_name),
            'dest': os.path.join(current_running_dir, dest_dir_name),
            'log': os.path.join(current_running_dir, log_dir_name),
        }

        root_script_dir = os.path.dirname(current_running_dir)
        command_path = os.path.abspath(os.path.join(root_script_dir,
                                                    'sanitise-and-move.py'
        ))

        #Construct a list to run the sanitisePaths command using Popen
        minimal_command = [command_path,
                                '-t', test_dirs['source'],
                                '-p', test_dirs['dest'],
                                '-r', os.path.join(test_dirs['log'],'renamed'),
                                '-l', os.path.join(test_dirs['log'], 'syslogs')
                                ]

        useful_vars = dict(current_running_dir=current_running_dir,
                           test_dirs=test_dirs,
                           minimal_command=minimal_command,
        )

        return useful_vars

    def make_dir_if_not_exists(self, dir):
        try:
            os.mkdir(dir)
        except OSError as e:
            error_number = e[0]
            if error_number == 17:  # File exists
                pass
            else:
                raise

    def create_dir_structure(self, test_dirs):
        for d_name in test_dirs:
            self.make_dir_if_not_exists(test_dirs[d_name])
        for d in ['.Hidden', 'To Archive', 'Problem Files', 'Logs']:
            self.make_dir_if_not_exists(os.path.join(test_dirs['source'], d))
        for d in ['syslogs','renamed']:
            self.make_dir_if_not_exists(os.path.join(test_dirs['log'], d))

    # SCRIPT NEEDS TO:
    # Not transfer single files from To Archive
    def test_do_not_move_files_not_in_a_directory(self):
        init_vars = self.init_vars()
        td = init_vars['test_dirs']
        orphan_file_path = os.path.join(td['source'],'To Archive', 'orphan.txt')
        with open(orphan_file_path, 'w') as orphan_file:
            orphan_file.write("NO MOVEY FILEY")

        sp.call(init_vars['minimal_command'])

        assert os.path.exists(orphan_file_path)
        assert not os.path.exists(os.path.join(td['dest'], 'orphan.txt'))
        assert not os.listdir(os.path.join(td['source'], 'Logs'))

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