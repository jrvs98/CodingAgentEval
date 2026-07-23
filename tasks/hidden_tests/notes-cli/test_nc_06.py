import contextlib
import csv
import io
import os
import tempfile
import unittest

from notes_cli import storage, cli


class TestExportCsv(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        os.remove(self.path)
        fd2, self.csv_path = tempfile.mkstemp(suffix=".csv")
        os.close(fd2)
        os.remove(self.csv_path)

    def tearDown(self):
        for p in (self.path, self.csv_path):
            if os.path.exists(p):
                os.remove(p)

    def test_export_writes_expected_csv(self):
        storage.add_note(self.path, "Title A", "Body A", tags=["work", "urgent"])
        storage.add_note(self.path, "Title B", "Body B", tags=[])

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = cli.run(["--file", self.path, "export", self.csv_path])
        self.assertEqual(code, 0)
        self.assertTrue(os.path.exists(self.csv_path))

        with open(self.csv_path, newline="") as f:
            rows = list(csv.DictReader(f))

        self.assertEqual(set(rows[0].keys()), {"id", "title", "body", "tags", "created_at"})
        self.assertEqual(len(rows), 2)
        row_a = next(r for r in rows if r["title"] == "Title A")
        self.assertEqual(row_a["tags"], "work;urgent")
        row_b = next(r for r in rows if r["title"] == "Title B")
        self.assertEqual(row_b["tags"], "")


if __name__ == "__main__":
    unittest.main()
