import os
import tempfile
import unittest

from notes_cli import storage


class TestSearchCaseInsensitive(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        os.remove(self.path)

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)

    def test_search_matches_regardless_of_case_in_title(self):
        storage.add_note(self.path, "Roadmap Q3", "some body")
        self.assertEqual(len(storage.search_notes(self.path, "roadmap")), 1)
        self.assertEqual(len(storage.search_notes(self.path, "ROADMAP")), 1)

    def test_search_matches_regardless_of_case_in_body(self):
        storage.add_note(self.path, "Notes", "Discuss ROADMAP next")
        self.assertEqual(len(storage.search_notes(self.path, "roadmap")), 1)


if __name__ == "__main__":
    unittest.main()
