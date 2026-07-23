import contextlib
import io
import os
import tempfile
import unittest

from notes_cli import storage, cli


class TestTagFilter(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        os.remove(self.path)

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)

    def test_list_notes_filters_by_tag(self):
        storage.add_note(self.path, "A", "body", tags=["work"])
        storage.add_note(self.path, "B", "body", tags=["personal"])
        storage.add_note(self.path, "C", "body", tags=["work", "urgent"])

        results = storage.list_notes(self.path, tag="work")
        titles = sorted(n.title for n in results)
        self.assertEqual(titles, ["A", "C"])

    def test_list_notes_without_tag_returns_all(self):
        storage.add_note(self.path, "A", "body", tags=["work"])
        storage.add_note(self.path, "B", "body", tags=["personal"])
        results = storage.list_notes(self.path)
        self.assertEqual(len(results), 2)

    def test_cli_list_with_tag_flag(self):
        storage.add_note(self.path, "A", "body", tags=["work"])
        storage.add_note(self.path, "B", "body", tags=["personal"])

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cli.run(["--file", self.path, "list", "--tag", "work"])
        out = buf.getvalue()
        self.assertIn("A", out)
        self.assertNotIn("B", out)


if __name__ == "__main__":
    unittest.main()
