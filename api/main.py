from __future__ import annotations

from datetime import date
import os

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from crime_map import (
    apply_rate_guardrails,
    clamp_dates,
    compute_relative_rates,
    filter_crime_by_date,
    get_bundle,
    get_supported_municipalities,
    safe_display_scale_max,
)
from crime_map.offense_mapping import macro_sort_key
from crime_map.payloads import build_metric_geojson, map_center

app = FastAPI(
    title="Crime Map API",
    version="0.1.0",
    description="Live metro Boston neighborhood crime rates backed by official municipal and census data.",
)


def _allowed_origins() -> list[str]:
    configured = os.getenv("CRIME_MAP_ALLOWED_ORIGINS", "").strip()
    if configured:
        return [origin.strip().rstrip("/") for origin in configured.split(",") if origin.strip()]

    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


def _allowed_origin_regex() -> str | None:
    configured = os.getenv("CRIME_MAP_ALLOWED_ORIGIN_REGEX", "").strip()
    return configured or None

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_origin_regex=_allowed_origin_regex(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _resolve_municipality(municipality: str) -> tuple[str, dict[str, object]]:
    supported = get_supported_municipalities()
    if municipality not in supported:
        raise HTTPException(
            status_code=404,
            detail=f"Unsupported municipality '{municipality}'. Supported values: {supported}",
        )
    return municipality, get_bundle(municipality)


def _macro_options(bundle: dict[str, object]) -> list[str]:
    crime_df = bundle["crime"]
    return sorted(crime_df["Macro Crime"].dropna().unique().tolist(), key=macro_sort_key)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/municipalities")
def list_municipalities() -> dict[str, list[str]]:
    return {"municipalities": get_supported_municipalities()}


@app.get("/api/v1/municipalities/{municipality}/metadata")
def municipality_metadata(municipality: str) -> dict[str, object]:
    municipality, bundle = _resolve_municipality(municipality)
    crime_df = bundle["crime"]
    macro_options = _macro_options(bundle)
    default_macro = "Violent Crime" if "Violent Crime" in macro_options else macro_options[0]

    return {
        "municipality": municipality,
        "macro_options": macro_options,
        "default_macro": default_macro,
        "zoom": bundle["zoom"],
        "center": map_center(bundle["geo"]),
        "population_year": bundle["population_year"],
        "min_date": crime_df["Date"].min().date().isoformat(),
        "max_date": crime_df["Date"].max().date().isoformat(),
    }


@app.get("/api/v1/municipalities/{municipality}/choropleth")
def municipality_choropleth(
    municipality: str,
    macro: str | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
) -> dict[str, object]:
    municipality, bundle = _resolve_municipality(municipality)
    crime_df = bundle["crime"]
    geo_df = bundle["geo"]
    population = bundle["population"]
    macro_options = _macro_options(bundle)

    if not macro_options:
        raise HTTPException(status_code=400, detail="No macro crime categories are available.")

    if macro is None:
        selected_macro = "Violent Crime" if "Violent Crime" in macro_options else macro_options[0]
    elif macro in macro_options:
        selected_macro = macro
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported macro '{macro}'. Supported values: {macro_options}",
        )

    start_date, end_date = clamp_dates(start_date, end_date)
    filtered_crime = filter_crime_by_date(crime_df, start_date, end_date)
    if filtered_crime.empty:
        rates_df = pd.DataFrame({selected_macro: 0.0}, index=population.keys())
    else:
        rates_df = compute_relative_rates(filtered_crime, population)

    if selected_macro not in rates_df.columns:
        rates_df = pd.DataFrame({selected_macro: 0.0}, index=population.keys())

    rates_df, valid_population_mask = apply_rate_guardrails(rates_df, population)
    scale_max = safe_display_scale_max(rates_df[selected_macro])

    return {
        "municipality": municipality,
        "selected_macro": selected_macro,
        "zoom": bundle["zoom"],
        "center": map_center(geo_df),
        "population_year": bundle["population_year"],
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
        "scale_max": scale_max,
        "excluded_area_count": int((~valid_population_mask).sum()),
        "incident_count": int(
            filtered_crime["Incident_Count"].sum() if "Incident_Count" in filtered_crime.columns else len(filtered_crime)
        ),
        "geojson": build_metric_geojson(
            geo_df=geo_df,
            rates_df=rates_df,
            population=population,
            selected_macro=selected_macro,
            valid_population_mask=valid_population_mask,
        ),
    }
