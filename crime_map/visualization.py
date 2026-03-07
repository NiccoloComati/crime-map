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
    return centroids.y.mean(), centroids.x.mean()


def build_choropleth_map(
    geo_df: gpd.GeoDataFrame,
    rates_df: pd.DataFrame,
    population: dict[str, float],
    selected_macro: str,
    zoom_start: float,
    population_year: str,
) -> folium.Map:
    pop_df = pd.DataFrame.from_dict(population, orient="index", columns=["Population"])
    pop_df.index.name = "Neighborhood"
    pop_df = pop_df.reset_index()

    geo_df_selected = geo_df.merge(
        rates_df[[selected_macro]], how="left", left_on="Mapped_Name", right_index=True
    )
    geo_df_selected = geo_df_selected.merge(
        pop_df, how="left", left_on="Mapped_Name", right_on="Neighborhood"
    )
    geo_df_selected[selected_macro] = pd.to_numeric(
        geo_df_selected[selected_macro], errors="coerce"
    ).replace([np.inf, -np.inf], np.nan)
    geo_df_selected[selected_macro] = geo_df_selected[selected_macro].fillna(0.0).round(5)

    geo_json = geo_df_selected.to_json()
    center_coords = _map_center(geo_df)
    folium_map = folium.Map(location=center_coords, zoom_start=zoom_start)

    folium.Choropleth(
        geo_data=geo_json,
        data=geo_df_selected,
        columns=["Mapped_Name", selected_macro],
        key_on="feature.properties.Mapped_Name",
        fill_color="YlOrRd",
        fill_opacity=0.65,
        line_opacity=0.4,
        legend_name=f"Relative {selected_macro} Rate ({population_year})",
    ).add_to(folium_map)

    folium.GeoJson(
        geo_json,
        style_function=lambda _: {"fillColor": "transparent", "color": "transparent"},
        tooltip=folium.GeoJsonTooltip(
            fields=["Mapped_Name", selected_macro, "Population"],
            aliases=["Neighborhood:", f"{selected_macro} Score:", f"Population ({population_year}):"],
            style=(
                "background-color: white; color: #333333; font-family: arial; "
                "font-size: 12px; padding: 10px;"
            ),
        ),
    ).add_to(folium_map)

    return folium_map
