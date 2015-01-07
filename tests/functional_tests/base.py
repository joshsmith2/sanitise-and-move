#!/usr/bin/python

import unittest
import os
import inspect
from sanitiseandmove import *

def make_dir_if_not_exists(dir):
    try:
        os.mkdir(dir)
    except OSError as e:
        error_number = e[0]
        if error_number == 17:  # File exists
            pass
        else:
            raise

def exists_in(container, content):
    os.path.exists(os.path.join(container, content))

class FunctionalTest(unittest.TestCase):


    def setUp(self):

        # Get the path of this script, and its containing directory (the test dir).
        self.script_path = os.path.abspath(inspect.stack()[0][1])
        self.functional_tests_dir = os.path.dirname(self.script_path)
        self.tests_dir = os.path.dirname(self.functional_tests_dir)
        self.root_dir = os.path.dirname(self.tests_dir)

        self.create_folders()

        self.command_path = os.path.abspath(os.path.join(self.root_dir,
                                                         'sanitiseandmove.py'
        ))

        #Construct a list to run the sanitisePaths command using Popen
        self.minimal_command = [self.command_path,
                               '-q',
                               '-t', os.path.abspath(self.source),
                               '-p', self.dest,
                               '-r', self.log_renamed,
                               '-l', self.log_syslog,]
        self.rename_command = self.minimal_command[:]
        self.rename_command.append('-d')

    def create_folders(self):
        # SOURCE:
        self.source = os.path.join(self.tests_dir, 'test_source')
        make_dir_if_not_exists(self.source)

        # Set up source subfolders and create them
        self.to_archive = os.path.join(self.source, 'To Archive')
        self.hidden = os.path.join(self.source, '.Hidden')
        self.logs = os.path.join(self.source, 'Logs')
        self.problem_files = os.path.join(self.source, 'Problem Files')
        make_dir_if_not_exists(self.to_archive)
        make_dir_if_not_exists(self.hidden)
        make_dir_if_not_exists(self.logs)
        make_dir_if_not_exists(self.problem_files)

        # DEST:
        self.dest = os.path.join(self.tests_dir, 'test_dest') # Local
        #self.dest = "/Volumes/HGSL-Archive/josh_test/test-dest" # Remote
        make_dir_if_not_exists(self.dest)

        # LOGS:
        # Create log folder
        self.log = os.path.join(self.tests_dir, 'test_logs')
        make_dir_if_not_exists(self.log)

        # Create log subfolders
        self.log_syslog = os.path.join(self.log, 'syslogs')
        self.log_renamed = os.path.join(self.log, 'renamed')
        make_dir_if_not_exists(self.log_syslog)
        make_dir_if_not_exists(self.log_renamed)


    def tearDown(self):
        for dir in [self.log, self.dest, self.source]:
            try:
                shutil.rmtree(dir)
            except OSError as e:
                error_number = e[0]
                if error_number == 2: #File doesn't exist
                    pass
                else:
                    print str(e)
                    raise
        # Remove pidfile
        pid = os.path.join('/tmp', self.source.replace('/','') + ".pid")
        if os.path.exists(pid):
            os.remove(pid)


    def check_in_logs(self, folder, messages):
        self.get_log_contents(folder)
        for m in messages:
            self.assertTrue(m in '\n'.join(self.log_contents))

    def minimal_object(self):
        """Create and return a sanitisation object which will work, with
        minimal, default arguments."""
        return Sanitisation(self.dest,
                            target=self.source,
                            rename_log_dir=self.log_renamed,
                            logstash_dir = self.log_syslog,
                            rename=True,
                            test_suite=True,
                            )

    def in_problem_files(self, folder):
        folder_in_pf = False
        problem_dir = os.path.join(self.problem_files, folder)
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
        for log_file in os.listdir(os.path.join(self.logs, folder_name)):
            log_path = os.path.join(self.logs, folder_name, log_file)
            with open(log_path, 'r') as lp:
                self.log_contents = lp.readlines()

if __name__ == '__main__':
    unittest.main()