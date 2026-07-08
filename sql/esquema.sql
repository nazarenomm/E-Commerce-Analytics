-- ============================================================
-- EXTENSIONES
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- 1. CUSTOMERS
-- Datos reales del CSV + columnas Faker marcadas con sufijo _fake
-- ============================================================
CREATE TABLE customers (
    customer_id          TEXT PRIMARY KEY, -- id de la 
    customer_unique_id   TEXT NOT NULL,
    zip_code_prefix      TEXT NOT NULL,
    city                 TEXT NOT NULL,
    state                CHAR(2) NOT NULL
);

CREATE INDEX idx_customers_unique   ON customers(customer_unique_id);
CREATE INDEX idx_customers_state    ON customers(state);

-- ============================================================
-- 2. SELLERS
-- ============================================================
CREATE TABLE sellers (
    seller_id          TEXT PRIMARY KEY,
    zip_code_prefix    TEXT NOT NULL,
    city               TEXT NOT NULL,
    state              CHAR(2) NOT NULL
    );

CREATE INDEX idx_sellers_state ON sellers(state);

-- ============================================================
-- 3. GEOLOCATION
-- Carga directa del CSV (puede tener duplicados por zip)
-- ============================================================
CREATE TABLE geolocation (
    id              BIGSERIAL PRIMARY KEY,
    zip_code_prefix TEXT NOT NULL,
    lat             NUMERIC(9,6) NOT NULL,
    lng             NUMERIC(9,6) NOT NULL,
    city            TEXT NOT NULL,
    state           CHAR(2) NOT NULL
);

CREATE INDEX idx_geo_zip ON geolocation(zip_code_prefix);

-- ============================================================
-- 4. PRODUCT CATEGORIES (traducción EN/PT)
-- ============================================================
CREATE TABLE product_categories (
    category_name_pt TEXT PRIMARY KEY,
    category_name_en TEXT NOT NULL
);

-- ============================================================
-- 5. PRODUCTS
-- ============================================================
CREATE TABLE products (
    product_id               TEXT PRIMARY KEY,
    category_name            TEXT REFERENCES product_categories(category_name_pt),
    name_length              INT,
    description_length       INT,
    photos_qty               INT,
    weight_g                 INT,
    length_cm                INT,
    height_cm                INT,
    width_cm                 INT
);

CREATE INDEX idx_products_category ON products(category_name);

-- ============================================================
-- 6. ORDERS
-- Tabla central del modelo estrella
-- ============================================================
CREATE TABLE orders (
    order_id                       TEXT PRIMARY KEY,
    customer_id                    TEXT NOT NULL REFERENCES customers(customer_id),
    status                         TEXT NOT NULL,
    purchase_timestamp             TIMESTAMPTZ NOT NULL,
    approved_at                    TIMESTAMPTZ,
    carrier_delivery_timestamp     TIMESTAMPTZ,  -- delivered_to_carrier
    customer_delivery_timestamp    TIMESTAMPTZ,  -- delivered_to_customer
    estimated_delivery_date        TIMESTAMPTZ
);

CREATE INDEX idx_orders_customer   ON orders(customer_id);
CREATE INDEX idx_orders_status     ON orders(status);
CREATE INDEX idx_orders_purchase   ON orders(purchase_timestamp);

-- ============================================================
-- 7. ORDER ITEMS
-- ============================================================
CREATE TABLE order_items (
    order_id              TEXT NOT NULL REFERENCES orders(order_id),
    order_item_id         INT  NOT NULL,   -- nro de item dentro del pedido
    product_id            TEXT NOT NULL REFERENCES products(product_id),
    seller_id             TEXT NOT NULL REFERENCES sellers(seller_id),
    shipping_limit_date   TIMESTAMPTZ,
    price                 NUMERIC(10,2) NOT NULL,
    freight_value         NUMERIC(10,2) NOT NULL,
    PRIMARY KEY (order_id, order_item_id)
);

CREATE INDEX idx_items_product ON order_items(product_id);
CREATE INDEX idx_items_seller  ON order_items(seller_id);

-- ============================================================
-- 8. ORDER PAYMENTS
-- Un pedido puede tener múltiples pagos (cuotas, métodos mixtos)
-- ============================================================
CREATE TABLE order_payments (
    order_id             TEXT NOT NULL REFERENCES orders(order_id),
    payment_sequential   INT  NOT NULL,
    payment_type         TEXT NOT NULL,   -- credit_card, boleto, voucher, debit_card
    installments         INT  NOT NULL DEFAULT 1,
    value                NUMERIC(10,2) NOT NULL,
    PRIMARY KEY (order_id, payment_sequential)
);

CREATE INDEX idx_payments_type ON order_payments(payment_type);

-- ============================================================
-- 9. ORDER REVIEWS
-- ============================================================
CREATE TABLE order_reviews (
    review_id               TEXT NOT NULL,
    order_id                TEXT NOT NULL REFERENCES orders(order_id),
    score                   SMALLINT NOT NULL CHECK (score BETWEEN 1 AND 5),
    comment_title           TEXT,
    comment_message         TEXT,
    creation_date           TIMESTAMPTZ,
    answer_timestamp        TIMESTAMPTZ,
    PRIMARY KEY (review_id, order_id)  -- hay duplicados de review_id en el CSV original
);

CREATE INDEX idx_reviews_order ON order_reviews(order_id);
CREATE INDEX idx_reviews_score ON order_reviews(score);