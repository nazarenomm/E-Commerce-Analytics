"""
Carga el dataset de Olist a Supabase.
"""

import os
import math
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

DATA_DIR = "data/proc"
CHUNK_SIZE = 500  # registros por batch

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ─────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────

def clean(df: pd.DataFrame) -> list[dict]:
    """Convierte NaN a None para que Supabase los inserte como NULL."""
    return [
        {k: (None if (isinstance(v, float) and math.isnan(v)) else v)
         for k, v in row.items()}
        for row in df.to_dict(orient="records")
    ]


def upsert_chunks(table: str, records: list[dict], on_conflict: str) -> None:
    total = len(records)
    for i in range(0, total, CHUNK_SIZE):
        chunk = records[i: i + CHUNK_SIZE]
        supabase.table(table).upsert(chunk, on_conflict=on_conflict).execute()
        pct = min(i + CHUNK_SIZE, total)
        print(f"  [{table}] {pct}/{total}")
    print(f"  [{table}] ✓ {total} registros cargados")


# ─────────────────────────────────────────────
# 1. product_categories
# ─────────────────────────────────────────────

def load_product_categories():
    print("\n→ product_categories")
    df = pd.read_csv(f"{DATA_DIR}/product_category_name_translation.csv")
    df = df.rename(columns={
        "product_category_name":            "category_name_pt",
        "product_category_name_english":    "category_name_en",
    })
    upsert_chunks("product_categories", clean(df), "category_name_pt")


# ─────────────────────────────────────────────
# 2. customers
# ─────────────────────────────────────────────

def load_customers():
    print("\n→ customers")
    df = pd.read_csv(f"{DATA_DIR}/olist_customers_dataset.csv")
    df = df.rename(columns={
        "customer_zip_code_prefix": "zip_code_prefix",
        "customer_city":            "city",
        "customer_state":           "state",
    })
    df = df[["customer_id", "customer_unique_id", "zip_code_prefix", "city", "state"]]
    upsert_chunks("customers", clean(df), "customer_id")


# ─────────────────────────────────────────────
# 3. sellers
# ─────────────────────────────────────────────

def load_sellers():
    print("\n→ sellers")
    df = pd.read_csv(f"{DATA_DIR}/olist_sellers_dataset.csv")
    df = df.rename(columns={
        "seller_zip_code_prefix": "zip_code_prefix",
        "seller_city":            "city",
        "seller_state":           "state",
    })
    df = df[["seller_id", "zip_code_prefix", "city", "state"]]
    upsert_chunks("sellers", clean(df), "seller_id")


# ─────────────────────────────────────────────
# 4. geolocation
# ─────────────────────────────────────────────

def load_geolocation():
    print("\n→ geolocation")
    df = pd.read_csv(f"{DATA_DIR}/olist_geolocation_dataset.csv")
    df = df.rename(columns={
        "geolocation_zip_code_prefix": "zip_code_prefix",
        "geolocation_lat":             "lat",
        "geolocation_lng":             "lng",
        "geolocation_city":            "city",
        "geolocation_state":           "state",
    })
    # esta tabla no tiene PK única (duplicados intencionales), usamos insert normal
    total = len(df)
    for i in range(0, total, CHUNK_SIZE):
        chunk = clean(df.iloc[i: i + CHUNK_SIZE])
        supabase.table("geolocation").insert(chunk).execute()
        pct = min(i + CHUNK_SIZE, total)
        print(f"  [geolocation] {pct}/{total}")
    print(f"  [geolocation] ✓ {total} registros cargados")


# ─────────────────────────────────────────────
# 5. products
# ─────────────────────────────────────────────

def load_products():
    print("\n→ products")
    df = pd.read_csv(f"{DATA_DIR}/olist_products_dataset.csv")
    df = df.rename(columns={
        "product_category_name":        "category_name",
        "product_name_lenght":          "name_length",
        "product_description_lenght":   "description_length",
        "product_photos_qty":           "photos_qty",
        "product_weight_g":             "weight_g",
        "product_length_cm":            "length_cm",
        "product_height_cm":            "height_cm",
        "product_width_cm":             "width_cm",
    })
    df = df[[
        "product_id", "category_name", "name_length", "description_length",
        "photos_qty", "weight_g", "length_cm", "height_cm", "width_cm",
    ]]

     # insertar categorías faltantes antes de los productos
    cats_in_products = df["category_name"].dropna().unique()
    cats_existing = pd.read_csv(f"{DATA_DIR}/product_category_name_translation.csv")
    cats_existing = cats_existing["product_category_name"].values
    
    missing = [c for c in cats_in_products if c not in cats_existing]
    if missing:
        print(f"  Categorías sin traducción: {missing}")
        missing_records = [{"category_name_pt": c, "category_name_en": None} for c in missing]
        supabase.table("product_categories").upsert(
            missing_records, on_conflict="category_name_pt"
        ).execute()

    # columnas INT que pandas lee como float por tener NaN
    int_cols = ["name_length", "description_length", "photos_qty",
                "weight_g", "length_cm", "height_cm", "width_cm"]
    for col in int_cols:
        df[col] = pd.array(df[col], dtype=pd.Int64Dtype())  # Int64 nullable soporta NaN

    upsert_chunks("products", clean(df), "product_id")


