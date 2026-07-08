import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.api import fetch_views, load_brazil_geojson, build_uf_name_map
import plotly.express as px

st.header("📊 Resumen de negocio")
#%% Load data
data = fetch_views(["rolling_revenue_30d", "order_status_distribution", "revenue_by_category", "revenue_by_state"])

df = data["rolling_revenue_30d"]
df_status = data["order_status_distribution"]
df_category = data["revenue_by_category"]
df_state = data["revenue_by_state"]

brazil_geojson = load_brazil_geojson()

#%% KPI CARDS
st.subheader("📌 Resumen general")

total_revenue = df["revenue"].sum()
total_orders = df_status["order_count"].sum()
avg_ticket = total_revenue / total_orders if total_orders else 0
delivered_pct = df_status.loc[df_status["status"] == "delivered", "order_count"].sum() / total_orders * 100

col1, col2, col3, col4 = st.columns(4)
with col1.container(border=True):
    st.metric("Revenue total", f"R$ {total_revenue:,.0f}")

with col2.container(border=True):
    st.metric("Pedidos totales", f"{total_orders:,.0f}")

with col3.container(border=True):
    st.metric("Ticket promedio", f"R$ {avg_ticket:,.2f}")

with col4.container(border=True):
    st.metric("Tasa de entrega", f"{delivered_pct:.1f}%")

#%% REVENUE — ROLLING 30 DAYS
st.subheader("📈 Rolling Revenue 30 días")
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
    "💡Se observa un patrón cíclico de picos y correcciones cada 3-4 meses "
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

df_category = df_category.sort_values("total_revenue", ascending=True)
df_category_top = df_category.sort_values("total_revenue", ascending=False).head(15)
df_category_top = df_category_top.sort_values("total_revenue", ascending=True)

fig_category = go.Figure(go.Bar(
    x=df_category_top["total_revenue"],
    y=df_category_top["category"],
    orientation="h",
    text=df_category_top["total_revenue"].apply(lambda x: f"R$ {x:,.0f}"),
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
#%% BOTTOM 15 CATEGORIES BY REVENUE
st.subheader("🔻 Bottom 15 categorías por revenue")

df_bottom = df_category.sort_values("total_revenue", ascending=False).tail(15)
df_bottom = df_bottom.sort_values("total_revenue", ascending=True)

fig_bottom = go.Figure(go.Bar(
    x=df_bottom["total_revenue"],
    y=df_bottom["category"],
    orientation="h",
    text=df_bottom["total_revenue"].apply(lambda x: f"R$ {x:,.0f}"),
    textposition="outside",
    marker_color="#d62728"
))

fig_bottom.update_layout(
    xaxis_title="Revenue total (R$)",
    yaxis_title="",
    margin=dict(l=200),
    height=500
)

st.plotly_chart(fig_bottom, use_container_width=True)

#%% PRECIO PROMEDIO VS REVIEW SCORE POR CATEGORÍA
st.subheader("⭐ Precio promedio vs. calificación por categoría")

df_scatter = df_category.dropna(subset=["avg_review_score"])

fig_price_review = px.scatter(
    df_scatter,
    x="avg_item_price",
    y="avg_review_score",
    color="total_revenue",
    color_continuous_scale="thermal",
    opacity=0.7,
    hover_name="category",
    labels={
        "avg_item_price": "Precio promedio (R$)",
        "avg_review_score": "Review promedio (⭐)",
        "order_count": "Cantidad de pedidos",
        "total_revenue": "Revenue total (R$)"
    },
    size_max=40
)

fig_price_review.update_traces(
    marker=dict(
        size=10,
        line=dict(width=1, color="DarkSlateGrey")
    )
)

fig_price_review.update_layout(
    yaxis=dict(range=[1, 5]),
    height=550
)

st.plotly_chart(fig_price_review, use_container_width=True)

st.caption(
    "El review_score es a nivel de pedido, no de item: pedidos con múltiples categorías "
    "distribuyen su calificación entre todas ellas. Interpretar como aproximación, no como "
    "medición exacta de satisfacción por categoría."
)
#%% TABLA DE CATEGORÍAS
with st.expander("Ver tabla detallada"):
    df_table = df_category.sort_values("total_revenue", ascending=False).reset_index(drop=True)
    st.dataframe(
        df_table.rename(columns={
            "category": "Categoría",
            "order_count": "Cantidad de pedidos",
            "total_revenue": "Revenue total (R$)",
            "avg_item_price": "Precio promedio item (R$)",
            "avg_review_score": "Review promedio (⭐)"
        }),
        use_container_width=True,
        hide_index=True
    )

#%% REVENUE BY STATE
st.subheader("🗺️ Revenue por estado")

uf_to_name = build_uf_name_map(brazil_geojson)

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