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

if __name__ == '__main__':
    unittest.main()
