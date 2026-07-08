import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.api import fetch_views

st.header("👥 Clientes")

#%% LOAD DATA
data = fetch_views(["retention_cohorts", "rfm_segments", "seller_rankings"])

df_cohort = data["retention_cohorts"]
df_rfm = data["rfm_segments"]
df_sellers = data["seller_rankings"]

#%% RETENTION COHORTS
st.subheader("📊 Retención por cohorte")

df_cohort["cohort_month"] = pd.to_datetime(df_cohort["cohort_month"]).dt.strftime("%Y-%m")

max_period = st.slider(
    "Meses a mostrar",
    min_value=3,
    max_value=int(df_cohort["period_number"].max()),
    value=12
)

# Excluimos period_number=0: siempre es 100% y no aporta información
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
    "**Cómo leer este gráfico:** cada fila es una cohorte de clientes que hizo su "
    "primera compra ese mes. Cada columna (Mes 1, Mes 2...) indica cuántos meses "
    "pasaron desde esa primera compra. El color muestra qué porcentaje de la cohorte "
    "original volvió a comprar en ese mes. Por ejemplo, la fila '2017-03' en la "
    "columna 'Mes 2' responde: *de los clientes que compraron por primera vez en "
    "marzo 2017, ¿qué % volvió a comprar en mayo 2017?*. "
    "Las celdas en blanco son combinaciones sin datos: el período aún no ocurrió dentro "
    "de la ventana del dataset, o nadie de esa cohorte volvió a comprar ese mes."
)

st.info(
    "💡 La retención de clientes es muy baja, lo que sugiere que el negocio depende fuertemente de adquisición de clientes nuevos más que de recompra."
    "Esta es un área de mejora clave para el crecimiento sostenible del negocio."
)

#%% RFM
st.subheader("🎯 Segmentación RFM")

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

#%% RFM 2
st.subheader("🔍 Detalle de clientes por segmento (RFM)")

segment_colors = {
    "champions": "#2ca02c",
    "loyal": "#1f77b4",
    "promising": "#ff7f0e",
    "at_risk": "#d62728",
    "others": "#7f7f7f"
}

selected_segments = st.multiselect(
    "Segmentos a visualizar",
    options=list(segment_colors.keys()),
    default=["at_risk", "loyal", "champions"],
)

df_selected = df_rfm[df_rfm["segment"].isin(selected_segments)]

fig_detail = go.Figure()

for segment in selected_segments:
    df_seg = df_selected[df_selected["segment"] == segment]
    if df_seg.empty:
        continue

    sizes = np.sqrt(df_seg["monetary"].clip(lower=0))
    sizes_scaled = 4 + (sizes - sizes.min()) / (sizes.max() - sizes.min() + 1e-9) * 20

    fig_detail.add_trace(go.Scatter(
        x=df_seg["recency_days"],
        y=df_seg["frequency"],
        mode="markers",
        name=segment,
        marker=dict(
            size=sizes_scaled,
            color=segment_colors[segment],
            opacity=0.35,
            line=dict(width=0)
        ),
        hovertemplate=(
            "Recency: %{x} días<br>"
            "Frequency: %{y} compras<br>"
            "Monetary: R$ %{marker.size:.0f}<br>"
            f"Segmento: {segment}<extra></extra>"
        )
    ))

fig_detail.update_layout(
    xaxis_title="Recency (días desde última compra)",
    yaxis_title="Frequency (cantidad de compras)",
    height=500,
    legend_title="Segmento"
)

st.plotly_chart(fig_detail, use_container_width=True)

st.caption(
    f"Mostrando {len(df_selected):,} clientes de los segmentos seleccionados. "
    "El tamaño de cada punto representa el monto gastado (Monetary)."
)
#%% SELLERS
st.header("🛍️ Vendedores")

st.subheader("📋 Top / Bottom vendedores")

df_sellers_table = df_sellers.dropna(subset=["avg_review_score"]).copy()
df_sellers_table["avg_revenue"] = df_sellers_table["total_revenue"] / df_sellers_table["total_orders"]

with st.expander("🔍 Filtros"):
    col_f1, col_f2 = st.columns(2)

    with col_f1:
        min_orders, max_orders = int(df_sellers_table["total_orders"].min()), int(df_sellers_table["total_orders"].max())
        orders_range = st.slider(
            "Cantidad de pedidos",
            min_value=min_orders, max_value=max_orders,
            value=(min_orders, max_orders)
        )
        min_rev, max_rev = float(df_sellers_table["total_revenue"].min()), float(df_sellers_table["total_revenue"].max())
        revenue_range = st.slider(
            "Revenue total (R$)",
            min_value=min_rev, max_value=max_rev,
            value=(min_rev, max_rev)
        )

    with col_f2:
        review_range = st.slider(
            "Review promedio",
            min_value=1.0, max_value=5.0,
            value=(1.0, 5.0), step=0.1
        )

df_sellers_filtered = df_sellers_table[
    (df_sellers_table["total_orders"].between(*orders_range)) &
    (df_sellers_table["total_revenue"].between(*revenue_range)) &
    (df_sellers_table["avg_review_score"].between(*review_range))
]

col1, col2 = st.columns(2)
with col1:
    n_rows = st.selectbox("Cantidad a mostrar", options=[5, 10, 20, 50], index=1)
with col2:
    sort_metric = st.selectbox(
        "Ordenar por",
        options=["total_revenue", "total_orders", "avg_revenue", "avg_review_score"],
        format_func=lambda x: {
            "total_revenue": "Revenue total",
            "total_orders": "Cantidad de pedidos",
            "avg_revenue": "Revenue promedio",
            "avg_review_score": "Review promedio"
        }[x]
    )

view_mode = st.radio("Ver:", options=["Top", "Bottom"], horizontal=True)

ascending = (view_mode == "Bottom")
df_table = df_sellers_filtered.sort_values(sort_metric, ascending=ascending).head(n_rows)

st.caption(f"Mostrando {len(df_table)} de {len(df_sellers_filtered)} vendedores filtrados (total sin filtrar: {len(df_sellers_table)}).")

st.dataframe(
    df_table[["seller_id", "total_orders", "total_revenue", "avg_revenue", "avg_review_score"]].rename(columns={
        "seller_id": "Seller ID",
        "total_orders": "Pedidos",
        "total_revenue": "Revenue (R$)",
        "avg_revenue": "Revenue promedio (R$)",
        "avg_review_score": "Review promedio"
    }),
    use_container_width=True,
    hide_index=True,
    column_config={
        "Revenue (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
        "Revenue promedio (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
        "Review promedio": st.column_config.NumberColumn(format="%.2f ⭐")
    }
)

st.subheader("🏆 Ranking de vendedores")

df_sellers_clean = df_sellers.dropna(subset=["avg_review_score"])
sellers_sin_reviews = df_sellers["avg_review_score"].isna().sum()

fig_sellers = go.Figure(go.Scatter(
    x=df_sellers_clean["total_orders"],
    y=df_sellers_clean["avg_review_score"],
    mode="markers",
    marker=dict(
        size=8,
        color=df_sellers_clean["total_revenue"],
        colorscale="thermal",
        showscale=True,
        colorbar=dict(title="Revenue (R$)"),
        opacity=0.6,
        line=dict(width=0.5, color="white")
    ),
    hovertemplate=(
        "Pedidos: %{x}<br>"
        "Review promedio: %{y:.2f}<br>"
        "Revenue: R$ %{marker.color:,.0f}<extra></extra>"
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
