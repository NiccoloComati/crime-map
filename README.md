# Crime Map

This repo now has one canonical implementation of the crime map pipeline.

- Shared logic lives in `crime_map/`.
- The Streamlit UI lives at `app/crime_map_app.py`.
- The historical notebook is preserved at `0. Test/Crime Map - Notebook.ipynb`, with newer sections appended below the original work.

## Run locally

```powershell
cd "crime-map"
pip install -r requirements.txt
streamlit run app/crime_map_app.py
```

The app and notebook both read the same code and the same repo-local raw data.
