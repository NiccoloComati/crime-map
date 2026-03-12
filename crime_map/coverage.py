from __future__ import annotations

from dataclasses import asdict, dataclass

CURRENT_AGGREGATE_NAME = "All Metro"
CURRENT_AGGREGATE_LABEL = "Boston Metro"
CURRENT_AGGREGATE_MEMBERS = ["Boston", "Cambridge", "Somerville"]

OFFICIAL_METRO_REFERENCE_NAME = "Boston-Cambridge-Newton, MA-NH Metropolitan Statistical Area"
OFFICIAL_METRO_REFERENCE_URL = (
    "https://www.census.gov/programs-surveys/metro-micro/about/delineation-files.html"
)


@dataclass(frozen=True)
class MunicipalityCoverage:
    name: str
    label: str
    status: str
    geography_level: str
    temporal_granularity: str
    source_kind: str
    included_in_current_aggregate: bool
    notes: str
    official_source_urls: tuple[str, ...]


MUNICIPALITY_COVERAGE: tuple[MunicipalityCoverage, ...] = (
    MunicipalityCoverage(
        name=CURRENT_AGGREGATE_NAME,
        label=CURRENT_AGGREGATE_LABEL,
        status="supported_aggregate",
        geography_level="multi-municipality aggregate",
        temporal_granularity="daily",
        source_kind="derived from supported municipal official feeds",
        included_in_current_aggregate=False,
        notes=(
            "This aggregate currently combines the supported neighborhood-level municipalities. "
            "Standalone municipality-level additions are kept out of this map until comparable submunicipal "
            "geometry is available. It is not yet the full official Census metro area."
        ),
        official_source_urls=(OFFICIAL_METRO_REFERENCE_URL,),
    ),
    MunicipalityCoverage(
        name="Belmont",
        label="Belmont",
        status="supported",
        geography_level="municipality",
        temporal_granularity="daily",
        source_kind="official municipal police public-log PDFs plus Census town boundary",
        included_in_current_aggregate=False,
        notes=(
            "Belmont is currently supported as a municipality-wide map because the official public log is "
            "available but a defensible submunicipal crime geography is not yet wired into the app."
        ),
        official_source_urls=("https://www.belmont-ma.gov/2225/Call-Log",),
    ),
    MunicipalityCoverage(
        name="Boston",
        label="Boston",
        status="supported",
        geography_level="neighborhood",
        temporal_granularity="daily",
        source_kind="official municipal open-data feed",
        included_in_current_aggregate=True,
        notes="Neighborhood polygons and incident-level records are both available from official sources.",
        official_source_urls=(
            "https://data.boston.gov/dataset/crime-incident-reports-august-2015-to-date-source-new-system",
            "https://data.boston.gov/dataset/boston-neighborhoods",
        ),
    ),
    MunicipalityCoverage(
        name="Cambridge",
        label="Cambridge",
        status="supported",
        geography_level="neighborhood",
        temporal_granularity="daily",
        source_kind="official municipal open-data feed",
        included_in_current_aggregate=True,
        notes="Neighborhood polygons and incident-level records are both available from official sources.",
        official_source_urls=(
            "https://data.cambridgema.gov/Public-Safety/Crime-Incident-Reports/xuad-73uj",
            "https://data.cambridgema.gov/Boundaries/Neighborhoods/k3pi-9823",
        ),
    ),
    MunicipalityCoverage(
        name="Reading",
        label="Reading",
        status="supported",
        geography_level="municipality",
        temporal_granularity="daily",
        source_kind="official municipal police public-log PDFs plus Census town boundary",
        included_in_current_aggregate=False,
        notes=(
            "Reading is currently supported as a municipality-wide map from the official daily police log. "
            "It is kept out of the metro aggregate until comparable submunicipal geometry is added."
        ),
        official_source_urls=("https://www.readingma.gov/752/Daily-Police-Log",),
    ),
    MunicipalityCoverage(
        name="Lexington",
        label="Lexington",
        status="candidate_logs_only",
        geography_level="municipality",
        temporal_granularity="daily",
        source_kind="official municipal police public-log PDFs plus Census town boundary",
        included_in_current_aggregate=False,
        notes=(
            "Lexington publishes an official weekly public-log archive and the extraction path is workable, "
            "but it has not yet been promoted into supported coverage because the current archive size would "
            "materially lengthen the bundle prewarm step."
        ),
        official_source_urls=(
            "https://www.lexingtonma.gov/489/Weekly-Police-Logs",
            "https://www.lexingtonma.gov/2496/2025-Weekly-Police-Logs",
            "https://www.lexingtonma.gov/2278/2024-Weekly-Police-Logs",
            "https://www.lexingtonma.gov/1940/2023-Weekly-Police-Logs",
            "https://www.lexingtonma.gov/1941/2022-Weekly-Police-Logs",
        ),
    ),
    MunicipalityCoverage(
        name="Somerville",
        label="Somerville",
        status="supported",
        geography_level="neighborhood",
        temporal_granularity="daily",
        source_kind="official municipal open-data feed",
        included_in_current_aggregate=True,
        notes=(
            "Official crime records are combined with official neighborhood geometry through a census-block lookup."
        ),
        official_source_urls=(
            "https://data.somervillema.gov/Public-Safety/Crime-Reports/aghs-hqvg",
            "https://data.somervillema.gov/api/views/n5md-vqta/files/13bc2d2b-77b1-4221-a24c-dd376f4834db",
        ),
    ),
    MunicipalityCoverage(
        name="Brookline",
        label="Brookline",
        status="candidate_review",
        geography_level="police sector or municipality",
        temporal_granularity="incident or daily",
        source_kind="officially linked third-party crime portal plus official municipal GIS",
        included_in_current_aggregate=False,
        notes=(
            "Official geography is available. The police department links crime reports to CityProtect, "
            "which needs a defensible extraction path before the municipality is promoted into coverage."
        ),
        official_source_urls=(
            "https://police.brooklinema.gov/",
            "https://maps.brooklinema.gov",
        ),
    ),
    MunicipalityCoverage(
        name="Medford",
        label="Medford",
        status="candidate_review",
        geography_level="unknown pending dashboard extraction",
        temporal_granularity="unknown pending dashboard extraction",
        source_kind="official municipal dashboard",
        included_in_current_aggregate=False,
        notes=(
            "The police department publishes an official Power BI crime dashboard, but it is not yet wired "
            "through a stable extraction path."
        ),
        official_source_urls=("https://medfordpolice.com/crime-dashboard/",),
    ),
    MunicipalityCoverage(
        name="Chelsea",
        label="Chelsea",
        status="candidate_summary_only",
        geography_level="municipality",
        temporal_granularity="annual or weekly log documents",
        source_kind="official summary PDFs and arrest-log PDFs",
        included_in_current_aggregate=False,
        notes=(
            "Official crime statistics are public, but the currently exposed sources are summary PDFs and "
            "arrest-log PDFs rather than a structured incident feed."
        ),
        official_source_urls=("https://chelseapolice.com/resources/crime_statistic_logs",),
    ),
    MunicipalityCoverage(
        name="Everett",
        label="Everett",
        status="candidate_logs_only",
        geography_level="ward or precinct",
        temporal_granularity="log-based",
        source_kind="official daily-log page plus official GIS precinct geometry",
        included_in_current_aggregate=False,
        notes=(
            "Official precinct geometry exists. Crime publication appears to be log-style rather than a clean "
            "incident feed, so a correct ingestion path still needs to be defined."
        ),
        official_source_urls=(
            "https://everettpolicema.com/?page_id=1545",
            "https://www.arcgis.com/sharing/rest/content/items/7f5035d6831a4386a16bbe82cbcc7ad7",
        ),
    ),
    MunicipalityCoverage(
        name="Burlington",
        label="Burlington",
        status="candidate_logs_only",
        geography_level="municipality",
        temporal_granularity="weekly public logs",
        source_kind="official municipal police log archive",
        included_in_current_aggregate=False,
        notes=(
            "Burlington publishes an official police-log archive. The archive path is promising, but it still "
            "needs a stable full-history extraction path before promotion into supported coverage."
        ),
        official_source_urls=("https://www.burlington.org/Archive.aspx",),
    ),
    MunicipalityCoverage(
        name="Watertown",
        label="Watertown",
        status="candidate_logs_only",
        geography_level="municipality",
        temporal_granularity="weekly dispatch logs",
        source_kind="official police dispatch-log archive",
        included_in_current_aggregate=False,
        notes=(
            "Watertown publishes an official dispatch-log archive. The current public archive appears shallow, "
            "so it remains a candidate until the available history and extraction path are strong enough."
        ),
        official_source_urls=("https://www.watertownpd.org/Archive.aspx?AMID=37",),
    ),
)


def coverage_payload() -> dict[str, object]:
    return {
        "official_metro_reference_name": OFFICIAL_METRO_REFERENCE_NAME,
        "official_metro_reference_url": OFFICIAL_METRO_REFERENCE_URL,
        "current_aggregate_name": CURRENT_AGGREGATE_NAME,
        "current_aggregate_label": CURRENT_AGGREGATE_LABEL,
        "current_aggregate_members": CURRENT_AGGREGATE_MEMBERS,
        "municipalities": [
            {
                **asdict(entry),
                "official_source_urls": list(entry.official_source_urls),
            }
            for entry in MUNICIPALITY_COVERAGE
        ],
    }


def municipality_label(name: str) -> str:
    for entry in MUNICIPALITY_COVERAGE:
        if entry.name == name:
            return entry.label
    return name


def get_supported_municipality_names() -> list[str]:
    return [entry.name for entry in MUNICIPALITY_COVERAGE if entry.status in {"supported", "supported_aggregate"}]
