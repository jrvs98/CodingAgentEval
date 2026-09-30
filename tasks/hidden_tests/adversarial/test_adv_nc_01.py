import os
import tempfile
import unittest

from notes_cli import storage


class AdversarialTagFilterTest(unittest.TestCase):
    def test_tag_filter_is_case_insensitive_and_hides_archived_notes(self):
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        os.remove(path)
        try:
            active = storage.add_note(path, "Active", "body", tags=["work"])
            archived = storage.add_note(path, "Archived", "body", tags=["Work"])
            storage.archive_note(path, archived.id)
            notes = storage.list_notes(path, tag="WORK")
            self.assertEqual([note.id for note in notes], [active.id])
            self.assertEqual(storage.list_notes(path, tag="WORK", include_archived=True), [active, archived])
        finally:
            for candidate in (path, path + ".next-id"):
                if os.path.exists(candidate):
                    os.remove(candidate)


if __name__ == "__main__":
    unittest.main()