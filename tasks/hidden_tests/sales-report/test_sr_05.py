import contextlib
import io
import os
import tempfile
import unittest

from sales_report import cli


class TestDateRangeFilter(unittest.TestCase):
    def setUp(self):
        fd, self.csv_path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        with open(self.csv_path, "w") as f:
            f.write("date,category,product,amount,type\n")
            f.write("2026-01-01,Tools,Hammer,25.00,sale\n")
            f.write("2026-02-01,Tools,Wrench,15.00,sale\n")
            f.write("2026-03-01,Kitchen,Blender,40.00,sale\n")

    def tearDown(self):
        if os.path.exists(self.csv_path):
            os.remove(self.csv_path)

    def test_start_and_end_restrict_transactions(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cli.main([self.csv_path, "--start", "2026-02-01", "--end", "2026-02-28"])
        out = buf.getvalue()
        self.assertIn("Tools: $15.00", out)
        self.assertNotIn("Kitchen", out)


if __name__ == "__main__":
    unittest.main()
