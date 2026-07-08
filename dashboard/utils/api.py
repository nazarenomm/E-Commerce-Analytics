import streamlit as st
import requests
import pandas as pd
import json
from urllib.request import urlopen

BASE_URL = st.secrets["SUPABASE_URL"] + "/rest/v1"
HEADERS = {
    "apikey": st.secrets["SUPABASE_KEY"],
    "Authorization": f"Bearer {st.secrets['SUPABASE_KEY']}"
}

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_view(view_name: str) -> pd.DataFrame:
    """Trae todas las filas de una vista/tabla expuesta por PostgREST."""
    response = requests.get(
        f"{BASE_URL}/{view_name}",
        headers=HEADERS,
        params={"select": "*"}
    )
    response.raise_for_status()
    return pd.DataFrame(response.json())


def fetch_views(view_names: list[str]) -> dict[str, pd.DataFrame]:
    """Trae múltiples vistas de una sola vez, con un único spinner."""
    with st.spinner(f"Cargando datos ({len(view_names)} vistas)..."):
        return {name: fetch_view(name) for name in view_names}

@st.cache_data(ttl=86400)
def load_brazil_geojson():
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    with urlopen(url) as response:
        return json.load(response)
    
@st.cache_data(ttl=86400)
def build_uf_name_map(geojson):
    return {
        feature["properties"]["sigla"]: feature["properties"]["name"]
        for feature in geojson["features"]
    }