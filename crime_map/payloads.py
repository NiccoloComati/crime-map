from __future__ import annotations

import json
from typing import Any

import geopandas as gpd
import numpy as np
import pandas as pd

AREA_CRS = "EPSG:26986"
TARGET_CRS = "EPSG:4326"


def map_center(geo_df: gpd.GeoDataFrame) -> list[float]:
    projected = geo_df.to_crs(AREA_CRS)
    centroids = gpd.GeoSeries(projected.geometry.centroid, crs=AREA_CRS).to_crs(TARGET_CRS)
    return [float(centroids.y.mean()), float(centroids.x.mean())]


def build_metric_geojson(
    geo_df: gpd.GeoDataFrame,
    rates_df: pd.DataFrame,
    population: dict[str, float],
    selected_macro: str,
    valid_population_mask: pd.Series | None = None,
) -> dict[str, Any]:
    pop_df = pd.DataFrame(
        {
            "GeoKey": list(population.keys()),
            "Population": list(population.values()),
        }
    )

    geo_df_selected = geo_df.copy()
    if selected_macro in rates_df.columns:
        metric_values = rates_df[[selected_macro]].copy()
    else:
        metric_values = pd.DataFrame({selected_macro: 0.0}, index=rates_df.index)

    geo_df_selected = geo_df_selected.merge(
        metric_values,
        how="left",
        left_on="GeoKey",
        right_index=True,
    )
    geo_df_selected = geo_df_selected.merge(pop_df, how="left", on="GeoKey")
    geo_df_selected[selected_macro] = pd.to_numeric(
        geo_df_selected[selected_macro], errors="coerce"
    ).replace([np.inf, -np.inf], np.nan)
    geo_df_selected[selected_macro] = geo_df_selected[selected_macro].fillna(0.0).round(6)
    geo_df_selected["Population"] = pd.to_numeric(
        geo_df_selected["Population"], errors="coerce"
    ).fillna(0.0)
    geo_df_selected = geo_df_selected.rename(columns={selected_macro: "metric_value"})
    if valid_population_mask is None:
        geo_df_selected["is_rate_valid"] = True
    else:
        mask_lookup = valid_population_mask.reindex(geo_df_selected["GeoKey"]).fillna(False)
        geo_df_selected["is_rate_valid"] = mask_lookup.astype(bool).to_numpy()
        geo_df_selected.loc[~geo_df_selected["is_rate_valid"], "metric_value"] = np.nan

    columns = ["City", "Mapped_Name", "GeoKey", "Population", "metric_value", "is_rate_valid", "geometry"]
    return json.loads(geo_df_selected[columns].to_json())
