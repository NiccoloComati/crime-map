from __future__ import annotations

import folium
import geopandas as gpd
import numpy as np
import pandas as pd

AREA_CRS = "EPSG:26986"
TARGET_CRS = "EPSG:4326"


def _map_center(geo_df: gpd.GeoDataFrame) -> tuple[float, float]:
    projected = geo_df.to_crs(AREA_CRS)
    centroids = gpd.GeoSeries(projected.geometry.centroid, crs=AREA_CRS).to_crs(TARGET_CRS)
    return float(centroids.y.mean()), float(centroids.x.mean())


def build_choropleth_map(
    geo_df: gpd.GeoDataFrame,
    rates_df: pd.DataFrame,
    population: dict[str, float],
    selected_macro: str,
    zoom_start: float,
    population_year: str,
) -> folium.Map:
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

    geo_json = geo_df_selected.to_json()
    center_coords = _map_center(geo_df_selected)
    folium_map = folium.Map(location=center_coords, zoom_start=zoom_start, tiles="CartoDB positron")

    folium.Choropleth(
        geo_data=geo_json,
        data=geo_df_selected,
        columns=["GeoKey", selected_macro],
        key_on="feature.properties.GeoKey",
        fill_color="YlOrRd",
        fill_opacity=0.68,
        line_opacity=0.35,
        legend_name=f"Relative {selected_macro} Rate ({population_year})",
        nan_fill_color="lightgray",
        nan_fill_opacity=0.45,
    ).add_to(folium_map)

    folium.GeoJson(
        geo_json,
        style_function=lambda _: {"fillColor": "transparent", "color": "transparent", "weight": 0},
        tooltip=folium.GeoJsonTooltip(
            fields=["City", "Mapped_Name", selected_macro, "Population"],
            aliases=["City:", "Neighborhood:", f"{selected_macro} Score:", f"Population ({population_year}):"],
            localize=True,
            sticky=False,
            labels=True,
            style=(
                "background-color: white; color: #2b2b2b; font-family: sans-serif; "
                "font-size: 12px; padding: 8px;"
            ),
        ),
    ).add_to(folium_map)

    return folium_map
