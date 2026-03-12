import unittest

import pandas as pd

from crime_map.municipal_logs import (
    _parse_belmont_log_text,
    _parse_lexington_words,
    _parse_reading_log_text,
)


class MunicipalLogParsingTests(unittest.TestCase):
    def test_belmont_log_parser_extracts_date_and_type(self) -> None:
        text = """
        Incident #: 26003733 Date: 2026-03-02 09:58:31 Type: THEFT
        Location: 24 MAPLE ST
        """

        records = _parse_belmont_log_text(text)

        self.assertEqual(records, [(pd.Timestamp("2026-03-02"), "THEFT")])

    def test_reading_log_parser_extracts_header_blocks(self) -> None:
        text = """
        *** MON 07/07/2025 ASSAULT-SIMPLE *
        **********
        13:42 * 1 MAIN ST REA
        814000 * SOME DETAIL
        """

        records = _parse_reading_log_text(text)

        self.assertEqual(records, [(pd.Timestamp("2025-07-07"), "ASSAULT-SIMPLE")])

    def test_lexington_parser_keeps_wrapped_offense_text(self) -> None:
        words = [
            {"text": "26-001581", "x0": 16.416, "top": 162.0},
            {"text": "02/08/26", "x0": 74.52, "top": 162.0},
            {"text": "20:26", "x0": 115.07, "top": 162.0},
            {"text": "ALARM-NON", "x0": 154.224, "top": 162.0},
            {"text": "RESIDENT", "x0": 206.593, "top": 162.0},
            {"text": "&", "x0": 250.964, "top": 162.0},
            {"text": "HIGH", "x0": 259.579, "top": 162.0},
            {"text": "RISK", "x0": 154.224, "top": 171.5},
        ]

        records = _parse_lexington_words(words)

        self.assertEqual(records, [(pd.Timestamp("2026-02-08"), "ALARM-NON RESIDENT & HIGH RISK")])


if __name__ == "__main__":
    unittest.main()
