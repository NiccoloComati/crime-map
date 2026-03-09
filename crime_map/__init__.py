"""Canonical crime map package shared by the app and notebooks."""

from .data import get_bundle, get_supported_municipalities, reset_state
from .metrics import clamp_dates, compute_relative_rates, filter_crime_by_date
from .visualization import build_choropleth_map

__all__ = [
    "build_choropleth_map",
    "clamp_dates",
    "compute_relative_rates",
    "filter_crime_by_date",
    "get_bundle",
    "get_supported_municipalities",
    "reset_state",
]
