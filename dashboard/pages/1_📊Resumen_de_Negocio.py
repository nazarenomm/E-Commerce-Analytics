import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.api import fetch_view
import plotly.express as px
import json
from urllib.request import urlopen

#%% REVENUE — ROLLING 30 DAYS
st.subheader("📈 Rolling Revenue 30 días")

df = fetch_view("rolling_revenue_30d")
df["day"] = pd.to_datetime(df["day"])

min_date = df["day"].min().date()
max_date = df["day"].max().date()
default_start = pd.Timestamp("2017-09-01").date()

date_range = st.slider(
    "Rango de fechas",
    min_value=min_date,
    max_value=max_date,
    value=(default_start, max_date),
    format="YYYY-MM-DD"
)

show_pct_change = st.checkbox("Mostrar % variación vs. período anterior", value=False)

df_filtered = df[
    (df["day"].dt.date >= date_range[0]) &
    (df["day"].dt.date <= date_range[1])
]

fig = make_subplots(specs=[[{"secondary_y": True}]])

fig.add_trace(
    go.Scatter(
        x=df_filtered["day"], y=df_filtered["revenue_30d"],
        mode="lines", name="Revenue (30d rolling)",
        line=dict(width=2, color="#1f77b4")
    ),
    secondary_y=False
)

if show_pct_change:
    fig.add_trace(
        go.Scatter(
            x=df_filtered["day"], y=df_filtered["pct_change"],
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

st.info(
    "💡 **Insight**: Se observa un patrón cíclico de picos y correcciones cada 3-4 meses "
    "(Dic 2017, May 2018, Ago 2018), con caídas de 30-40% inmediatamente después de cada pico. "
    "El pico de diciembre coincide con la temporada de fin de año, pero los picos de mayo y "
    "agosto no tienen una causa estacional obvia, podrían estar asociados a campañas "
    "promocionales puntuales más que a estacionalidad del negocio."
)
#%% Revenue mensual — Comparación 2017 vs 2018
st.subheader("📊 Revenue mensual — Comparación 2017 vs 2018")

df_monthly = df.copy()
df_monthly["year"] = df_monthly["day"].dt.year
df_monthly["month_num"] = df_monthly["day"].dt.month

df_monthly_agg = df_monthly.groupby(["year", "month_num"], as_index=False)["revenue"].sum()

df_2017 = df_monthly_agg[df_monthly_agg["year"] == 2017].sort_values("month_num")
df_2018 = df_monthly_agg[df_monthly_agg["year"] == 2018].sort_values("month_num")

month_names = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

fig_yoy = go.Figure()

fig_yoy.add_trace(go.Bar(
    x=[month_names[m - 1] for m in df_2018["month_num"]],
    y=df_2018["revenue"],
    name="2018",
    marker_color="#1f77b4"
))

fig_yoy.add_trace(go.Scatter(
    x=[month_names[m - 1] for m in df_2017["month_num"]],
    y=df_2017["revenue"],
    name="2017",
    mode="lines+markers",
    line=dict(width=2.5, color="#d62728")
))

fig_yoy.update_layout(
    xaxis_title="Mes",
    yaxis_title="Revenue (R$)",
    xaxis=dict(categoryorder="array", categoryarray=month_names),
    hovermode="x unified",
    height=450,
    legend_title="Año"
)

st.plotly_chart(fig_yoy, use_container_width=True)

#%% DISTRIBUTION OF ORDERS BY STATUS
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
    "Los análisis de revenue por categoría y por estado excluyen los pedidos 'canceled' y 'unavailable' para reflejar solo ventas efectivas."
)

#%% TOP 15 CATEGORIES BY REVENUE
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

#%% REVENUE BY STATE
st.subheader("🗺️ Revenue por estado")

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


brazil_geojson = load_brazil_geojson()
uf_to_name = build_uf_name_map(brazil_geojson)

df_state = fetch_view("revenue_by_state")
df_state["state_name"] = df_state["uf"].map(uf_to_name)

metric_option = st.radio(
    "Métrica:",
    options=["Revenue total", "Valor de orden promedio"],
    horizontal=True
)
metric_col = "total_revenue" if metric_option == "Revenue total" else "avg_order_value"

col_map, col_bar = st.columns([3, 2])

with col_map:
    fig_map = px.choropleth(
        df_state,
        geojson=brazil_geojson,
        locations="uf",
        featureidkey="properties.sigla",
        color=metric_col,
        color_continuous_scale="thermal",
        scope="south america",
        hover_name="state_name",
        hover_data={"uf": False, metric_col: ":,.0f"},
        labels={metric_col: metric_option}
    )
    fig_map.update_geos(fitbounds="locations", visible=False)
    fig_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=450)
    st.plotly_chart(fig_map, use_container_width=True)

with col_bar:
    df_state_sorted = df_state.sort_values(metric_col, ascending=True)

    fig_bar = go.Figure(go.Bar(
        x=df_state_sorted[metric_col],
        y=df_state_sorted["state_name"],
        orientation="h",
        marker=dict(
            color=df_state_sorted[metric_col],
            colorscale="thermal",
            showscale=False
        ),
        text=df_state_sorted[metric_col].apply(lambda x: f"R$ {x:,.0f}"),
        textposition="outside"
    ))
    fig_bar.update_layout(
        xaxis_title=metric_option,
        yaxis_title="",
        height=550,
        margin=dict(t=40, l=100)
    )
    st.plotly_chart(fig_bar, use_container_width=True)