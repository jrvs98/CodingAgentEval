import contextlib
import io
import os
import tempfile
import unittest

from sales_report import cli


class AdversarialDateValidationTest(unittest.TestCase):
    def test_cli_rejects_bad_dates_and_reversed_ranges(self):
        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        try:
            with open(path, "w") as stream:
                stream.write("date,category,product,amount,type\n2026-01-01,Tools,Hammer,10,sale\n")
            for args in ((path, "--start", "not-a-date"), (path, "--start", "2026-02-01", "--end", "2026-01-01")):
                with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as raised:
                    cli.main(list(args))
                self.assertNotEqual(raised.exception.code, 0)
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()