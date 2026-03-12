from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

MIN_EFFECTIVE_POPULATION = 100.0
DISPLAY_SCALE_QUANTILE = 0.98
DISPLAY_SCALE_MIN_FEATURES = 8


def clamp_dates(start_date: date, end_date: date) -> tuple[date, date]:
    if start_date and end_date and start_date > end_date:
        return end_date, start_date
    return start_date, end_date


def filter_crime_by_date(crime_df: pd.DataFrame, start_date: date, end_date: date) -> pd.DataFrame:
    filtered = crime_df.copy()
    if start_date is not None:
        start_dt = pd.to_datetime(start_date)
        filtered = filtered[filtered["Date"] >= start_dt]
    if end_date is not None:
        end_dt = pd.to_datetime(end_date)
        filtered = filtered[filtered["Date"] <= end_dt]
    return filtered.copy()


def compute_relative_rates(
    filtered_crime: pd.DataFrame, population: dict[str, float]
) -> pd.DataFrame:
    if "Incident_Count" in filtered_crime.columns:
        crime_table_macro = (
            filtered_crime.groupby(["GeoKey", "Macro Crime"], observed=False)["Incident_Count"]
            .sum()
            .unstack("Macro Crime")
            .fillna(0)
        )
    else:
        crime_table_macro = (
            filtered_crime.groupby(["GeoKey", "Macro Crime"], observed=False)
            .size()
            .unstack("Macro Crime")
            .fillna(0)
        )
    population_series = pd.Series(population, dtype="float64")
    rates = crime_table_macro.reindex(population_series.index, fill_value=0).div(population_series, axis=0)
    rates = rates.replace([np.inf, -np.inf], np.nan)
    return rates.clip(lower=0.0)


def population_is_rate_valid(population: dict[str, float]) -> pd.Series:
    population_series = pd.Series(population, dtype="float64")
    return population_series.ge(MIN_EFFECTIVE_POPULATION) & population_series.notna() & np.isfinite(population_series)


def apply_rate_guardrails(
    rates_df: pd.DataFrame,
    population: dict[str, float],
) -> tuple[pd.DataFrame, pd.Series]:
    valid_population_mask = population_is_rate_valid(population)
    safe_rates = rates_df.reindex(valid_population_mask.index, fill_value=0.0).copy()
    safe_rates = safe_rates.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
    safe_rates = safe_rates.clip(lower=0.0)
    return safe_rates.where(valid_population_mask, np.nan), valid_population_mask


def safe_display_scale_max(metric_values: pd.Series) -> float:
    valid_values = (
        pd.to_numeric(metric_values, errors="coerce")
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
    )

    if valid_values.empty:
        return 0.0

    absolute_max = float(valid_values.max())
    if len(valid_values) < DISPLAY_SCALE_MIN_FEATURES:
        return absolute_max

    percentile_max = float(valid_values.quantile(DISPLAY_SCALE_QUANTILE))
    if not np.isfinite(percentile_max) or percentile_max <= 0:
        return absolute_max

    return min(absolute_max, max(percentile_max, absolute_max * 0.4))
