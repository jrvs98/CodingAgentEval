import contextlib
import io
import os
import tempfile
import unittest

from notes_cli import cli


class TestCli(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        os.remove(self.path)

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)

    def _run(self, args):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = cli.run(["--file", self.path] + args)
        return code, buf.getvalue()

    def test_add_and_list(self):
        code, out = self._run(["add", "--title", "Hello", "--body", "World"])
        self.assertEqual(code, 0)
        self.assertIn("Added note 1", out)

        code, out = self._run(["list"])
        self.assertEqual(code, 0)
        self.assertIn("Hello", out)

    def test_delete(self):
        self._run(["add", "--title", "Hello", "--body", "World"])
        code, out = self._run(["delete", "1"])
        self.assertEqual(code, 0)
        self.assertIn("Deleted", out)

    def test_delete_missing(self):
        code, out = self._run(["delete", "42"])
        self.assertEqual(code, 1)
        self.assertIn("Not found", out)

    def test_search(self):
        self._run(["add", "--title", "Roadmap", "--body", "Q3 plan"])
        code, out = self._run(["search", "Roadmap"])
        self.assertEqual(code, 0)
        self.assertIn("Roadmap", out)


if __name__ == "__main__":
    unittest.main()
