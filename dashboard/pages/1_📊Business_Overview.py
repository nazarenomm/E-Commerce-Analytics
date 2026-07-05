import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.api import fetch_view
import plotly.express as px
import json
from urllib.request import urlopen

# REVENUE — ROLLING 30 DAYS
st.subheader("📈 Revenue — Rolling 30 días")

show_pct_change = st.checkbox("Mostrar % variación vs. período anterior", value=False)

df = fetch_view("rolling_revenue_30d")
df["day"] = pd.to_datetime(df["day"])

fig = make_subplots(specs=[[{"secondary_y": True}]])

fig.add_trace(
    go.Scatter(
        x=df["day"], y=df["revenue_30d"],
        mode="lines", name="Revenue (30d rolling)",
        line=dict(width=2, color="#1f77b4")
    ),
    secondary_y=False
)

if show_pct_change:
    fig.add_trace(
        go.Scatter(
            x=df["day"], y=df["pct_change"],
            mode="lines", name="% variación",
            line=dict(width=1.5, color="#d62728", dash="dot")
        ),
        secondary_y=True
    )
    fig.update_yaxes(range=[-100, 200], secondary_y=True)

fig.update_layout(hovermode="x unified")
fig.update_xaxes(title_text="Fecha")
fig.update_yaxes(title_text="Revenue acumulado 30d (R$)", secondary_y=False)
fig.update_yaxes(title_text="% variación", secondary_y=True)

st.plotly_chart(fig, use_container_width=True)

# DISTRIBUTION OF ORDERS BY STATUS
st.subheader("📦 Distribución de pedidos por status")

df_status = fetch_view("order_status_distribution")

exclude_delivered = st.checkbox("Excluir 'delivered' (ver solo estados minoritarios)", value=False)

df_display = df_status[df_status["status"] != "delivered"] if exclude_delivered else df_status.copy()
df_display = df_display.sort_values("order_count", ascending=True).copy()
df_display["pct_dynamic"] = round(df_display["order_count"] / df_display["order_count"].sum() * 100, 2)

fig_status = go.Figure(go.Bar(
    x=df_display["order_count"],
    y=df_display["status"],
    orientation="h",
    text=df_display["pct_dynamic"].astype(str) + "%",
    textposition="outside",
    marker_color="#1f77b4"
))

fig_status.update_layout(
    xaxis_title="Cantidad de pedidos",
    yaxis_title="",
    margin=dict(l=100)
)

st.plotly_chart(fig_status, use_container_width=True)

st.caption(
    "Los porcentajes se recalculan sobre el subconjunto visible según el filtro aplicado. "
    "Los análisis de revenue por categoría y por estado excluyen los pedidos 'canceled' y 'unavailable' para reflejar solo ventas efectivas."
)

# TOP 15 CATEGORIES BY REVENUE
st.subheader("🏷️ Top 15 categorías por revenue")

df_category = fetch_view("revenue_by_category")
df_category = df_category.sort_values("total_revenue", ascending=True)

fig_category = go.Figure(go.Bar(
    x=df_category["total_revenue"],
    y=df_category["category"],
    orientation="h",
    text=df_category["total_revenue"].apply(lambda x: f"R$ {x:,.0f}"),
    textposition="outside",
    marker_color="#2ca02c"
))

fig_category.update_layout(
    xaxis_title="Revenue total (R$)",
    yaxis_title="",
    margin=dict(l=200),  # nombres de categoría pueden ser largos
    height=500
)

st.plotly_chart(fig_category, use_container_width=True)

st.caption(
    "Excluye pedidos 'canceled' y 'unavailable'. Revenue calculado sobre el precio de los items, no sobre el total pagado (que puede incluir flete y variar por forma de pago)."
)

with st.expander("Ver tabla detallada (incluye precio promedio por item)"):
    df_table = df_category.sort_values("total_revenue", ascending=False).reset_index(drop=True)
    st.dataframe(
        df_table.rename(columns={
            "category": "Categoría",
            "order_count": "Cantidad de pedidos",
            "total_revenue": "Revenue total (R$)",
            "avg_item_price": "Precio promedio item (R$)"
        }),
        use_container_width=True,
        hide_index=True
    )

# REVENUE BY STATE
st.subheader("🗺️ Revenue por estado")

@st.cache_data(ttl=86400)
def load_brazil_geojson():
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    with urlopen(url) as response:
        return json.load(response)

brazil_geojson = load_brazil_geojson()

df_state = fetch_view("revenue_by_state")

metric_option = st.radio(
    "Métrica:",
    options=["Revenue total", "Valor de orden promedio"],
    horizontal=True
)
metric_col = "total_revenue" if metric_option == "Revenue total" else "avg_order_value"

fig_map = px.choropleth(
    df_state,
    geojson=brazil_geojson,
    locations="uf",
    featureidkey="properties.sigla",
    color=metric_col,
    color_continuous_scale="Blues",
    scope="south america",
    labels={metric_col: metric_option}
)
fig_map.update_geos(fitbounds="locations", visible=False)
fig_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

st.plotly_chart(fig_map, use_container_width=True)

st.caption(
    "No se utiliza la tabla de geolocalización de Olist: el estado (UF) proviene directamente de customers.customer_state, suficiente para un análisis a nivel estadual."
)