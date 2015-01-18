#!/usr/bin/python

from base import *
import threading
import subprocess
import time

def destroy_mount(local_path):
    subprocess.Popen(['sudo', 'umount', '-f', local_path])

class RetryTransferTest(SanitiseTest):

    def test_the_right_number_of_retries_are_attempted_if_transfer_fails(self):
        transfer_event = threading.Event()
        test_dir_name = "test1"
        self.dest = '/Volumes/HGSL-Archive/josh_test'
        if os.path.exists(os.path.join(self.dest, test_dir_name)):
            try:
                shutil.rmtree(os.path.join(self.dest, test_dir_name))
            except:
                print "Oh dear. reosurce busy."

        self.make_test_folder(test_dir_name, 'test_file')
        large_file_source = os.path.join(self.tests_dir, 'test_file_1M')
        test_dir = os.path.join(self.to_archive, test_dir_name)
        large_file_dest = os.path.join(test_dir, 'test_file_large')
        shutil.copyfile(large_file_source, large_file_dest)

        s = self.minimal_object()
        s.started_transfer = transfer_event

        transfer_thread = threading.Thread(name='main', target=main, args=(s,))
        transfer_thread.start()
        transfer_event.wait(10)

        print "Dropping mount"
        destroy_mount(self.mount_path)
        # Wait 5s to drop mount
        seconds = 5
        check_frequency = 0.2
        no_of_checks = int(seconds / check_frequency)
        for i in range(no_of_checks):
            if os.path.exists(self.mount_path):
                time.sleep(check_frequency)
                if i == no_of_checks - 1:
                    self.fail("Mount failed to drop")

        self.assertFalse(os.path.exists(self.mount_path))

        transfer_thread.join()

        expected = ["A fatal error occurred while transferring:"]
        wrong = ["No transfer errors occurred"]
        self.check_in_logs(test_dir_name, expected)
        self.check_in_logs(test_dir_name, wrong, positive_test=False)
