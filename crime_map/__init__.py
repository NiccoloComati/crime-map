"""Canonical crime map package shared by the app and notebooks."""

from .data import get_bundle, get_supported_municipalities, reset_state, warm_processed_cache
from .metrics import clamp_dates, compute_relative_rates, filter_crime_by_date


def build_choropleth_map(*args, **kwargs):
    from .visualization import build_choropleth_map as _build_choropleth_map

    return _build_choropleth_map(*args, **kwargs)

__all__ = [
    "build_choropleth_map",
    "clamp_dates",
    "compute_relative_rates",
    "filter_crime_by_date",
    "get_bundle",
    "get_supported_municipalities",
    "reset_state",
    "warm_processed_cache",
]
