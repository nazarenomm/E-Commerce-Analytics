# 📊 E-Commerce Analytics — Olist Brazilian E-Commerce

Dashboard de analítica de negocio construido sobre el [Brazilian E-Commerce Public Dataset (Olist)](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), con foco en análisis de cohortes, segmentación de clientes (RFM), performance de vendedores y evolución de ingresos.

> ⚠️ **Nota**: el dashboard está deployado en Streamlit Community Cloud (tier gratuito). Si la base de datos estuvo inactiva, el primer request puede tardar ~30 segundos en "despertar". Si ves un error de conexión, esperá unos segundos y recargá / hacé click en "Wake up".

🔗 **Demo en vivo**: [[streamlit](https://e-commerce-analytics-olist.streamlit.app/)]

---

## 🧱 Stack

- **Datos**: Brazilian E-Commerce Public Dataset (Olist), vía Kaggle
- **Carga de datos**: Python + `supabase-py`
- **Base de datos**: Supabase (PostgreSQL)
- **API**: PostgREST (autogenerada por Supabase) sobre vistas SQL
- **Dashboard**: Streamlit + Plotly
- **Deployment**: Streamlit Community Cloud
- **Automatización**: GitHub Actions (keep-alive de la base de datos)

---

## 🎯 Objetivo del proyecto

Mostrar manejo end-to-end de un pipeline de datos: desde la carga y modelado en una base relacional, pasando por SQL analítico avanzado (window functions, vistas, RLS), hasta la exposición vía API y visualización interactiva.

---

## 🗂️ Estructura del proyecto

```
E-Commerce-Analytics/
├── data/                      # Dataset crudo y preprocesado
|   ├── proc/
|   └── raw/
├── scripts/                   # Scripts de carga y preprocesamiento (Python)
├── sql/                       # Definición de esquema, vistas y RLS
├── dashboard/
│   ├── E-Commerce_Analytics_Dashboard.py                 # Entry point de Streamlit
│   ├── pages/
│   │   ├── 1_📊_Business_Overview.py
│   │   └── 2_👥_Clientes_y_Vendedores.py
│   └── utils/
│       └── api.py             # Funciones de fetch a la API (PostgREST) con cache
├── .streamlit/
│   └── secrets.toml           # Credenciales (no versionado)
├── requirements.txt
└── README.md
```

---

## 🔄 Pipeline del proyecto

1. **Descarga del dataset** desde Kaggle (Brazilian E-Commerce Public Dataset by Olist).
2. **Preprocesamiento**: filtrado del rango temporal a enero 2017 – agosto 2018 (ver [Decisiones de diseño](#-decisiones-de-diseño)).
3. **Creación del proyecto en Supabase**.
4. **Definición del esquema**: script SQL para crear las tablas base, con ayuda de IA (Claude) para acelerar la escritura del DDL.
5. **Carga del esquema** en el SQL Editor de Supabase.
6. **Diseño del dashboard**: definición de las páginas y gráficos a incluir según las preguntas de negocio que se querían responder.
7. **Carga de datos**: script en Python (`supabase-py`) para poblar las tablas, con upsert idempotente y limpieza de datos.
8. **Creación de vistas SQL**: cohort retention, RFM scoring, revenue rolling, seller ranking (las más complejas con asistencia de Claude).
9. **Desarrollo del dashboard** en Streamlit (primera vez usando el framework, con asistencia de Claude como copiloto durante todo el proyecto).
10. **Deployment** en Streamlit Community Cloud.
11. **Automatización con GitHub Actions**: ping periódico a Supabase para evitar que la base de datos gratuita se pause por inactividad.

> 🤖 Este proyecto fue desarrollado usando Claude como asistente de código a lo largo varias de las etapas (definición de esquema , vistas complejas, y construcción del dashboard en Streamlit, framework que estaba usando por primera vez). Las decisiones de diseño, arquitectura y análisis fueron guiadas por mí; la IA se usó para acelerar la implementación.

---

## 📈 El dashboard

### Página 1 — Business Overview
- Ingresos con ventana móvil de 30 días, con variación porcentual opcional en eje secundario.
- Distribución de estados de las órdenes (con opción de excluir "delivered" para ver el detalle del resto).
- Top y Bottom 15 categorías por ingresos.
- Relación Precio vs Calidad por categoría.
- Mapa coroplético de Brasil por estado (ingreso total / ticket promedio).

### Página 2 — Clientes y Vendedores
- Heatmap de retención por cohortes.
- Segmentación RFM (bubble chart de centroides + distribución por segmento).
- Detalle de clientes por segmento RFM (scatter interactivo).
- Ranking de vendedores por volumen y calidad.

---

## 🧠 SQL analítico (el corazón del proyecto)

- **Cohort retention**: `DATE_TRUNC`, `FIRST_VALUE`, `AGE`.
- **RFM scoring**: `NTILE(5)` sobre recencia, frecuencia y monto → segmentos (champions, loyal, promising, at_risk, others).
- **Revenue rolling de 30 días**: `LAG` + `NULLIF` para el cálculo de variación porcentual.
- **Seller ranking**: `PERCENT_RANK` por volumen y calidad de servicio.

---

## 🌐 API pública

Las vistas están expuestas vía PostgREST, por ejemplo:

```
GET /rest/v1/rfm_segments
```

---

## 🛠️ Decisiones de diseño

- **Filtro temporal (enero 2017 – agosto 2018)**: se excluyen datos anteriores y posteriores a este rango ya que parecen discontinuos, probablemente a causa del método por el cual fueron obtenidos estos datos originalmente.
- **RLS vs. filtrado a nivel de aplicación**: se usa RLS a nivel de base de datos en vez de filtrado a nivel de aplicación (Streamlit/API layer), para garantizar que el control de acceso sea inviolable sin importar el cliente que consuma el endpoint público de PostgREST. Dado que el dataset es público y de solo lectura, la policy es simple: SELECT permitido para todos, sin condiciones (USING (true)).

---

## 🚀 Cómo correrlo localmente

```bash
# Clonar el repo
git clone <https://github.com/nazarenomm/E-Commerce-Analytics>
cd E-Commerce-Analytics

# Instalar dependencias
pip install -r requirements.txt

# Configurar credenciales
# Completar dashboard/.streamlit/secrets.toml con las credenciales de Supabase

# Correr el dashboard
streamlit run dashboard/app.py
```