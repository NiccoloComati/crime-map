from __future__ import annotations

from dataclasses import dataclass
import re

import pandas as pd

VIOLENT_CRIME = "Violent Crime"
PROPERTY_CRIME = "Property Crime"
DRUG_VICE_OFFENSE = "Drug & Vice Offense"
FRAUD_FINANCIAL_CRIME = "Fraud & Financial Crime"
PUBLIC_ORDER_WEAPONS = "Public Order & Weapons"
TRAFFIC_OUI = "Traffic & OUI"
PERSONAL_FAMILY_PROTECTIVE = "Personal / Family / Protective"
SERVICE_ADMINISTRATIVE = "Service / Administrative"

MACRO_CATEGORY_ORDER = [
    VIOLENT_CRIME,
    PROPERTY_CRIME,
    DRUG_VICE_OFFENSE,
    FRAUD_FINANCIAL_CRIME,
    PUBLIC_ORDER_WEAPONS,
    TRAFFIC_OUI,
    PERSONAL_FAMILY_PROTECTIVE,
    SERVICE_ADMINISTRATIVE,
]
_MACRO_ORDER_INDEX = {macro: index for index, macro in enumerate(MACRO_CATEGORY_ORDER)}


@dataclass(frozen=True)
class OffenseGroupDefinition:
    label: str
    macro: str
    benchmark_family: str | None = None


OFFENSE_GROUPS: dict[str, OffenseGroupDefinition] = {
    "homicide": OffenseGroupDefinition("Homicide", VIOLENT_CRIME, benchmark_family="violent_crime"),
    "sexual_assault": OffenseGroupDefinition("Sexual Assault", VIOLENT_CRIME, benchmark_family="violent_crime"),
    "robbery": OffenseGroupDefinition("Robbery", VIOLENT_CRIME, benchmark_family="violent_crime"),
    "aggravated_assault": OffenseGroupDefinition(
        "Aggravated Assault", VIOLENT_CRIME, benchmark_family="violent_crime"
    ),
    "kidnapping_trafficking": OffenseGroupDefinition("Kidnapping / Trafficking", VIOLENT_CRIME),
    "personal_assault_harassment": OffenseGroupDefinition(
        "Personal Assault / Harassment", PERSONAL_FAMILY_PROTECTIVE
    ),
    "family_protective": OffenseGroupDefinition("Family / Protective", PERSONAL_FAMILY_PROTECTIVE),
    "burglary_breaking": OffenseGroupDefinition("Burglary / Breaking & Entering", PROPERTY_CRIME),
    "larceny_theft": OffenseGroupDefinition("Larceny / Theft", PROPERTY_CRIME, benchmark_family="property_crime"),
    "motor_vehicle_theft": OffenseGroupDefinition(
        "Motor Vehicle Theft", PROPERTY_CRIME, benchmark_family="property_crime"
    ),
    "arson": OffenseGroupDefinition("Arson", PROPERTY_CRIME, benchmark_family="property_crime"),
    "property_damage": OffenseGroupDefinition("Property Damage", PROPERTY_CRIME),
    "stolen_property": OffenseGroupDefinition("Stolen Property", PROPERTY_CRIME),
    "drug_narcotic": OffenseGroupDefinition("Drug / Narcotic", DRUG_VICE_OFFENSE, benchmark_family="drug_offense"),
    "vice_obscenity": OffenseGroupDefinition("Vice / Obscenity", DRUG_VICE_OFFENSE),
    "fraud_financial": OffenseGroupDefinition("Fraud / Financial", FRAUD_FINANCIAL_CRIME),
    "public_order": OffenseGroupDefinition("Public Order", PUBLIC_ORDER_WEAPONS),
    "weapons": OffenseGroupDefinition("Weapons", PUBLIC_ORDER_WEAPONS),
    "traffic_oui": OffenseGroupDefinition("Traffic / OUI", TRAFFIC_OUI),
    "service_admin": OffenseGroupDefinition("Service / Administrative", SERVICE_ADMINISTRATIVE),
}

_SPACE_RE = re.compile(r"\s+")


