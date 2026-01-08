from __future__ import annotations

from datetime import date

import folium
import pandas as pd


def clamp_dates(start_date: date, end_date: date) -> tuple[date, date]:
    if start_date and end_date and start_date > end_date:
        return end_date, start_date
    return start_date, end_date


def filter_crime_by_date(crime_df: pd.DataFrame, start_date: date, end_date: date) -> pd.DataFrame:
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    return crime_df[(crime_df["Date"] >= start_dt) & (crime_df["Date"] <= end_dt)].copy()


def compute_relative_rates(
    filtered_crime: pd.DataFrame, population: dict[str, float]
) -> pd.DataFrame:
    crime_table_macro = (
        filtered_crime.groupby(["Neighborhood", "Macro Crime"]).size().unstack("Macro Crime").fillna(0)
    )
    return crime_table_macro.div(pd.Series(population), axis=0)


def build_choropleth_map(
    geo_df: pd.DataFrame,
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
    geo_df_selected[selected_macro] = geo_df_selected[selected_macro].round(5)

    geo_json = geo_df_selected.to_json()
    center_coords = geo_df.geometry.centroid.y.mean(), geo_df.geometry.centroid.x.mean()
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
        style_function=lambda x: {"fillColor": "transparent", "color": "transparent"},
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
