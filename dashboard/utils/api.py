import streamlit as st
import requests
import pandas as pd

BASE_URL = st.secrets["SUPABASE_URL"] + "/rest/v1"
HEADERS = {
    "apikey": st.secrets["SUPABASE_KEY"],
    "Authorization": f"Bearer {st.secrets['SUPABASE_KEY']}"
}

@st.cache_data(ttl=3600)
def fetch_view(view_name: str) -> pd.DataFrame:
    """Trae todas las filas de una vista/tabla expuesta por PostgREST."""
    response = requests.get(
        f"{BASE_URL}/{view_name}",
        headers=HEADERS,
        params={"select": "*"}
    )
    response.raise_for_status()
    return pd.DataFrame(response.json())