# ─────────────────────────────────────────────
# 6. orders
# ─────────────────────────────────────────────

def load_orders():
    print("\n→ orders")
    df = pd.read_csv(f"{DATA_DIR}/olist_orders_dataset.csv", parse_dates=[
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ])
    df = df.rename(columns={
        "order_status":                     "status",
        "order_purchase_timestamp":         "purchase_timestamp",
        "order_approved_at":                "approved_at",
        "order_delivered_carrier_date":     "carrier_delivery_timestamp",
        "order_delivered_customer_date":    "customer_delivery_timestamp",
        "order_estimated_delivery_date":    "estimated_delivery_date",
    })
    # convertir timestamps a string ISO para JSON serialization
    for col in ["purchase_timestamp", "approved_at", "carrier_delivery_timestamp",
                "customer_delivery_timestamp", "estimated_delivery_date"]:
        df[col] = df[col].astype(str).replace("NaT", None)

    df = df[[
        "order_id", "customer_id", "status", "purchase_timestamp",
        "approved_at", "carrier_delivery_timestamp",
        "customer_delivery_timestamp", "estimated_delivery_date",
    ]]
    upsert_chunks("orders", clean(df), "order_id")


# ─────────────────────────────────────────────
# 7. order_items
# ─────────────────────────────────────────────

def load_order_items():
    print("\n→ order_items")
    df = pd.read_csv(f"{DATA_DIR}/olist_order_items_dataset.csv",
                     parse_dates=["shipping_limit_date"])
    df = df.rename(columns={"order_item_id": "order_item_id"})
    df["shipping_limit_date"] = df["shipping_limit_date"].astype(str).replace("NaT", None)
    df = df[[
        "order_id", "order_item_id", "product_id", "seller_id",
        "shipping_limit_date", "price", "freight_value",
    ]]
    upsert_chunks("order_items", clean(df), "order_id,order_item_id")


# ─────────────────────────────────────────────
# 8. order_payments
# ─────────────────────────────────────────────

def load_order_payments():
    print("\n→ order_payments")
    df = pd.read_csv(f"{DATA_DIR}/olist_order_payments_dataset.csv")
    df = df.rename(columns={
        "payment_sequential":   "payment_sequential",
        "payment_type":         "payment_type",
        "payment_installments": "installments",
        "payment_value":        "value",
    })
    df = df[["order_id", "payment_sequential", "payment_type", "installments", "value"]]
    upsert_chunks("order_payments", clean(df), "order_id,payment_sequential")


# ─────────────────────────────────────────────
# 9. order_reviews
# ─────────────────────────────────────────────

def load_order_reviews():
    print("\n→ order_reviews")
    df = pd.read_csv(f"{DATA_DIR}/olist_order_reviews_dataset.csv",
                     parse_dates=["review_creation_date", "review_answer_timestamp"])
    df = df.rename(columns={
        "review_score":             "score",
        "review_comment_title":     "comment_title",
        "review_comment_message":   "comment_message",
        "review_creation_date":     "creation_date",
        "review_answer_timestamp":  "answer_timestamp",
    })
    for col in ["creation_date", "answer_timestamp"]:
        df[col] = df[col].astype(str).replace("NaT", None)

    df = df[[
        "review_id", "order_id", "score", "comment_title",
        "comment_message", "creation_date", "answer_timestamp",
    ]]
    # PK compuesta (review_id, order_id) por duplicados en el CSV
    upsert_chunks("order_reviews", clean(df), "review_id,order_id")


# ─────────────────────────────────────────────
# main
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Carga Olist → Supabase ===")
    load_product_categories()
    load_customers()
    load_sellers()
    # load_geolocation()   # la cargamos despues en caso de ser necesaria porque tiene muchos registros
    load_products()
    load_orders()
    load_order_items()
    load_order_payments()
    load_order_reviews()
    print("\n✓ Carga completa")
