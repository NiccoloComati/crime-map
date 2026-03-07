from __future__ import annotations

from datetime import date

import numpy as np
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
    population_series = pd.Series(population, dtype="float64")
    population_series = population_series.where(population_series > 0, np.nan)
    rates = crime_table_macro.reindex(population_series.index, fill_value=0).div(population_series, axis=0)
    rates = rates.replace([np.inf, -np.inf], np.nan)
    return rates.fillna(0.0)
