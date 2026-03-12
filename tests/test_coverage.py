import unittest

from crime_map.coverage import (
    CURRENT_AGGREGATE_LABEL,
    coverage_payload,
    get_supported_municipality_names,
)


class CoverageTests(unittest.TestCase):
    def test_supported_municipalities_match_current_app_scope(self) -> None:
        self.assertEqual(
            get_supported_municipality_names(),
            ["All Metro", "Belmont", "Boston", "Cambridge", "Reading", "Somerville"],
        )

    def test_coverage_payload_exposes_current_aggregate_label(self) -> None:
        payload = coverage_payload()
        self.assertEqual(payload["current_aggregate_label"], CURRENT_AGGREGATE_LABEL)
        self.assertEqual(payload["current_aggregate_members"], ["Boston", "Cambridge", "Somerville"])


if __name__ == "__main__":
    unittest.main()
