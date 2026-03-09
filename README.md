# Crime Map

Single canonical crime-map pipeline for Cambridge, Boston, and Somerville.

This refactor removes local static data dependencies from active code paths and uses
live official web sources with local caching.

## Project structure

- `crime_map/`: shared data ingestion, normalization, metrics, and map rendering
- `app/crime_map_app.py`: Streamlit UI
- `notebook/Crime Map - Notebook.ipynb`: function-driven analysis playground
- `old/`: archived legacy local datasets and prior notebook snapshot

## Live data sources

- Cambridge crime: `data.cambridgema.gov` (`xuad-73uj`)
- Cambridge neighborhoods: `data.cambridgema.gov` (`k3pi-9823`)
- Boston crime: `data.boston.gov` CKAN package (`6220d948-eae2-4e4b-8723-2dc8e67722a3`)
- Boston neighborhoods: `data.boston.gov` 2020 block-group approximated neighborhoods
- Somerville crime: `data.somervillema.gov` (`aghs-hqvg`)
- Somerville neighborhoods: `data.somervillema.gov` file asset (`n5md-vqta`)
- Population: U.S. Census 2020 P.L. block population API + TIGER2020PL block geometries

Population is area-allocated from census blocks to city neighborhoods for all municipalities.

## Run locally

```powershell
pip install -r requirements.txt
streamlit run app/crime_map_app.py
```

## Notes

- Downloads are cached under `.cache/crime_map/`.
- The map keys by `City::Neighborhood` to avoid cross-city key collisions and improve
  reliability for Boston and All Metro rendering.
