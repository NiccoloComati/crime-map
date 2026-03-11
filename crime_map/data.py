from __future__ import annotations

from functools import lru_cache
from io import StringIO
from pathlib import Path
import pickle
from zipfile import ZipFile

import geopandas as gpd
import pandas as pd
import requests

from .cache import cache_path, clear_cache_dir, download_file, is_fresh
from .config import (
    AREA_CRS,
    BOSTON_CRIME_MACROS,
    BOSTON_CRIME_PACKAGE_ID,
    BOSTON_CRIME_PACKAGE_URL,
    BOSTON_NEIGHBORHOOD_NAME_MAP,
    BOSTON_NEIGHBORHOODS_URL,
    CAMBRIDGE_CRIME_DATASET_ID,
    CAMBRIDGE_CRIME_DOMAIN,
    CAMBRIDGE_CRIME_MACROS,
    CAMBRIDGE_NEIGHBORHOOD_NAME_MAP,
    CAMBRIDGE_NEIGHBORHOODS_URL,
    CENSUS_BLOCK_GEOMETRY_URLS,
    CENSUS_BLOCK_POPULATION_API,
    MUNICIPALITY_ZOOM,
    POPULATION_YEAR_LABEL,
    SOMERVILLE_CRIME_DATASET_ID,
    SOMERVILLE_CRIME_DOMAIN,
    SOMERVILLE_CRIME_MACROS,
    SOMERVILLE_NEIGHBORHOODS_URL,
    TARGET_CRS,
)

SUPPORTED_MUNICIPALITIES = ["All Metro", "Cambridge", "Boston", "Somerville"]
PROCESSED_BUNDLES_CACHE_NAME = "bundles_v1.pkl"
PROCESSED_BUNDLES_MAX_AGE_HOURS = 12.0


def _first_existing_column(frame: pd.DataFrame, candidates: list[str]) -> str:
    lookup = {column.lower(): column for column in frame.columns}
    for candidate in candidates:
        column = lookup.get(candidate.lower())
        if column:
            return column
    raise KeyError(f"None of the expected columns were found: {candidates}")


def _optional_existing_column(frame: pd.DataFrame, candidates: list[str]) -> str | None:
    lookup = {column.lower(): column for column in frame.columns}
    for candidate in candidates:
        column = lookup.get(candidate.lower())
        if column:
            return column
    return None


