from pathlib import Path

TARGET_CRS = "EPSG:4326"
AREA_CRS = "EPSG:26986"

CACHE_DIR = Path(__file__).resolve().parents[1] / ".cache" / "crime_map"

CAMBRIDGE_CRIME_DATASET_ID = "xuad-73uj"
CAMBRIDGE_CRIME_DOMAIN = "data.cambridgema.gov"
CAMBRIDGE_NEIGHBORHOODS_URL = (
    "https://data.cambridgema.gov/api/views/k3pi-9823/rows.geojson?accessType=DOWNLOAD"
)

BOSTON_CRIME_PACKAGE_ID = "6220d948-eae2-4e4b-8723-2dc8e67722a3"
BOSTON_CRIME_PACKAGE_URL = "https://data.boston.gov/api/3/action/package_show"
BOSTON_NEIGHBORHOODS_URL = (
    "https://data.boston.gov/dataset/2513408b-b130-43f6-83d6-0f896ff3b2cc/"
    "resource/37c3db4c-e1c8-44b2-83ef-e4f6ada613ed/download/census2020_bg_neighborhoods.json"
)

SOMERVILLE_CRIME_DATASET_ID = "aghs-hqvg"
SOMERVILLE_CRIME_DOMAIN = "data.somervillema.gov"
SOMERVILLE_NEIGHBORHOODS_URL = (
    "https://data.somervillema.gov/api/views/n5md-vqta/files/"
    "13bc2d2b-77b1-4221-a24c-dd376f4834db"
)

CENSUS_BLOCK_GEOMETRY_URLS = {
    "017": (
        "https://www2.census.gov/geo/tiger/TIGER2020PL/STATE/25_MASSACHUSETTS/"
        "25017/tl_2020_25017_tabblock20.zip"
    ),
    "025": (
        "https://www2.census.gov/geo/tiger/TIGER2020PL/STATE/25_MASSACHUSETTS/"
        "25025/tl_2020_25025_tabblock20.zip"
    ),
}
CENSUS_BLOCK_POPULATION_API = (
    "https://api.census.gov/data/2020/dec/pl?get=P1_001N&for=block:*&in=state:25%20county:{county}"
)

MUNICIPALITY_ZOOM = {
    "Cambridge": 13.0,
    "Boston": 12.0,
    "Somerville": 13.0,
    "All Metro": 11.5,
}
POPULATION_YEAR_LABEL = "2020 Census (P.L. 94-171 block population, area-allocated)"

CAMBRIDGE_NEIGHBORHOOD_NAME_MAP = {
    "The Port": "Area 4",
    "Neighborhood Nine": "Peabody",
    "Wellington-Harrington": "Inman/Harrington",
    "Mid-Cambridge": "Mid-Cambridge",
    "North Cambridge": "North Cambridge",
    "Cambridge Highlands": "Highlands",
    "Strawberry Hill": "Strawberry Hill",
    "West Cambridge": "West Cambridge",
    "Riverside": "Riverside",
    "Cambridgeport": "Cambridgeport",
    "Area 2/MIT": "MIT",
    "East Cambridge": "East Cambridge",
    "Baldwin": "Agassiz",
}

BOSTON_NEIGHBORHOOD_NAME_MAP = {
    "Chinatown": "Downtown",
    "Leather District": "Downtown",
    "Bay Village": "South End",
}
