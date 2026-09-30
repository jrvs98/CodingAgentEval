import os
import tempfile
import unittest

from sales_report.loader import load_transactions


class AdversarialLoaderValidationTest(unittest.TestCase):
    def test_unknown_transaction_type_is_rejected(self):
        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        try:
            with open(path, "w") as stream:
                stream.write("date,category,product,amount,type\n2026-01-01,Tools,Hammer,10,chargeback\n")
            with self.assertRaisesRegex(ValueError, "type"):
                load_transactions(path)
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()