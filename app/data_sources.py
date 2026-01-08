from __future__ import annotations

from functools import lru_cache

import geopandas as gpd
import pandas as pd

from config import (
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
    SOMERVILLE_TOTAL_POP_2022,
)


@lru_cache(maxsize=1)
def load_cambridge_crime() -> pd.DataFrame:
    df = pd.read_csv(CAMBRIDGE_CRIME_CSV)
    df = df[["Crime Date Time", "Crime", "Neighborhood", "Reporting Area"]].copy()
    df["Date"] = pd.to_datetime(df["Crime Date Time"].str.split(" ").str[0])
    df["Macro Crime"] = df["Crime"].map(CAMBRIDGE_CRIME_MACROS)
    return df


@lru_cache(maxsize=1)
def load_cambridge_geo() -> gpd.GeoDataFrame:
    geo_df = gpd.read_file(CAMBRIDGE_SHAPEFILE)
    if geo_df.crs != "EPSG:4326":
        geo_df = geo_df.to_crs(epsg=4326)
    geo_df["Mapped_Name"] = geo_df["NAME"].map(CAMBRIDGE_NEIGHBORHOOD_NAME_MAP)
    return geo_df


@lru_cache(maxsize=1)
def load_boston_crime() -> pd.DataFrame:
    df = pd.read_csv(BOSTON_CRIME_CSV)
    df = df[["From Date", "Crime", "Neighborhood", "BPD District"]].copy()
    df["Date"] = pd.to_datetime(df["From Date"].str.split(" ").str[0])
    df["Crime"] = df["Crime"].str.title()
    df["Macro Crime"] = df["Crime"].map(BOSTON_CRIME_MACROS)
    df["Mapped_Neighborhood"] = (
        df["Neighborhood"].map(BOSTON_NEIGHBORHOOD_NAME_MAP).fillna(df["Neighborhood"])
    )
    return df


@lru_cache(maxsize=1)
def load_boston_population() -> dict[str, float]:
    df = pd.read_excel(BOSTON_POP_XLSM, header=2)
    df.set_index("Unnamed: 0", inplace=True)
    pop_dict = df.loc["Allston":"West Roxbury", "Total Population"].to_dict()
    return {k.strip(): v for k, v in pop_dict.items()}


@lru_cache(maxsize=1)
def load_boston_geo() -> gpd.GeoDataFrame:
    geo_df = gpd.read_file(BOSTON_SHAPEFILE)
    if geo_df.crs != "EPSG:4326":
        geo_df = geo_df.to_crs(epsg=4326)
    geo_df["Mapped_Name"] = geo_df["blockgr202"].map(BOSTON_NEIGHBORHOOD_NAME_MAP).fillna(
        geo_df["blockgr202"]
    )
    return geo_df


def _build_area_weighted_population(geo_df: gpd.GeoDataFrame, total_population: int) -> dict[str, float]:
    area_df = geo_df.to_crs(epsg=26986)
    area_df["area"] = area_df.geometry.area
    total_area = area_df["area"].sum()
    if total_area == 0:
        return {name: float(total_population) for name in geo_df["NBHD"].dropna().unique()}
    area_df["pop"] = area_df["area"] / total_area * total_population
    return area_df.set_index("NBHD")["pop"].to_dict()


@lru_cache(maxsize=1)
def load_somerville_geo() -> gpd.GeoDataFrame:
    geo_df = gpd.read_file(SOMERVILLE_SHAPEFILE)
    if geo_df.crs != "EPSG:4326":
        geo_df = geo_df.to_crs(epsg=4326)
    geo_df["Mapped_Name"] = geo_df["NBHD"]
    return geo_df


@lru_cache(maxsize=1)
def load_somerville_crime() -> pd.DataFrame:
    df = pd.read_csv(SOMERVILLE_CRIME_CSV)
    day_month = df["Day and Month Reported"].fillna("").astype(str).str.strip()
    year_part = df["Year Reported"].astype(str)
    df["Date"] = day_month.where(day_month.ne(""), "01/01") + "/" + year_part
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df[["Date", "Offense Type", "Block Code"]].copy()
    df["Crime"] = df["Offense Type"].astype(str).str.title()
    df["Macro Crime"] = df["Crime"].map(SOMERVILLE_CRIME_MACROS)
    df["Block Code"] = df["Block Code"].astype(str).str.rstrip(".0")

    blocks = gpd.read_file(MA_CENSUS_BLOCKS)
    somerville_blocks = blocks[blocks["TOWN"] == "SOMERVILLE"].copy()
    if somerville_blocks.crs != "EPSG:4326":
        somerville_blocks = somerville_blocks.to_crs(epsg=4326)

    df = df.merge(
        somerville_blocks[["GEOID20", "geometry"]],
        left_on="Block Code",
        right_on="GEOID20",
        how="left",
    )
    df = gpd.GeoDataFrame(df, geometry="geometry")
    geo_df = load_somerville_geo()
    df = gpd.sjoin(df, geo_df[["NBHD", "geometry"]], how="left", predicate="intersects")
    df = df.rename(columns={"NBHD": "Neighborhood"})
    df = df.drop(columns=["geometry", "Block Code", "GEOID20", "index_right"], errors="ignore")
    return df[["Date", "Crime", "Macro Crime", "Neighborhood"]]


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
    geo_df = load_somerville_geo()
    population = _build_area_weighted_population(geo_df, SOMERVILLE_TOTAL_POP_2022)
    return {
        "crime": load_somerville_crime(),
        "geo": geo_df,
        "population": population,
        "zoom": 13,
        "population_year": "2022 (area-weighted)",
    }


def get_all_metro_bundle() -> dict[str, object]:
    cambridge = get_cambridge_bundle()
    boston = get_boston_bundle()
    somerville = get_somerville_bundle()
    crime_data = pd.concat(
        [cambridge["crime"], boston["crime"], somerville["crime"]], ignore_index=True
    )

    geo_df = gpd.GeoDataFrame(
        pd.concat(
            [
                cambridge["geo"].assign(City="Cambridge"),
                boston["geo"].assign(City="Boston"),
                somerville["geo"].assign(City="Somerville"),
            ],
            ignore_index=True,
        ),
        crs=cambridge["geo"].crs,
    )

    population = {
        **cambridge["population"],
        **boston["population"],
        **somerville["population"],
    }
    return {
        "crime": crime_data,
        "geo": geo_df,
        "population": population,
        "zoom": 11.5,
        "population_year": "2020, 2019, 2022",
    }


def get_bundle(municipality: str) -> dict[str, object]:
    if municipality == "Cambridge":
        return get_cambridge_bundle()
    if municipality == "Boston":
        return get_boston_bundle()
    if municipality == "Somerville":
        return get_somerville_bundle()
    return get_all_metro_bundle()