def _ensure_latlon(geo_df: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if geo_df.crs is None:
        return geo_df.set_crs(TARGET_CRS, allow_override=True)
    if str(geo_df.crs) != TARGET_CRS:
        return geo_df.to_crs(TARGET_CRS)
    return geo_df


def _clean_geometry(geo_df: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    geo_df = geo_df.copy()
    geo_df["geometry"] = geo_df["geometry"].buffer(0)
    geo_df = geo_df[geo_df["geometry"].notna()]
    geo_df = geo_df[~geo_df.geometry.is_empty]
    return geo_df


def _read_zip_shapefile(zip_path: str) -> gpd.GeoDataFrame:
    with ZipFile(zip_path) as archive:
        shapefiles = [name for name in archive.namelist() if name.lower().endswith(".shp")]
    if not shapefiles:
        raise ValueError(f"No .shp file was found in archive: {zip_path}")
    shapefile_name = shapefiles[0]
    resolved_zip = Path(zip_path).resolve().as_posix()
    return gpd.read_file(f"zip://{resolved_zip}!{shapefile_name}")


def _fetch_socrata_csv(
    *,
    domain: str,
    dataset_id: str,
    cache_name: str,
    max_age_hours: float = 12.0,
    force_refresh: bool = False,
) -> pd.DataFrame:
    cached = cache_path(cache_name)
    if not force_refresh and is_fresh(cached, max_age_hours):
        return pd.read_csv(cached, dtype=str, low_memory=False)

    session = requests.Session()
    all_frames: list[pd.DataFrame] = []
    limit = 50_000
    offset = 0

    while True:
        response = session.get(
            f"https://{domain}/resource/{dataset_id}.csv",
            params={"$limit": limit, "$offset": offset},
            timeout=120,
        )
        response.raise_for_status()
        frame = pd.read_csv(StringIO(response.text), dtype=str, low_memory=False)
        if frame.empty:
            break
        all_frames.append(frame)
        if len(frame) < limit:
            break
        offset += limit

    if not all_frames:
        return pd.DataFrame()

    combined = pd.concat(all_frames, ignore_index=True)
    combined.to_csv(cached, index=False)
    return combined


def _fetch_boston_crime_resource_urls() -> list[dict[str, str]]:
    response = requests.get(
        BOSTON_CRIME_PACKAGE_URL,
        params={"id": BOSTON_CRIME_PACKAGE_ID},
        timeout=120,
    )
    response.raise_for_status()
    payload = response.json()
    resources = payload["result"]["resources"]

    filtered: list[dict[str, str]] = []
    for resource in resources:
        if str(resource.get("state", "")).lower() != "active":
            continue
        if str(resource.get("format", "")).lower() != "csv":
            continue
        if "crime incident reports" not in str(resource.get("name", "")).lower():
            continue
        url = resource.get("url")
        resource_id = resource.get("id")
        if not url or not resource_id:
            continue
        filtered.append(
            {
                "id": resource_id,
                "url": url,
                "name": resource.get("name", ""),
                "last_modified": resource.get("last_modified", ""),
            }
        )

    if not filtered:
        raise ValueError("No Boston crime CSV resources were found in package metadata.")

    filtered.sort(key=lambda item: item["name"])
    return filtered


def _load_boston_crime_raw(force_refresh: bool = False) -> pd.DataFrame:
    resources = _fetch_boston_crime_resource_urls()
    frames: list[pd.DataFrame] = []

    for resource in resources:
        path = download_file(
            resource["url"],
            filename=f"boston_crime_{resource['id']}.csv",
            max_age_hours=12.0,
            force_refresh=force_refresh,
        )
        frame = pd.read_csv(path, dtype=str, low_memory=False)
        frame["__resource_id"] = resource["id"]
        frames.append(frame)

    combined = pd.concat(frames, ignore_index=True)
    return combined.drop_duplicates()


def _normalize_boston_crime(raw: pd.DataFrame) -> pd.DataFrame:
    date_column = _first_existing_column(
        raw,
        [
            "From Date",
            "from_date",
            "fromdate",
            "OCCURRED_ON_DATE",
            "occurred_on_date",
            "REPORT_DATE",
            "report_date",
        ],
    )
    crime_column = _first_existing_column(
        raw,
        [
            "Crime",
            "crime",
            "Offense Description",
            "OFFENSE_DESCRIPTION",
            "offense_description",
            "OFFENSE_CODE_GROUP",
            "offense_code_group",
            "incident_type_description",
        ],
    )
    neighborhood_column = _optional_existing_column(
        raw,
        ["Neighborhood", "NEIGHBORHOOD", "neighborhood"],
    )
    district_column = _optional_existing_column(
        raw,
        ["BPD District", "district", "DISTRICT", "reporting_district", "REPORTING_AREA"],
    )
    latitude_column = _optional_existing_column(raw, ["Lat", "LAT", "lat", "Latitude", "latitude"])
    longitude_column = _optional_existing_column(
        raw,
        ["Long", "LONG", "long", "Longitude", "longitude", "Lng", "lng"],
    )

    data = pd.DataFrame()
    data["Date"] = pd.to_datetime(raw[date_column], errors="coerce")
    data["Crime"] = raw[crime_column].fillna("").astype(str).str.title().str.strip()
    if neighborhood_column:
        data["Neighborhood"] = raw[neighborhood_column].fillna("").astype(str).str.strip()
    else:
        data["Neighborhood"] = ""
    data["Macro Crime"] = data["Crime"].map(BOSTON_CRIME_MACROS).fillna("Miscellaneous")
    data["City"] = "Boston"
    if district_column:
        data["BPD District"] = raw[district_column].fillna("").astype(str).str.strip()
    if latitude_column and longitude_column:
        data["Latitude"] = pd.to_numeric(raw[latitude_column], errors="coerce")
        data["Longitude"] = pd.to_numeric(raw[longitude_column], errors="coerce")
    else:
        data["Latitude"] = pd.NA
        data["Longitude"] = pd.NA
    return data


def _normalize_cambridge_crime(raw: pd.DataFrame) -> pd.DataFrame:
    date_column = _first_existing_column(raw, ["crime_date_time", "Crime Date Time"])
    crime_column = _first_existing_column(raw, ["crime", "Crime"])
    neighborhood_column = _first_existing_column(raw, ["neighborhood", "Neighborhood"])

    data = pd.DataFrame()
    date_values = raw[date_column].fillna("").astype(str).str.split(" ").str[0]
    data["Date"] = pd.to_datetime(date_values, errors="coerce")
    data["Crime"] = raw[crime_column].fillna("").astype(str).str.strip()
    data["Neighborhood"] = raw[neighborhood_column].fillna("").astype(str).str.strip()
    data["Neighborhood"] = data["Neighborhood"].replace(CAMBRIDGE_NEIGHBORHOOD_NAME_MAP)
    data["Macro Crime"] = data["Crime"].map(CAMBRIDGE_CRIME_MACROS).fillna("Miscellaneous")
    data["City"] = "Cambridge"
    return data


def _normalize_somerville_crime(raw: pd.DataFrame, block_to_neighborhood: dict[str, str]) -> pd.DataFrame:
    day_column = _first_existing_column(raw, ["day_and_month", "Day and Month Reported"])
    year_column = _first_existing_column(raw, ["year", "Year Reported"])
    crime_column = _first_existing_column(raw, ["offense", "Offense Type"])
    block_column = _first_existing_column(raw, ["blockcode", "Block Code"])

    day_month = raw[day_column].fillna("").astype(str).str.strip()
    year = raw[year_column].fillna("").astype(str).str.strip()
    date_text = day_month.where(day_month.ne(""), "01/01") + "/" + year

    block_codes = (
        raw[block_column]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )
    block_codes = block_codes.str.extract(r"(\d{15})", expand=False).fillna(block_codes)

    data = pd.DataFrame()
    data["Date"] = pd.to_datetime(date_text, errors="coerce")
    data["Crime"] = raw[crime_column].fillna("").astype(str).str.title().str.strip()
    data["Macro Crime"] = data["Crime"].map(SOMERVILLE_CRIME_MACROS).fillna("Miscellaneous")
    data["Neighborhood"] = block_codes.map(block_to_neighborhood)
    data["City"] = "Somerville"
    return data


def _fill_neighborhoods_from_points(
    crime_df: pd.DataFrame,
    city_geo: gpd.GeoDataFrame,
) -> pd.DataFrame:
    if "Latitude" not in crime_df.columns or "Longitude" not in crime_df.columns:
        return crime_df

    pending = (
        crime_df["Neighborhood"].fillna("").astype(str).str.strip().eq("")
        & crime_df["Latitude"].notna()
        & crime_df["Longitude"].notna()
    )
    if not pending.any():
        return crime_df

    points = gpd.GeoDataFrame(
        crime_df.loc[pending].copy(),
        geometry=gpd.points_from_xy(
            crime_df.loc[pending, "Longitude"],
            crime_df.loc[pending, "Latitude"],
        ),
        crs=TARGET_CRS,
    )
    neighborhoods = city_geo[["Mapped_Name", "geometry"]].copy()
    joined = gpd.sjoin(points, neighborhoods, how="left", predicate="within")
    joined = joined[~joined.index.duplicated(keep="first")]

    mapped = joined["Mapped_Name"].fillna("")
    crime_df.loc[mapped.index, "Neighborhood"] = mapped.values
    return crime_df


def _prepare_geography(geo_df: gpd.GeoDataFrame, *, city: str, neighborhood_column: str) -> gpd.GeoDataFrame:
    prepared = _ensure_latlon(_clean_geometry(geo_df))
    prepared["City"] = city
    prepared["Mapped_Name"] = prepared[neighborhood_column].fillna("").astype(str).str.strip()
    prepared = prepared[prepared["Mapped_Name"].ne("")].copy()
    prepared["GeoKey"] = prepared["City"] + "::" + prepared["Mapped_Name"]
    prepared = prepared[["City", "Mapped_Name", "GeoKey", "geometry"]].copy()
    return prepared.dissolve(by=["City", "Mapped_Name", "GeoKey"], as_index=False)


def _load_cambridge_geo(force_refresh: bool = False) -> gpd.GeoDataFrame:
    path = download_file(
        CAMBRIDGE_NEIGHBORHOODS_URL,
        "cambridge_neighborhoods.geojson",
        max_age_hours=72.0,
        force_refresh=force_refresh,
    )
    geo = gpd.read_file(path)
    geo = _prepare_geography(geo, city="Cambridge", neighborhood_column="name")
    geo["Mapped_Name"] = geo["Mapped_Name"].replace(CAMBRIDGE_NEIGHBORHOOD_NAME_MAP)
    geo["GeoKey"] = geo["City"] + "::" + geo["Mapped_Name"]
    return geo.dissolve(by=["City", "Mapped_Name", "GeoKey"], as_index=False)


def _load_boston_geo(force_refresh: bool = False) -> gpd.GeoDataFrame:
    path = download_file(
        BOSTON_NEIGHBORHOODS_URL,
        "boston_neighborhoods.geojson",
        max_age_hours=72.0,
        force_refresh=force_refresh,
    )
    geo = gpd.read_file(path)
    neighborhood_column = _first_existing_column(geo, ["BlockGr202", "blockgr202", "Neighborhood"])
    geo = _prepare_geography(geo, city="Boston", neighborhood_column=neighborhood_column)
    geo["Mapped_Name"] = geo["Mapped_Name"].replace(BOSTON_NEIGHBORHOOD_NAME_MAP)
    geo["GeoKey"] = geo["City"] + "::" + geo["Mapped_Name"]
    return geo.dissolve(by=["City", "Mapped_Name", "GeoKey"], as_index=False)


def _load_somerville_geo(force_refresh: bool = False) -> gpd.GeoDataFrame:
    zip_path = download_file(
        SOMERVILLE_NEIGHBORHOODS_URL,
        "somerville_neighborhoods.zip",
        max_age_hours=72.0,
        force_refresh=force_refresh,
    )
    geo = _read_zip_shapefile(str(zip_path))
    neighborhood_column = _first_existing_column(geo, ["NBHD", "Neighborhood"])
    return _prepare_geography(geo, city="Somerville", neighborhood_column=neighborhood_column)


def _load_census_block_population(county_fips: str, force_refresh: bool = False) -> pd.DataFrame:
    cache_name = f"census_population_{county_fips}.csv"
    cached = cache_path(cache_name)
    if not force_refresh and is_fresh(cached, 72.0):
        return pd.read_csv(cached, dtype={"GEOID20": str})

    response = requests.get(
        CENSUS_BLOCK_POPULATION_API.format(county=county_fips),
        timeout=300,
    )
    response.raise_for_status()
    payload = response.json()
    header = payload[0]
    records = payload[1:]
    table = pd.DataFrame(records, columns=header)
    table["GEOID20"] = table["state"] + table["county"] + table["tract"] + table["block"]
    table["POP20"] = pd.to_numeric(table["P1_001N"], errors="coerce").fillna(0.0)
    table = table[["GEOID20", "POP20"]].copy()
    table.to_csv(cached, index=False)
    return table


def _load_census_blocks(force_refresh: bool = False) -> gpd.GeoDataFrame:
    block_frames: list[gpd.GeoDataFrame] = []

    for county_fips, url in CENSUS_BLOCK_GEOMETRY_URLS.items():
        zip_path = download_file(
            url,
            filename=f"census_blocks_{county_fips}.zip",
            max_age_hours=168.0,
            force_refresh=force_refresh,
        )
        geometry = _read_zip_shapefile(str(zip_path))
        geoid_column = _first_existing_column(geometry, ["GEOID20", "geoid20"])
        geometry = geometry[[geoid_column, "geometry"]].rename(columns={geoid_column: "GEOID20"})
        geometry["GEOID20"] = geometry["GEOID20"].astype(str)

        population = _load_census_block_population(county_fips, force_refresh=force_refresh)
        merged = geometry.merge(population, on="GEOID20", how="left")
        merged["POP20"] = pd.to_numeric(merged["POP20"], errors="coerce").fillna(0.0)
        block_frames.append(gpd.GeoDataFrame(merged, geometry="geometry", crs=geometry.crs))

    blocks = gpd.GeoDataFrame(pd.concat(block_frames, ignore_index=True), crs=block_frames[0].crs)
    return _ensure_latlon(_clean_geometry(blocks))


def _build_somerville_block_lookup(
    blocks: gpd.GeoDataFrame, somerville_geo: gpd.GeoDataFrame
) -> dict[str, str]:
    neighborhoods = somerville_geo[["Mapped_Name", "geometry"]].copy()
    neighborhoods = _ensure_latlon(neighborhoods).to_crs(AREA_CRS)
    city_union = neighborhoods.unary_union

    city_blocks = _ensure_latlon(blocks).to_crs(AREA_CRS)
    city_blocks = city_blocks[city_blocks.intersects(city_union)].copy()
    city_blocks = city_blocks[["GEOID20", "geometry"]]

    intersections = gpd.overlay(
        city_blocks,
        neighborhoods,
        how="intersection",
        keep_geom_type=False,
    )
    if intersections.empty:
        return {}

    intersections["intersection_area"] = intersections.geometry.area
    best = intersections.loc[
        intersections.groupby("GEOID20")["intersection_area"].idxmax(),
        ["GEOID20", "Mapped_Name"],
    ]
    return dict(zip(best["GEOID20"], best["Mapped_Name"]))


def _compute_population_by_neighborhood(
    neighborhoods: gpd.GeoDataFrame,
    blocks: gpd.GeoDataFrame,
) -> dict[str, float]:
    populations: dict[str, float] = {}
    blocks_area = _ensure_latlon(blocks).to_crs(AREA_CRS).copy()
    blocks_area["block_area"] = blocks_area.geometry.area

    for city, city_geo in neighborhoods.groupby("City"):
        city_geo = city_geo[["GeoKey", "geometry"]].copy().to_crs(AREA_CRS)
        city_union = city_geo.unary_union
        city_blocks = blocks_area[blocks_area.intersects(city_union)].copy()
        if city_blocks.empty:
            continue

        intersections = gpd.overlay(
            city_blocks[["GEOID20", "POP20", "block_area", "geometry"]],
            city_geo,
            how="intersection",
            keep_geom_type=False,
        )
        if intersections.empty:
            continue

        intersections = intersections[intersections["block_area"] > 0].copy()
        intersections["intersection_area"] = intersections.geometry.area
        intersections["allocated_population"] = (
            intersections["POP20"] * intersections["intersection_area"] / intersections["block_area"]
        )

        city_population = intersections.groupby("GeoKey")["allocated_population"].sum()
        populations.update({key: float(value) for key, value in city_population.items()})

    for geokey in neighborhoods["GeoKey"].unique():
        populations.setdefault(geokey, 0.0)
    return populations


def _add_geokey_and_clean(data: pd.DataFrame) -> pd.DataFrame:
    data = data.copy()
    data["Neighborhood"] = data["Neighborhood"].fillna("").astype(str).str.strip()
    data = data[data["Neighborhood"].ne("")]
    data = data[data["Date"].notna()]
    data["GeoKey"] = data["City"] + "::" + data["Neighborhood"]
    return data[["City", "Date", "Crime", "Macro Crime", "Neighborhood", "GeoKey"]]


def _build_city_bundle(
    city: str,
    crime: pd.DataFrame,
    geo: gpd.GeoDataFrame,
    population: dict[str, float],
) -> dict[str, object]:
    city_population = {
        geokey: value for geokey, value in population.items() if geokey.startswith(f"{city}::")
    }
    for geokey in geo["GeoKey"]:
        city_population.setdefault(geokey, 0.0)

    return {
        "crime": crime,
        "geo": geo,
        "population": city_population,
        "zoom": MUNICIPALITY_ZOOM[city],
        "population_year": POPULATION_YEAR_LABEL,
    }


def _load_cached_bundles() -> dict[str, dict[str, object]] | None:
    cached = cache_path(PROCESSED_BUNDLES_CACHE_NAME)
    if not is_fresh(cached, PROCESSED_BUNDLES_MAX_AGE_HOURS):
        return None

    try:
        with cached.open("rb") as handle:
            bundles = pickle.load(handle)
    except Exception:
        return None

    if not isinstance(bundles, dict):
        return None
    return bundles


def _store_cached_bundles(bundles: dict[str, dict[str, object]]) -> None:
    cached = cache_path(PROCESSED_BUNDLES_CACHE_NAME)
    with cached.open("wb") as handle:
        pickle.dump(bundles, handle, protocol=pickle.HIGHEST_PROTOCOL)


@lru_cache(maxsize=1)
def _load_bundles() -> dict[str, dict[str, object]]:
    cached = _load_cached_bundles()
    if cached is not None:
        return cached

    blocks = _load_census_blocks(force_refresh=False)
    cambridge_geo = _load_cambridge_geo(force_refresh=False)
    boston_geo = _load_boston_geo(force_refresh=False)
    somerville_geo = _load_somerville_geo(force_refresh=False)
    combined_geo = gpd.GeoDataFrame(
        pd.concat([cambridge_geo, boston_geo, somerville_geo], ignore_index=True),
        geometry="geometry",
        crs=cambridge_geo.crs,
    )

    population = _compute_population_by_neighborhood(combined_geo, blocks)
    somerville_block_lookup = _build_somerville_block_lookup(blocks, somerville_geo)

    cambridge_crime_raw = _fetch_socrata_csv(
        domain=CAMBRIDGE_CRIME_DOMAIN,
        dataset_id=CAMBRIDGE_CRIME_DATASET_ID,
        cache_name="cambridge_crime.csv",
    )
    boston_crime_raw = _load_boston_crime_raw(force_refresh=False)
    somerville_crime_raw = _fetch_socrata_csv(
        domain=SOMERVILLE_CRIME_DOMAIN,
        dataset_id=SOMERVILLE_CRIME_DATASET_ID,
        cache_name="somerville_crime.csv",
    )

    cambridge_crime = _add_geokey_and_clean(_normalize_cambridge_crime(cambridge_crime_raw))
    boston_crime = _normalize_boston_crime(boston_crime_raw)
    boston_crime["Neighborhood"] = (
        boston_crime["Neighborhood"].fillna("").astype(str).str.strip().replace(BOSTON_NEIGHBORHOOD_NAME_MAP)
    )
    boston_crime = _fill_neighborhoods_from_points(boston_crime, boston_geo)
    if "BPD District" in boston_crime.columns:
        missing = boston_crime["Neighborhood"].fillna("").astype(str).str.strip().eq("")
        boston_crime.loc[missing, "Neighborhood"] = (
            boston_crime.loc[missing, "BPD District"].fillna("").astype(str).str.strip()
        )
    boston_crime = _add_geokey_and_clean(boston_crime)
    somerville_crime = _add_geokey_and_clean(
        _normalize_somerville_crime(somerville_crime_raw, somerville_block_lookup)
    )

    bundles: dict[str, dict[str, object]] = {}
    bundles["Cambridge"] = _build_city_bundle(
        "Cambridge",
        cambridge_crime,
        cambridge_geo,
        population,
    )
    bundles["Boston"] = _build_city_bundle(
        "Boston",
        boston_crime,
        boston_geo,
        population,
    )
    bundles["Somerville"] = _build_city_bundle(
        "Somerville",
        somerville_crime,
        somerville_geo,
        population,
    )

    all_crime = pd.concat([cambridge_crime, boston_crime, somerville_crime], ignore_index=True)
    all_geo = gpd.GeoDataFrame(
        pd.concat([cambridge_geo, boston_geo, somerville_geo], ignore_index=True),
        geometry="geometry",
        crs=cambridge_geo.crs,
    )
    bundles["All Metro"] = {
        "crime": all_crime,
        "geo": all_geo,
        "population": population,
        "zoom": MUNICIPALITY_ZOOM["All Metro"],
        "population_year": POPULATION_YEAR_LABEL,
    }
    _store_cached_bundles(bundles)
    return bundles


def get_supported_municipalities() -> list[str]:
    return SUPPORTED_MUNICIPALITIES.copy()


def get_bundle(municipality: str) -> dict[str, object]:
    bundles = _load_bundles()
    if municipality in bundles:
        return bundles[municipality]
    return bundles["All Metro"]


def warm_processed_cache() -> list[str]:
    _load_bundles()
    return get_supported_municipalities()


def reset_state(*, clear_disk_cache: bool = False) -> None:
    _load_bundles.cache_clear()
    if clear_disk_cache:
        clear_cache_dir()
