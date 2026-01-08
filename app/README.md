# Crime Map App

This folder contains an app-style rewrite of the crime map notebook, built with
modular Python files and a Streamlit entrypoint.

## Run locally

```powershell
cd "crime-map"
pip install -r requirements.txt
streamlit run app/crime_map_app.py
```

The app reads data from the repo root (Boston, Cambridge, and Somerville
data and shapefiles).
