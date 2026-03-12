"""Canonical crime map package shared by the app and notebooks."""

from .coverage import coverage_payload, get_supported_municipality_names, municipality_label
from .data import get_bundle, get_supported_municipalities, reset_state, warm_processed_cache
from .metrics import (
    apply_rate_guardrails,
    clamp_dates,
    compute_relative_rates,
    filter_crime_by_date,
    safe_display_scale_max,
)


def build_choropleth_map(*args, **kwargs):
    from .visualization import build_choropleth_map as _build_choropleth_map

    return _build_choropleth_map(*args, **kwargs)

__all__ = [
    "build_choropleth_map",
    "apply_rate_guardrails",
    "clamp_dates",
    "compute_relative_rates",
    "coverage_payload",
    "filter_crime_by_date",
    "get_bundle",
    "get_supported_municipality_names",
    "get_supported_municipalities",
    "municipality_label",
    "reset_state",
    "safe_display_scale_max",
    "warm_processed_cache",
]
