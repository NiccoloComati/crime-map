# Codex Context

## Product

- Repository: `crime-map`
- Active app: FastAPI backend + Next.js frontend
- Archived app: `old/` Streamlit implementation is not the product

## Architecture

- Backend entrypoint: `api/main.py`
- Data pipeline: `crime_map/data.py`
- Crime taxonomy: `crime_map/offense_mapping.py`
- Metrics and guardrails: `crime_map/metrics.py`
- Frontend app: `frontend/`
- Map rendering is browser-side with Leaflet-style tiles and choropleth polygons

## Data Model

- Runtime stores aggregated incident counts, not raw incidents
- Crime is grouped into standardized macro categories through `crime_map/offense_mapping.py`
- Population comes from 2020 Census block population, area-allocated to neighborhood polygons
- Areas with extremely small resident population are excluded from stable rate ranking and rendered neutral

## Deployment

- Frontend: Vercel
- Backend: Render
- Vercel project metadata is in `.vercel/project.json`
- Render service name: `crime-map-api`
- Render service URL: `https://crime-map-api-epxb.onrender.com`
- As of 2026-03-12, Render `autoDeploy` was off and manual deploys may be required unless that setting is changed

## Recent Backend Stability Work

- Aggregated crime bundle tables were compacted with categorical columns and `int32` counts
- Processed bundles are cached per municipality instead of loading the whole metro cache on first request
- Prewarmed processed bundles are versioned and do not expire on a time window during runtime

## Frontend State

- Product name: `Metro Crime Atlas`
- Current design direction is polished, direct, and non-demo-like
- Choropleth uses proportional robust-linear scaling with small-population safeguards
- The map currently uses a CARTO basemap and partially transparent polygon fills

## User Preferences

- Prefer practical fixes over overengineering
- Prefer one clean canonical implementation
- Prefer fast root-cause debugging
- Preserve polished product-level design, not notebook or Streamlit aesthetics
- Keep copy direct and reasonable, not flashy or marketing-heavy

## Working Rule

- If a substantial change affects architecture, deployment, methodology, or product behavior, update this file in the same task so future chats inherit the right context.
