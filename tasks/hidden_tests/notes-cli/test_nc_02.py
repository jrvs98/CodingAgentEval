import os
import tempfile
import unittest

from notes_cli import storage


class TestUniqueIdsAfterDeletion(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        os.remove(self.path)

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)

    def test_id_not_reused_after_delete(self):
        n1 = storage.add_note(self.path, "First", "body")
        n2 = storage.add_note(self.path, "Second", "body")
        n3 = storage.add_note(self.path, "Third", "body")
        storage.delete_note(self.path, n1.id)
        n4 = storage.add_note(self.path, "Fourth", "body")

        ids = [n.id for n in storage.load_notes(self.path)]
        self.assertEqual(len(ids), len(set(ids)), f"duplicate ids found: {ids}")
        self.assertNotIn(n4.id, {n2.id, n3.id})


if __name__ == "__main__":
    unittest.main()
