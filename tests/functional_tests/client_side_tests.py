from base import *
import unittest

class PickUpProjectsTest(FunctionalTest):

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