def normalize_offense_label(label: str | None) -> str:
    if label is None:
        return ""
    cleaned = str(label).replace("\xa0", " ")
    return _SPACE_RE.sub(" ", cleaned).strip().casefold()


def _build_city_overrides(group_code: str, labels: list[str]) -> dict[str, str]:
    return {normalize_offense_label(label): group_code for label in labels}


CITY_OFFENSE_GROUP_OVERRIDES: dict[str, dict[str, str]] = {
    "cambridge": {
        **_build_city_overrides(
            "service_admin",
            ["Civil Dispute", "Elder Assistance/19A", "Encampment", "Hoarding", "Medical", "Missing Person", "Warrant Arrest"],
        ),
        **_build_city_overrides("larceny_theft", ["Larceny of Services"]),
        **_build_city_overrides("property_damage", ["Mal. Dest. Property"]),
        **_build_city_overrides("stolen_property", ["Rec. Stol. Property"]),
        **_build_city_overrides("public_order", ["Liquor Possession/Sale"]),
    },
    "boston": {
        **_build_city_overrides(
            "service_admin",
            [
                "Auto Theft - Outside - Recovered In Boston",
                "Auto Theft - Recovered In By Police",
                "Biological Threats",
                "Dangerous Or Hazardous Condition",
                "Evidence Tracker Incidents",
                "Injury Bicycle No M/V Involved",
                "Investigate Person",
                "Investigate Property",
                "Investigation For Another Agency",
                "Landlord - Tenant",
                "Landlord - Tenant Service",
                "Medical Assistance",
                "Missing Person",
                "Missing Person - Located",
                "Missing Person - Not Reported - Located",
                "Police Service Incidents",
                "Prisoner - Suicide / Suicide Attempt",
                "Prisoner Attempt To Rescue",
                "Prisoner Escape / Escape & Recapture",
                "Property - Accidental Damage",
                "Property - Found",
                "Property - Lost",
                "Property - Lost Then Located",
                "Property - Lost/ Missing",
                "Property - Missing",
                "Property - Stolen Then Recovered",
                "Protective Custody / Safekeeping",
                "Recovered - Mv Recovered In Boston (Stolen In Boston) Must Be Supplemental",
                "Recovered - Mv Recovered In Boston (Stolen Outside Boston)",
                "Recovered Stolen Plate",
                "Report Affecting Other Depts.",
                "Search Warrant",
                "Search Warrants",
                "Service To Other Agency",
                "Service To Other Pd Inside Of Ma.",
                "Service To Other Pd Outside Of Ma.",
                "Sick Assist",
                "Sick/Injured/Medical - Person",
                "Sick/Injured/Medical - Police",
                "Sudden Death",
                "Suicide / Suicide Attempt",
                "Towed Motor Vehicle",
                "Towed",
                "Truancy / Runaway",
                "Warrant Arrest",
                "Warrant Arrest - Boston Warrant (Must Be Supplemental)",
                "Warrant Arrest - Outside Of Boston Warrant",
            ],
        ),
        **_build_city_overrides(
            "vice_obscenity",
            [
                "Obscene Materials - Pornography",
                "Prostitute - Common Nightwalker",
                "Prostitution",
                "Prostitution - Assisting Or Promoting",
                "Prostitution - Common Nightwalker",
                "Prostitution - Soliciting",
            ],
        ),
        **_build_city_overrides(
            "family_protective",
            [
                "Child Abandonment (No Assault)",
                "Child Abuse",
                "Child Endangerment",
                "Child Endangerment (No Assault)",
                "Contributing To Delinquency Of Minor",
                "Failure To Register As A Sex Offender",
                "Harassment",
                "Harassment/ Criminal Harassment",
                "Offenses Against Child / Family",
                "Sex Offender Registration",
                "Sex Offense - Other",
                "Threats To Do Bodily Harm",
                "Viol. Of Restraining Order W Arrest",
                "Viol. Of Restraining Order W No Arrest",
                "Violation - Harassment Prevention Order",
                "Violation - Restraining Order",
                "Violation - Restraining Order (No Arrest)",
            ],
        ),
        **_build_city_overrides(
            "service_admin",
            [
                "Animal Abuse",
                "Animal Control - Dog Bites - Etc.",
                "Animal Incidents",
                "Animal Incidents (Dog Bites, Lost Dog, Etc)",
                "Aircraft Incidents",
                "Death Investigation",
                "Fire Report",
                "Fire Report - Car, Brush, Etc.",
                "Fire Report - House, Building, Etc.",
                "Fire Report/Alarm - False",
                "Fugitive From Justice",
                "Harbor Incident / Violation",
                "Missing Person Reported",
                "Other",
                "Other Offense",
                "Violations",
            ],
        ),
        **_build_city_overrides("weapons", ["Ballistics Evidence/Found", "Firearm/Weapon - Found Or Confiscated"]),
        **_build_city_overrides("property_damage", ["Graffiti", "Vandalism"]),
        **_build_city_overrides(
            "stolen_property",
            [
                "Property - Concealing Leased",
                "Property - Receiving Stolen",
                "Stolen Property - Buying / Receiving / Possessing",
            ],
        ),
        **_build_city_overrides("public_order", ["Conspiracy Except Drug Law", "License Premise Violation", "License Violation"]),
        **_build_city_overrides("traffic_oui", ["M/V Plates - Lost"]),
        **_build_city_overrides("weapons", ["Firearm/Weapon - Accidental Injury / Death"]),
        **_build_city_overrides("family_protective", ["Assault - Simple", "Sexual Assault Investigation", "Sexual Assault Kit Collected"]),
    },
    "somerville": {
        **_build_city_overrides("fraud_financial", ["Identity Theft"]),
        **_build_city_overrides("service_admin", ["All Other Offenses"]),
    },
}


