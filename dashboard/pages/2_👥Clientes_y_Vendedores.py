import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.api import fetch_view
import plotly.express as px
import json
from urllib.request import urlopen

#%% RETENTION COHORTS
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

#%% RFM
st.subheader("🎯 Segmentación RFM")

df_rfm = fetch_view("rfm_segments")

df_summary = df_rfm.groupby("segment").agg(
    avg_recency=("recency_days", "mean"),
    avg_frequency=("frequency", "mean"),
    avg_monetary=("monetary", "mean"),
    customer_count=("customer_unique_id", "count")
).reset_index()

segment_colors = {
    "champions": "#2ca02c",
    "loyal": "#1f77b4",
    "promising": "#ff7f0e",
    "at_risk": "#d62728",
    "others": "#7f7f7f"
}

import numpy as np

col1, col2 = st.columns([3, 2])

with col1:
    fig_rfm = go.Figure()

    # Tamaño de burbuja acotado manualmente entre 20 y 70 px, escalado por sqrt (proporcional a área)
    min_size, max_size = 20, 70
    counts = df_summary["customer_count"].astype(float)
    scaled_sizes = min_size + (np.sqrt(counts) - np.sqrt(counts.min())) / \
                   (np.sqrt(counts.max()) - np.sqrt(counts.min())) * (max_size - min_size)

    for i, (_, row) in enumerate(df_summary.iterrows()):
        fig_rfm.add_trace(go.Scatter(
            x=[row["avg_recency"]],
            y=[row["avg_frequency"]],
            mode="markers+text",
            name=row["segment"],
            text=[row["segment"]],
            textposition="top center",
            marker=dict(
                size=scaled_sizes.iloc[i],
                color=segment_colors.get(row["segment"], "#7f7f7f"),
                opacity=0.75,
                line=dict(width=1, color="white")
            ),
            hovertemplate=(
                f"Segmento: {row['segment']}<br>"
                f"Clientes: {row['customer_count']:,}<br>"
                f"Recency prom: {row['avg_recency']:.1f} días<br>"
                f"Frequency prom: {row['avg_frequency']:.2f}<br>"
                f"Monetary prom: R$ {row['avg_monetary']:,.0f}<extra></extra>"
            )
        ))

    fig_rfm.update_layout(
        xaxis_title="Recency promedio (días)",
        yaxis_title="Frequency promedio (compras)",
        height=450,
        showlegend=False,
        margin=dict(t=40)
    )
    st.plotly_chart(fig_rfm, use_container_width=True)

with col2:
    df_summary_sorted = df_summary.sort_values("customer_count", ascending=True)

    fig_bar = go.Figure(go.Bar(
        x=df_summary_sorted["customer_count"],
        y=df_summary_sorted["segment"],
        orientation="h",
        marker_color=[segment_colors.get(s, "#7f7f7f") for s in df_summary_sorted["segment"]],
        text=df_summary_sorted["customer_count"],
        textposition="outside"
    ))
    fig_bar.update_layout(
        xaxis_title="Cantidad de clientes",
        yaxis_title="",
        height=450,
        margin=dict(t=40, l=100)
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.caption(
    "Izquierda: cada burbuja representa el promedio de Recency/Frequency de todos los "
    "clientes de ese segmento; el tamaño indica la cantidad de clientes. "
    "Derecha: distribución absoluta de clientes por segmento."
)

#%% SELLERS
st.subheader("🏆 Ranking de vendedores")

df_sellers = fetch_view("seller_rankings")

df_sellers_clean = df_sellers.dropna(subset=["avg_review_score"])
sellers_sin_reviews = df_sellers["avg_review_score"].isna().sum()

df_sellers_clean["log_revenue"] = np.log10(df_sellers_clean["total_revenue"].clip(lower=1))

fig_sellers = go.Figure(go.Scatter(
    x=df_sellers_clean["total_orders"],
    y=df_sellers_clean["avg_review_score"],
    mode="markers",
    marker=dict(
        size=8,
        color=df_sellers_clean["log_revenue"],
        colorscale="RdBu",
        showscale=True,
        colorbar=dict(
            title="Revenue (R$)",
            tickvals=[1, 2, 3, 4, 5],
            ticktext=["R$10", "R$100", "R$1K", "R$10K", "R$100K"]
        ),
        opacity=0.6,
        line=dict(width=0.5, color="white")
    ),
    customdata=df_sellers_clean["total_revenue"],
    hovertemplate=(
        "Pedidos: %{x}<br>"
        "Review promedio: %{y:.2f}<br>"
        "Revenue: R$ %{customdata:,.0f}<extra></extra>"
    )
))

median_orders = df_sellers_clean["total_orders"].median()
median_review = df_sellers_clean["avg_review_score"].median()

fig_sellers.add_hline(y=median_review, line_dash="dot", line_color="gray", opacity=0.5)
fig_sellers.add_vline(x=median_orders, line_dash="dot", line_color="gray", opacity=0.5)

fig_sellers.update_layout(
    xaxis_title="Cantidad de pedidos",
    yaxis_title="Review score promedio",
    height=550
)

st.plotly_chart(fig_sellers, use_container_width=True)

st.caption(
    f"Se excluyen {sellers_sin_reviews} sellers sin reviews. Las líneas punteadas marcan "
    "la mediana de cada eje. Los percentiles de volumen y calidad (volume_percentile, "
    "quality_percentile) están disponibles en la vista para análisis más detallado, "
    "pero se optó por mostrar las métricas crudas para mayor claridad interpretativa."
)