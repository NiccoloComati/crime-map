import unittest

import pandas as pd

from crime_map.data import _parse_mixed_datetime


class DataParsingTests(unittest.TestCase):
    def test_parse_mixed_datetime_keeps_naive_and_utc_rows(self) -> None:
        values = pd.Series(
            [
                "2022-12-31 23:50:00",
                "2023-01-27 22:44:00+00",
                "",
            ]
        )

        parsed = _parse_mixed_datetime(values)

        self.assertEqual(parsed.iloc[0], pd.Timestamp("2022-12-31 23:50:00"))
        self.assertEqual(parsed.iloc[1], pd.Timestamp("2023-01-27 22:44:00"))
        self.assertTrue(pd.isna(parsed.iloc[2]))


if __name__ == "__main__":
    unittest.main()
