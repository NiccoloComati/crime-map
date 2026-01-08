from datetime import date

import pandas as pd
import streamlit as st
from streamlit.components.v1 import html

from data_sources import get_bundle
from maps import build_choropleth_map, clamp_dates, compute_relative_rates, filter_crime_by_date


st.set_page_config(page_title="Crime Map", layout="wide")

st.title("Metro Crime Map")
st.caption("Interactive neighborhood crime rates for Cambridge and Boston.")

municipality = st.selectbox(
    "City",
    options=["All Metro", "Cambridge", "Boston"],
    index=0,
)

bundle = get_bundle(municipality)
crime_df = bundle["crime"]
geo_df = bundle["geo"]
population = bundle["population"]
zoom_start = bundle["zoom"]
population_year = bundle["population_year"]

macro_options = sorted(crime_df["Macro Crime"].dropna().unique().tolist())
if not macro_options:
    st.error("No macro crime categories found for the selected city.")
    st.stop()
default_macro = "Violent Crime" if "Violent Crime" in macro_options else macro_options[0]
selected_macro = st.selectbox("Crime", options=macro_options, index=macro_options.index(default_macro))

min_date = crime_df["Date"].min().date()
max_date = crime_df["Date"].max().date()
default_start = max(min_date, date(2015, 1, 1))
default_end = min(max_date, date(2025, 1, 7))

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", value=default_start, min_value=min_date, max_value=max_date)
with col2:
    end_date = st.date_input("End Date", value=default_end, min_value=min_date, max_value=max_date)

start_date, end_date = clamp_dates(start_date, end_date)

filtered_crime = filter_crime_by_date(crime_df, start_date, end_date)
if filtered_crime.empty:
    st.warning("No incidents found for the selected date range.")
    rates_df = pd.DataFrame({selected_macro: 0.0}, index=population.keys())
else:
    rates_df = compute_relative_rates(filtered_crime, population)

if rates_df is None or selected_macro not in rates_df.columns:
    rates_df = pd.DataFrame({selected_macro: 0.0}, index=population.keys())

folium_map = build_choropleth_map(
    geo_df=geo_df,
    rates_df=rates_df,
    population=population,
    selected_macro=selected_macro,
    zoom_start=zoom_start,
    population_year=population_year,
)

html(folium_map._repr_html_(), height=700, width=None)
