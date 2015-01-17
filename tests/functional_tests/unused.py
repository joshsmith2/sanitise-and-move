# Half written before os.path.exists epiphany. Might still come in handy

def test_do_not_move_resource_forks_if_not_set(self):
    fork_source = os.path.join(self.to_archive, 'forks')
    fork_container = os.path.join(fork_source, 'container')
    os.mkdir(fork_source)
    os.mkdir(fork_container)
    resource_files = ['._a.pdf', 'container/._hungbad.panc', '._.DS_Store']
    standard_files = ['a.pdf', 'container/gran._bag', 'pumpup._',]
    rf_paths = [os.path.join(fork_source, rf) for rf in resource_files]
    st_paths = [os.path.join(fork_source, sf) for sf in standard_files]
    all_paths = [].extend(rf_paths).extend(st_paths)

    # Create all the files we're about to move
    for ap in all_paths:
        with open (ap, 'w') as f:
            f.write('a')

    s = self.minimal_object()


    # Check a script being run again won't interrupt it
#    def test_cannot_run_script_twice(self):
#        large_file = os.path.join(self.tests_dir, 'test_file_large')
#        dir_to_move_1 = os.path.join(self.to_archive, 'dir_1')
#        dir_to_move_2 = os.path.join(self.to_archive, 'dir_2')
#        os.mkdir(dir_to_move_1)
#        os.mkdir(dir_to_move_2)
#
#        shutil.copy(large_file, dir_to_move_1)
#        shutil.copy(large_file, dir_to_move_2)
#
#        self.assertTrue(os.path.exists(os.path.join(dir_to_move_1,
#                                                    'test_file_large')))
#        self.assertTrue(os.path.exists(os.path.join(dir_to_move_2,
#                                                    'test_file_large')))
#
#        # Set up threads
#        s1 = self.minimal_object()
#        s1.create_pid = True
#        thread_1 = threading.Thread(name='test_thread_1', target=main, args=(s1,))
#        s2 = self.minimal_object()
#        s2.create_pid = True
#        thread_2 = threading.Thread(name='test_thread_2', target=main, args=(s2,))
#
#        #Start threads and test
#        thread_1.start()
#        time.sleep(0.01)
#        self.assertTrue(os.path.exists(s1.pid_file))
#
#        self.assertTrue(thread_1.is_alive())
#        # Start a second thread while the first is running, check it
#        # complains about the pidfile, writes a log, and exits.
#        thread_2.start()
#        time.sleep(0.1)
#        self.assertFalse(thread_2.is_alive())
#        with open(self.temp_log, 'r') as f:
#            messages = ["Process with pid",
#                        "is currently running. Exiting now."]
#            for m in messages:
#                self.assertTrue(m in ['\n'.join(f.readlines())])
#        self.assertTrue(True)
#
#        s1.moved_to_hidden.wait()
#        self.assertTrue(exists_in(self.hidden, 'dir_1'))
#        self.assertFalse(exists_in(self.hidden, 'dir_2'))
#        self.assertTrue(exists_in(self.to_archive, 'dir_2'))
#        self.assertFalse(exists_in(self.to_archive, 'dir_1'))