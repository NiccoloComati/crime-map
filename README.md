# Crime Map

Canonical crime-map pipeline for Cambridge, Boston, and Somerville, backed by live official web sources.

The active app stack is:

- `api/`: FastAPI backend for a real browser app
- `frontend/`: Next.js frontend with Leaflet rendering

The old Streamlit UI is archived under `old/legacy-streamlit-app/` and is no longer part of the active deployment path.

## Architecture

- `crime_map/`: shared ingestion, normalization, metrics, caching, and payload shaping
- `api/main.py`: HTTP API over the shared Python crime pipeline
- `frontend/`: React/Next client that consumes the API and renders the map in-browser
- `notebook/Crime Map - Notebook.ipynb`: local analysis notebook
- `old/`: archived local datasets, old notebook snapshot, and retired Streamlit UI

## Live data sources

- Cambridge crime: `data.cambridgema.gov` (`xuad-73uj`)
- Cambridge neighborhoods: `data.cambridgema.gov` (`k3pi-9823`)
- Boston crime: `data.boston.gov` CKAN package (`6220d948-eae2-4e4b-8723-2dc8e67722a3`)
- Boston neighborhoods: `data.boston.gov` 2020 block-group approximated neighborhoods
- Somerville crime: `data.somervillema.gov` (`aghs-hqvg`)
- Somerville neighborhoods: `data.somervillema.gov` file asset (`n5md-vqta`)
- Population: U.S. Census 2020 P.L. block population API + TIGER2020PL block geometries

Population is area-allocated from census blocks to city neighborhoods for all municipalities.

## Local development

### Backend API

```powershell
pip install -r requirements.txt
python -m uvicorn api.main:app --reload
```

To allow deployed frontend domains, set:

- `CRIME_MAP_ALLOWED_ORIGINS`: comma-separated exact origins
- `CRIME_MAP_ALLOWED_ORIGIN_REGEX`: optional regex for preview domains

Useful endpoints:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/api/v1/municipalities`
- `http://127.0.0.1:8000/api/v1/municipalities/All%20Metro/metadata`

### Frontend web app

Requirements:

- Node.js 20+

```powershell
cd frontend
copy .env.example .env.local
npm install
npm run dev
```

Then open:

- `http://127.0.0.1:3000`

By default the frontend expects the API at `http://127.0.0.1:8000`.

## Deployment

Deployment is now split:

- frontend: Vercel Hobby
- API: Render Free by default

Exact project files and steps are in `DEPLOY.md`.

## Notes

- Downloads are cached under `.cache/crime_map/`.
- The data key is `City::Neighborhood` to avoid cross-city collisions and improve Boston and All Metro rendering reliability.
- The API and notebook reuse the same shared Python pipeline, so there is one canonical data flow instead of duplicated logic.
