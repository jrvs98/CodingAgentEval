import os
import tempfile
import unittest

from notes_cli import storage


class TestStorage(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        os.remove(self.path)  # start from "file does not exist"

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)

    def test_load_notes_missing_file_returns_empty(self):
        self.assertEqual(storage.load_notes(self.path), [])

    def test_add_note_assigns_incrementing_ids(self):
        n1 = storage.add_note(self.path, "First", "Body one")
        n2 = storage.add_note(self.path, "Second", "Body two")
        self.assertEqual(n1.id, 1)
        self.assertEqual(n2.id, 2)

    def test_add_note_persists_to_disk(self):
        storage.add_note(self.path, "Title", "Body", tags=["a", "b"])
        notes = storage.load_notes(self.path)
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0].title, "Title")
        self.assertEqual(notes[0].tags, ["a", "b"])

    def test_delete_note_removes_correct_note(self):
        n1 = storage.add_note(self.path, "First", "Body one")
        storage.add_note(self.path, "Second", "Body two")
        removed = storage.delete_note(self.path, n1.id)
        self.assertTrue(removed)
        remaining = storage.load_notes(self.path)
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0].title, "Second")

    def test_delete_note_missing_id_returns_false(self):
        storage.add_note(self.path, "First", "Body one")
        self.assertFalse(storage.delete_note(self.path, 999))

    def test_search_notes_finds_matching_title(self):
        storage.add_note(self.path, "Grocery list", "milk, eggs")
        storage.add_note(self.path, "Meeting notes", "discuss roadmap")
        results = storage.search_notes(self.path, "Grocery")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Grocery list")

    def test_search_notes_finds_matching_body(self):
        storage.add_note(self.path, "Grocery list", "milk, eggs")
        results = storage.search_notes(self.path, "eggs")
        self.assertEqual(len(results), 1)

    def test_list_notes_returns_all_notes(self):
        storage.add_note(self.path, "A", "a body")
        storage.add_note(self.path, "B", "b body")
        storage.add_note(self.path, "C", "c body")
        notes = storage.list_notes(self.path)
        self.assertEqual(len(notes), 3)


if __name__ == "__main__":
    unittest.main()