def macro_sort_key(value: str) -> tuple[int, str]:
    return (_MACRO_ORDER_INDEX.get(value, len(MACRO_CATEGORY_ORDER)), value)


def _contains_any(label: str, tokens: tuple[str, ...]) -> bool:
    return any(token in label for token in tokens)


def _classify_general_label(label: str) -> str:
    if not label:
        return "service_admin"

    if label.startswith("migrated report - "):
        return _classify_general_label(label.removeprefix("migrated report - ").strip())

    if _contains_any(
        label,
        (
            "investigate ",
            "investigation for another agency",
            "service",
            "search warrant",
            "missing person",
            "sick assist",
            "medical",
            "death investigation",
            "animal ",
            "aircraft",
            "landlord",
            "civil dispute",
            "elder assistance",
            "encampment",
            "hoarding",
            "suspicious package",
            "evidence tracker",
            "protective custody",
            "report affecting other depts",
            "prisoner",
            "fugitive from justice",
            "sudden death",
            "fire report",
            "harbor incident",
            "harbor related",
            "police service incidents",
            "recovered -",
        ),
    ):
        return "service_admin"

    if label.startswith("property - "):
        return "service_admin"

    if _contains_any(
        label,
        (
            "auto theft - recovered",
            "auto theft recovery",
            "recovered stolen",
            "property found",
            "property lost",
            "property lost then located",
            "property lost/ missing",
            "property - found",
            "property - lost",
            "property - missing",
            "property - stolen then recovered",
        ),
    ):
        return "service_admin"

    if _contains_any(
        label,
        (
            "operating under the influence",
            "driving under the influence",
            "m/v accident",
            "mv crash",
            "motor vehicle crash",
            "leaving scene",
            "hit and run",
            "taxi violation",
            "plates - lost",
            "towed motor vehicle",
            "towed",
            "val - ",
            "other criminal mv offenses",
            "oui",
        ),
    ):
        return "traffic_oui"

    if label == "accident":
        return "traffic_oui"

    if _contains_any(
        label,
        (
            "fraud",
            "forgery",
            "counterfeit",
            "credit card",
            "embezzlement",
            "extortion",
            "blackmail",
            "swindle",
            "flim flam",
            "confidence games",
            "identity theft",
            "identity fraud",
            "false pretense",
            "false pretenses",
            "impersonation",
            "uttering",
        ),
    ):
        return "fraud_financial"

    if _contains_any(label, ("drug", "narcotic")):
        return "drug_narcotic"

    if _contains_any(
        label,
        (
            "prostitution",
            "pornography",
            "obscene material",
            "common nightwalker",
        ),
    ):
        return "vice_obscenity"

    if _contains_any(
        label,
        (
            "weapon",
            "firearm",
            "ballistics",
            "bomb",
            "explosive",
        ),
    ):
        return "weapons"

    if _contains_any(
        label,
        (
            "affray",
            "assembly or gathering",
            "conspiracy except drug law",
            "demonstrations/riot",
            "disorderly",
            "disturbing the peace",
            "drinking in public",
            "drunkenness",
            "gambling",
            "gathering causing annoyance",
            "liquor",
            "noise complaint",
            "noisy party",
            "ordinance",
            "trespass",
            "trespassing",
            "hawker and peddler",
            "license premise violation",
            "license violation",
        ),
    ):
        return "public_order"

    if _contains_any(
        label,
        (
            "murder",
            "homicide",
            "manslaughter",
            "killing of felon",
        ),
    ):
        return "homicide"

    if _contains_any(label, ("kidnapping", "abduction", "human trafficking")):
        return "kidnapping_trafficking"

    if _contains_any(label, ("robbery", "car jacking")):
        return "robbery"

    if _contains_any(label, ("rape", "sodomy", "fondling", "indecent assault", "sex offenses")):
        return "sexual_assault"

    if _contains_any(
        label,
        (
            "aggravated assault",
            "a&b",
            "assault & battery d/w",
            "assault d/w",
            "assault - aggravated",
            "med. attention req",
            "on police officer",
        ),
    ):
        return "aggravated_assault"

    if _contains_any(
        label,
        (
            "simple assault",
            "assault - simple",
            "assault & battery",
            "assault simple - battery",
            "harassment",
            "threat",
            "stalking",
            "domestic dispute",
            "verbal dispute",
            "phone call",
            "annoying and accost",
            "annoying & accost",
            "peeping",
            "indecent exposure",
            "intimidation",
            "child abuse",
            "child endangerment",
            "child abandonment",
            "child requiring assistance",
            "contributing to delinquency",
            "family offenses",
            "offenses against child / family",
            "sex offender",
            "restraining order",
            "harassment prevention order",
            "violation of h.o.",
            "violation of r.o.",
        ),
    ):
        return "family_protective"

    if "home invasion" in label:
        return "robbery"

    if "arson" in label:
        return "arson"

    if _contains_any(label, ("auto theft", "motor vehicle theft")):
        return "motor_vehicle_theft"

    if _contains_any(
        label,
        (
            "burglary",
            "b&e",
            "breaking and entering",
            "housebreak",
            "commercial break",
            "possession of burglarious tools",
        ),
    ):
        return "burglary_breaking"

    if _contains_any(
        label,
        (
            "larceny",
            "shoplifting",
            "pick-pocket",
            "pocket-picking",
            "theft from",
            "theft of",
            "all other larceny",
        ),
    ):
        return "larceny_theft"

    if _contains_any(
        label,
        (
            "stolen property",
            "receiving stolen",
            "rec. stol. property",
            "buying, receiving, selling etc",
            "buying, receiving, selling",
        ),
    ):
        return "stolen_property"

    if _contains_any(
        label,
        (
            "vandalism",
            "graffiti",
            "destruction",
            "mal. dest. property",
            "property related damage",
        ),
    ):
        return "property_damage"

    return "service_admin"


def classify_offense_label(city: str, label: str | None) -> OffenseGroupDefinition:
    normalized_city = normalize_offense_label(city)
    normalized_label = normalize_offense_label(label)
    city_overrides = CITY_OFFENSE_GROUP_OVERRIDES.get(normalized_city, {})
    group_code = city_overrides.get(normalized_label)
    if group_code is None:
        group_code = _classify_general_label(normalized_label)
    return OFFENSE_GROUPS[group_code]


def classify_offense_series(city: str, labels: pd.Series) -> pd.DataFrame:
    classifications = labels.fillna("").map(lambda label: classify_offense_label(city, label))
    return pd.DataFrame(
        {
            "Offense Group": classifications.map(lambda item: item.label),
            "Macro Crime": classifications.map(lambda item: item.macro),
            "Benchmark Crime": classifications.map(lambda item: item.benchmark_family),
        },
        index=labels.index,
    )
