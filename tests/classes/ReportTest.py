import sqlite3
import unittest
from zsis.classes.Report import Report
from tests.stubs.CursorStub import CursorStub


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.report = Report()

    def test_update_with(self):
        cursor = CursorStub()

        expected_files_scanned = 0
        expected_sourceables_added = 0
        expected_color_hashes_added = 0
        expected_sources_added = 0

        def check_in():
            self.assertEqual(self.report.files_scanned, expected_files_scanned)
            self.assertEqual(self.report.sourceables_added, expected_sourceables_added)
            self.assertEqual(self.report.color_hashes_added, expected_color_hashes_added)
            self.assertEqual(self.report.sources_added, expected_sources_added)

        check_in()

        self.report.update_with(None, None, [])
        expected_files_scanned += 1
        check_in()

        self.report.update_with(cursor, None, [])
        expected_files_scanned += 1
        expected_sourceables_added += 1
        check_in()

        self.report.update_with(None, cursor, [])
        expected_files_scanned += 1
        expected_color_hashes_added += 1
        check_in()

    def test_str(self):
        def change_values(files_scanned, sourceables_added, color_hashes_added, sources_added):
            self.report.files_scanned = files_scanned
            self.report.sourceables_added = sourceables_added
            self.report.color_hashes_added = color_hashes_added
            self.report.sources_added = sources_added

        change_values(0, 0, 0, 0)
        self.assertEqual(str(self.report), "Scanned 0 files: No changes.")
        change_values(1, 0, 0, 0)
        self.assertEqual(str(self.report), "Scanned 1 files: No changes.")
        change_values(0, 1, 0, 0)
        self.assertEqual(str(self.report), "Scanned 0 files: Added 1 sourcable(s).")
        change_values(0, 0, 1, 0)
        self.assertEqual(str(self.report), "Scanned 0 files: Added 1 color hash(es).")
        change_values(0, 0, 0, 1)
        self.assertEqual(str(self.report), "Scanned 0 files: Added 1 source(s).")
        change_values(1, 2, 3, 4)
        self.assertEqual(str(self.report), "Scanned 1 files: Added 2 sourcable(s), 3 color hash(es), 4 source(s).")


if __name__ == '__main__':
    unittest.main()
