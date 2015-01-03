#!/usr/bin/python

import unittest
import os
import inspect
from sanitiseandmove import *

class FunctionalTest(unittest.TestCase):

    def setUp(self):
        # Variables
        self.current_path = os.path.abspath(inspect.stack()[0][1])
        self.current_dir = os.path.dirname(self.current_path)
        self.test_dir = os.path.dirname(self.current_dir)

        # A dictionary containing all paths which need to be created for the test
        self.source_dir_name = 'test_source'
        self.dest_dir_name = 'test_dest'
        self.log_dir_name = 'test_logs'

        self.source = self.source_dir_name

        self.dest = os.path.join(self.test_dir, self.dest_dir_name) # Local

        #self.dest = os.path.join("/Volumes/HGSL-Archive/josh_test/",
        #                         self.dest_dir_name)

        self.log = os.path.join(self.test_dir, self.log_dir_name)
        self.rootdirs = [self.source, self.log, self.dest]

        self.source_subfolders = ['.Hidden', 'To Archive', 'Problem Files', 'Logs']
        self.log_subfolders = ['syslogs','renamed']

        self.root_script_dir = os.path.join(self.test_dir, '..')
        self.command_path = os.path.abspath(os.path.join(self.root_script_dir,
                                                         'sanitiseandmove.py'
        ))
        self.rename_log_dir = os.path.join(self.log, 'renamed')
        self.syslog_dir = os.path.join(self.log, 'syslogs')

        #Construct a list to run the sanitisePaths command using Popen
        self.minimal_command = [self.command_path,
                               '-q',
                               '-t', os.path.abspath(self.source),
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

if __name__ == '__main__':
    unittest.main()