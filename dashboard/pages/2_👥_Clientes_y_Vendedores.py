import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.api import fetch_view
import plotly.express as px
import json
from urllib.request import urlopen

st.subheader("📊 Retención por cohorte")

df_cohort = fetch_view("retention_cohorts")
df_cohort["cohort_month"] = pd.to_datetime(df_cohort["cohort_month"]).dt.strftime("%Y-%m")

max_period = st.slider(
    "Meses a mostrar",
    min_value=3,
    max_value=int(df_cohort["period_number"].max()),
    value=12
)

# Excluimos period_number=0: siempre es 100% por definición (no aporta info real)
# y aplastaría la escala de color del resto de los valores
df_filtered = df_cohort[(df_cohort["period_number"] >= 1) & (df_cohort["period_number"] <= max_period)]

pivot = df_filtered.pivot(
    index="cohort_month",
    columns="period_number",
    values="retention_pct"
).sort_index(ascending=False)

zmax_dynamic = pivot.max().max()

fig_cohort = go.Figure(data=go.Heatmap(
    z=pivot.values,
    x=[f"Mes {i}" for i in pivot.columns],
    y=pivot.index,
    colorscale="Blues",
    zmin=0,
    zmax=zmax_dynamic,
    hoverongaps=False,
    hovertemplate="Cohorte: %{y}<br>%{x}<br>Retención: %{z}%<extra></extra>",
    colorbar=dict(title="% Retención")
))

fig_cohort.update_layout(
    xaxis_title="Meses desde primera compra",
    yaxis_title="Cohorte",
    height=600
)

st.plotly_chart(fig_cohort, use_container_width=True)

st.caption(
    "Se omite el mes 0 (100% por definición, ya que es la cohorte completa en su mes de origen). "
    "Las celdas vacías indican combinaciones cohorte/período sin datos observables: "
    "el período aún no ocurrió dentro de la ventana del dataset, o ningún cliente de esa "
    "cohorte volvió a comprar en ese mes."
)