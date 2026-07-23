import contextlib
import io
import os
import tempfile
import unittest

from notes_cli import storage, cli


class TestArchive(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        os.remove(self.path)

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)

    def test_archived_note_excluded_by_default(self):
        storage.add_note(self.path, "Keep", "body")
        n2 = storage.add_note(self.path, "Archive me", "body")
        storage.archive_note(self.path, n2.id)

        titles = [n.title for n in storage.list_notes(self.path)]
        self.assertIn("Keep", titles)
        self.assertNotIn("Archive me", titles)

    def test_archived_note_included_with_include_archived(self):
        storage.add_note(self.path, "Keep", "body")
        n2 = storage.add_note(self.path, "Archive me", "body")
        storage.archive_note(self.path, n2.id)

        titles = [n.title for n in storage.list_notes(self.path, include_archived=True)]
        self.assertIn("Archive me", titles)

    def test_unarchive_restores_visibility(self):
        n1 = storage.add_note(self.path, "Note", "body")
        storage.archive_note(self.path, n1.id)
        storage.unarchive_note(self.path, n1.id)
        self.assertEqual(len(storage.list_notes(self.path)), 1)

    def test_cli_archive_and_list_all(self):
        n1 = storage.add_note(self.path, "Note", "body")

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cli.run(["--file", self.path, "archive", str(n1.id)])

        buf2 = io.StringIO()
        with contextlib.redirect_stdout(buf2):
            cli.run(["--file", self.path, "list"])
        self.assertNotIn("Note", buf2.getvalue())

        buf3 = io.StringIO()
        with contextlib.redirect_stdout(buf3):
            cli.run(["--file", self.path, "list", "--all"])
        self.assertIn("Note", buf3.getvalue())


if __name__ == "__main__":
    unittest.main()
