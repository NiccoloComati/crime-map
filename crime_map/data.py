from __future__ import annotations

from functools import lru_cache

import geopandas as gpd
import pandas as pd

from .config import (
    BOSTON_CRIME_CSV,
    BOSTON_CRIME_MACROS,
    BOSTON_NEIGHBORHOOD_NAME_MAP,
    BOSTON_POP_XLSM,
    BOSTON_SHAPEFILE,
    CAMBRIDGE_CRIME_CSV,
    CAMBRIDGE_CRIME_MACROS,
    CAMBRIDGE_NEIGHBORHOOD_NAME_MAP,
    CAMBRIDGE_POP_2020,
    CAMBRIDGE_SHAPEFILE,
    MA_CENSUS_BLOCKS,
    SOMERVILLE_CRIME_CSV,
    SOMERVILLE_CRIME_MACROS,
    SOMERVILLE_SHAPEFILE,
)

TARGET_CRS = "EPSG:4326"
AREA_CRS = "EPSG:26986"


def _ensure_latlon(geo_df: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if geo_df.crs != TARGET_CRS:
        return geo_df.to_crs(TARGET_CRS)
    return geo_df


def _pick_population_column(frame: pd.DataFrame, candidates: list[str]) -> str:
    for column in candidates:
        if column in frame.columns:
            return column
    raise KeyError(f"None of the expected population columns were found: {candidates}")


@lru_cache(maxsize=1)
def load_mass_census_blocks() -> gpd.GeoDataFrame:
    blocks = gpd.read_file(MA_CENSUS_BLOCKS)
    return _ensure_latlon(blocks)


@lru_cache(maxsize=1)
def load_cambridge_crime() -> pd.DataFrame:
    df = pd.read_csv(CAMBRIDGE_CRIME_CSV)
    df = df[["Crime Date Time", "Crime", "Neighborhood", "Reporting Area"]].copy()
    df["City"] = "Cambridge"
    df["Date"] = pd.to_datetime(df["Crime Date Time"].str.split(" ").str[0])
    df["Macro Crime"] = df["Crime"].map(CAMBRIDGE_CRIME_MACROS)
    return df[["City", "Date", "Crime", "Macro Crime", "Neighborhood", "Reporting Area"]]


@lru_cache(maxsize=1)
def load_cambridge_geo() -> gpd.GeoDataFrame:
    geo_df = _ensure_latlon(gpd.read_file(CAMBRIDGE_SHAPEFILE))
    geo_df["Mapped_Name"] = geo_df["NAME"].map(CAMBRIDGE_NEIGHBORHOOD_NAME_MAP).fillna(
        geo_df["NAME"]
    )
    geo_df["City"] = "Cambridge"
    return geo_df


@lru_cache(maxsize=1)
def load_boston_crime() -> pd.DataFrame:
    df = pd.read_csv(BOSTON_CRIME_CSV)
    df = df[["From Date", "Crime", "Neighborhood", "BPD District"]].copy()
    df["City"] = "Boston"
    df["Date"] = pd.to_datetime(df["From Date"].str.split(" ").str[0])
    df["Crime"] = df["Crime"].str.title()
    df["Macro Crime"] = df["Crime"].map(BOSTON_CRIME_MACROS)
    df["Neighborhood_Source"] = df["Neighborhood"]
    df["Neighborhood"] = (
        df["Neighborhood"].map(BOSTON_NEIGHBORHOOD_NAME_MAP).fillna(df["Neighborhood"])
    )
    return df[
        ["City", "Date", "Crime", "Macro Crime", "Neighborhood", "Neighborhood_Source", "BPD District"]
    ]


@lru_cache(maxsize=1)
def load_boston_population() -> dict[str, float]:
    df = pd.read_excel(BOSTON_POP_XLSM, header=2)
    df.set_index("Unnamed: 0", inplace=True)
    pop_dict = df.loc["Allston":"West Roxbury", "Total Population"].to_dict()
    return {str(k).strip(): float(v) for k, v in pop_dict.items()}


@lru_cache(maxsize=1)
def load_boston_geo() -> gpd.GeoDataFrame:
    geo_df = _ensure_latlon(gpd.read_file(BOSTON_SHAPEFILE))
    geo_df["Mapped_Name"] = geo_df["blockgr202"].map(BOSTON_NEIGHBORHOOD_NAME_MAP).fillna(
        geo_df["blockgr202"]
    )
    geo_df["City"] = "Boston"
    return geo_df


@lru_cache(maxsize=1)
def load_somerville_geo() -> gpd.GeoDataFrame:
    geo_df = _ensure_latlon(gpd.read_file(SOMERVILLE_SHAPEFILE))
    geo_df["Mapped_Name"] = geo_df["NBHD"]
    geo_df["City"] = "Somerville"
    return geo_df


@lru_cache(maxsize=1)
def load_somerville_blocks() -> gpd.GeoDataFrame:
    blocks = load_mass_census_blocks()
    somerville_blocks = blocks[blocks["TOWN"] == "SOMERVILLE"].copy()
    if somerville_blocks.empty:
        raise ValueError("No Somerville census blocks were found in the Massachusetts census shapefile.")
    return somerville_blocks


@lru_cache(maxsize=1)
def load_somerville_population() -> dict[str, float]:
    neighborhoods = load_somerville_geo()[["NBHD", "geometry"]].copy()
    blocks = load_somerville_blocks().copy()

    population_column = _pick_population_column(
        blocks,
        ["POP20", "POPULATION", "POP", "TOTPOP", "TOTAL_POP"],
    )

    blocks = blocks[["GEOID20", population_column, "geometry"]].copy()
    blocks[population_column] = pd.to_numeric(blocks[population_column], errors="coerce").fillna(0.0)

    blocks_area = blocks.to_crs(AREA_CRS).copy()
    neighborhoods_area = neighborhoods.to_crs(AREA_CRS).copy()

    blocks_area["block_area"] = blocks_area.geometry.area
    intersections = gpd.overlay(
        blocks_area,
        neighborhoods_area,
        how="intersection",
        keep_geom_type=False,
    )

    intersections["intersection_area"] = intersections.geometry.area
    intersections["population_share"] = 0.0
    positive_area = intersections["block_area"] > 0
    intersections.loc[positive_area, "population_share"] = (
        intersections.loc[positive_area, "intersection_area"]
        / intersections.loc[positive_area, "block_area"]
    )
    intersections["allocated_population"] = (
        intersections[population_column] * intersections["population_share"]
    )

    population = intersections.groupby("NBHD")["allocated_population"].sum()
    population = population.reindex(neighborhoods["NBHD"].sort_values().unique(), fill_value=0.0)
    return {name: float(value) for name, value in population.items()}


@lru_cache(maxsize=1)
def load_somerville_crime() -> pd.DataFrame:
    df = pd.read_csv(SOMERVILLE_CRIME_CSV)
    day_month = df["Day and Month Reported"].fillna("").astype(str).str.strip()
    year_part = df["Year Reported"].astype(str)
    df["Date"] = day_month.where(day_month.ne(""), "01/01") + "/" + year_part
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df[["Date", "Offense Type", "Block Code"]].copy()
    df["City"] = "Somerville"
    df["Crime"] = df["Offense Type"].astype(str).str.title()
    df["Macro Crime"] = df["Crime"].map(SOMERVILLE_CRIME_MACROS)
    df["Block Code"] = df["Block Code"].astype(str).str.rstrip(".0")

    somerville_blocks = load_somerville_blocks()
    df = df.merge(
        somerville_blocks[["GEOID20", "geometry"]],
        left_on="Block Code",
        right_on="GEOID20",
        how="left",
    )
    df = gpd.GeoDataFrame(df, geometry="geometry", crs=somerville_blocks.crs)

    neighborhoods = load_somerville_geo()[["NBHD", "geometry"]]
    df = gpd.sjoin(df, neighborhoods, how="left", predicate="intersects")
    df = df.rename(columns={"NBHD": "Neighborhood"})
    df = df.drop(columns=["geometry", "Block Code", "GEOID20", "index_right"], errors="ignore")
    return df[["City", "Date", "Crime", "Macro Crime", "Neighborhood"]]


def get_cambridge_bundle() -> dict[str, object]:
    return {
        "crime": load_cambridge_crime(),
        "geo": load_cambridge_geo(),
        "population": CAMBRIDGE_POP_2020,
        "zoom": 13,
        "population_year": "2020",
    }


def get_boston_bundle() -> dict[str, object]:
    return {
        "crime": load_boston_crime(),
        "geo": load_boston_geo(),
        "population": load_boston_population(),
        "zoom": 12,
        "population_year": "2019",
    }


def get_somerville_bundle() -> dict[str, object]:
    return {
        "crime": load_somerville_crime(),
        "geo": load_somerville_geo(),
        "population": load_somerville_population(),
        "zoom": 13,
        "population_year": "2020 block population allocated to neighborhoods",
    }


def get_all_metro_bundle() -> dict[str, object]:
    bundles = [get_cambridge_bundle(), get_boston_bundle()]
    try:
        bundles.append(get_somerville_bundle())
    except Exception:
        pass

    crime_data = pd.concat([bundle["crime"] for bundle in bundles], ignore_index=True)
    geo_df = gpd.GeoDataFrame(
        pd.concat([bundle["geo"] for bundle in bundles], ignore_index=True),
        crs=bundles[0]["geo"].crs,
    )

    population: dict[str, float] = {}
    for bundle in bundles:
        population.update(bundle["population"])

    years = ", ".join(bundle["population_year"] for bundle in bundles)
    return {
        "crime": crime_data,
        "geo": geo_df,
        "population": population,
        "zoom": 11.5,
        "population_year": years,
    }


def get_supported_municipalities() -> list[str]:
    options = ["All Metro", "Cambridge", "Boston"]
    try:
        get_somerville_bundle()
    except Exception:
        return options
    return [*options, "Somerville"]


def get_bundle(municipality: str) -> dict[str, object]:
    if municipality == "Cambridge":
        return get_cambridge_bundle()
    if municipality == "Boston":
        return get_boston_bundle()
    if municipality == "Somerville":
        return get_somerville_bundle()
    return get_all_metro_bundle()
