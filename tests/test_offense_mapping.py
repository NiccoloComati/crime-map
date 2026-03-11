import unittest

from crime_map.offense_mapping import (
    MACRO_CATEGORY_ORDER,
    PERSONAL_FAMILY_PROTECTIVE,
    PROPERTY_CRIME,
    PUBLIC_ORDER_WEAPONS,
    SERVICE_ADMINISTRATIVE,
    VIOLENT_CRIME,
    FRAUD_FINANCIAL_CRIME,
    classify_offense_label,
    macro_sort_key,
)


class OffenseMappingTests(unittest.TestCase):
    def test_cambridge_commercial_robbery_is_violent(self) -> None:
        self.assertEqual(classify_offense_label("Cambridge", "Commercial Robbery").macro, VIOLENT_CRIME)

    def test_cambridge_larceny_of_services_stays_property(self) -> None:
        self.assertEqual(classify_offense_label("Cambridge", "Larceny of Services").macro, PROPERTY_CRIME)

    def test_boston_property_found_is_service(self) -> None:
        self.assertEqual(
            classify_offense_label("Boston", "Property - Found").macro,
            SERVICE_ADMINISTRATIVE,
        )

    def test_boston_assault_simple_is_personal_family(self) -> None:
        self.assertEqual(
            classify_offense_label("Boston", "Assault - Simple").macro,
            PERSONAL_FAMILY_PROTECTIVE,
        )

    def test_boston_weapon_violation_is_public_order_weapons(self) -> None:
        self.assertEqual(
            classify_offense_label(
                "Boston",
                "Weapon Violation - Carry/ Possessing/ Sale/ Trafficking/ Other",
            ).macro,
            PUBLIC_ORDER_WEAPONS,
        )

    def test_somerville_identity_theft_is_financial(self) -> None:
        self.assertEqual(
            classify_offense_label("Somerville", "Identity Theft").macro,
            FRAUD_FINANCIAL_CRIME,
        )

    def test_macro_order_keeps_violent_before_service(self) -> None:
        ordered = sorted(
            [SERVICE_ADMINISTRATIVE, PROPERTY_CRIME, VIOLENT_CRIME],
            key=macro_sort_key,
        )
        self.assertEqual(ordered, [VIOLENT_CRIME, PROPERTY_CRIME, SERVICE_ADMINISTRATIVE])

    def test_macro_order_constant_starts_with_violent_and_property(self) -> None:
        self.assertEqual(MACRO_CATEGORY_ORDER[:2], [VIOLENT_CRIME, PROPERTY_CRIME])


if __name__ == "__main__":
    unittest.main()
