#!/usr/bin/python

from base import *
import unittest

class PickUpProjectsTest(SanitiseTest):

    def test_only_one_project_picked_up_at_a_single_run(self):
        project_1 = os.path.join(self.to_archive, "p1")
        project_2 = os.path.join(self.to_archive, "p2")
        os.mkdir(project_1)
        os.mkdir(project_2)

        s = self.minimal_object()
        main(s)

        self.assertTrue(os.path.exists(project_2))

    def test_exits_gracefully_if_no_files_to_move(self):
        s=self.minimal_object()
        main(s)
        # Check no logs

class RemoveUnwantedFilesTest(SanitiseTest):

    def test_DS_Store_files_deleted(self):
        source_dir = os.path.join(self.to_archive, 'moveme')
        ds_source = os.path.join(source_dir, '.DS_Store')
        ds_dest = os.path.join(self.dest, 'moveme', '.DS_Store')

        os.mkdir(source_dir)
        with open(ds_source, 'w') as ds:
            ds.write('dot')

        s = self.minimal_object()
        main(s)

        self.assertFalse(os.path.exists(ds_dest))

    def test_resource_forks_get_deleted_from_source_when_dest_exists(self):
        def create_files(list, path):
            for f in list:
                full_path = os.path.join(path, f)
                with open(full_path, 'w') as wf:
                    wf.write("PUN BANGLE, CRAN HANDLE, PIN TINGLE, CRIMBAFFLE")

        source_dir = os.path.join(self.to_archive, 'movemetoo')
        dest_dir = os.path.join(self.dest, 'movemetoo')
        good_files = ['file1.txt', 'a._file._bum']
        bad_files = ['._file1.txt', '._', '._DS_Store']

        os.mkdir(source_dir)
        os.mkdir(dest_dir)
        create_files(good_files, source_dir)
        create_files(bad_files, source_dir)

        s = self.minimal_object()
        main(s)

        for gf in good_files:
            self.assertTrue(os.path.exists(os.path.join(dest_dir, gf)))
        for bf in bad_files:
            self.assertFalse(os.path.exists(os.path.join(dest_dir, bf)))
        expected = ["3 resource forks deleted.",
                    "The following files transferred successfully:"]
        expected.extend(good_files)
        self.check_in_logs('moveme', expected)



if __name__ == '__main__':
    unittest.main()
