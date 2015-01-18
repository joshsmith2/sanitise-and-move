#!/usr/bin/python

from base import *
import threading
import subprocess

def destroy_mount(local_path):
    subprocess.Popen(['sudo', 'umount', '-f', local_path])

class RetryTransferTest(FunctionalTest):

    def test_the_right_number_of_retries_are_attempted_if_transfer_fails(self):
        self.make_test_folder('test_dir', 'test_file')
        s = self.minimal_object()
        s.pass_dir = "/tmp/does/not/exist"


        transfer_thread = threading.Thread(name='main', target=main(s))
        transfer_thread.start()

#        destroy_mount(self.mount_path)
#        self.assertFalse(os.path.exists(self.mount_path))
        expected = ("An error occured when moving some files to")
        self.check_in_logs('test_dir', expected)

