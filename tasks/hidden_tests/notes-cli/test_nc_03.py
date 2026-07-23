import os
import tempfile
import unittest

from notes_cli import storage


class TestSortBranches(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        os.remove(self.path)

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)

    def _add_with_date(self, title, body, created_at):
        note = storage.add_note(self.path, title, body)
        notes = storage.load_notes(self.path)
        for n in notes:
            if n.id == note.id:
                n.created_at = created_at
        storage.save_notes(self.path, notes)

    # Titles are alphabetically Alpha < Bravo < Charlie, but dates run in the
    # *opposite* order, so title-order and date-order can't be confused for
    # one another -- this is what actually catches the swapped branches.
    def test_sort_by_title_orders_alphabetically(self):
        self._add_with_date("Charlie", "b", "2026-01-01")
        self._add_with_date("Bravo", "b", "2026-02-01")
        self._add_with_date("Alpha", "b", "2026-03-01")

        titles = [n.title for n in storage.list_notes(self.path, sort_by="title")]
        self.assertEqual(titles, ["Alpha", "Bravo", "Charlie"])

    def test_sort_by_date_orders_chronologically(self):
        self._add_with_date("Charlie", "b", "2026-01-01")
        self._add_with_date("Bravo", "b", "2026-02-01")
        self._add_with_date("Alpha", "b", "2026-03-01")

        dates = [n.created_at for n in storage.list_notes(self.path, sort_by="date")]
        self.assertEqual(dates, ["2026-01-01", "2026-02-01", "2026-03-01"])


if __name__ == "__main__":
    unittest.main()
