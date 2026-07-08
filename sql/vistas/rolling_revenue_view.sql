CREATE VIEW rolling_revenue_30d AS
WITH daily AS (
  SELECT
    DATE(purchase_timestamp) AS day,
    SUM(value)               AS revenue
  FROM orders o
  JOIN order_payments p USING (order_id)
  GROUP BY 1
),
rolling AS (
  SELECT
    day,
    revenue,
    SUM(revenue) OVER (
      ORDER BY day
      ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) AS revenue_30d
  FROM daily
),
with_prev AS (
  SELECT
    day,
    revenue,
    revenue_30d,
    LAG(revenue_30d, 30) OVER (ORDER BY day) AS revenue_30d_prev
  FROM rolling
)
SELECT
  day,
  revenue,
  revenue_30d,
  revenue_30d_prev,
  ROUND(
    (revenue_30d - revenue_30d_prev) * 100.0 / NULLIF(revenue_30d_prev, 0),
    2
  ) AS pct_change
FROM with_prev
ORDER BY day;