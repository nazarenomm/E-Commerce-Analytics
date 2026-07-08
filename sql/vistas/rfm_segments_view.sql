CREATE VIEW rfm_segments AS
WITH customer_orders AS (
  SELECT
    c.customer_unique_id,
    o.order_id,
    o.purchase_timestamp,
    p.value AS payment_value
  FROM orders o
  JOIN customers c USING (customer_id)
  JOIN order_payments p USING (order_id)
  WHERE o.status NOT IN ('canceled', 'unavailable')
),
rfm_raw AS (
  SELECT
    customer_unique_id,
    EXTRACT(DAY FROM AGE(
      (SELECT MAX(purchase_timestamp) FROM customer_orders),
      MAX(purchase_timestamp)
    )) AS recency_days,
    COUNT(DISTINCT order_id) AS frequency,
    SUM(payment_value) AS monetary
  FROM customer_orders
  GROUP BY customer_unique_id
),
rfm_scored AS (
  SELECT
    customer_unique_id,
    recency_days,
    frequency,
    monetary,
    NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,
    NTILE(5) OVER (ORDER BY frequency ASC) AS f_score,
    NTILE(5) OVER (ORDER BY monetary ASC) AS m_score
  FROM rfm_raw
)
SELECT
  customer_unique_id,
  recency_days,
  frequency,
  monetary,
  r_score,
  f_score,
  m_score,
  (r_score + f_score + m_score) AS rfm_total,
  CASE
    WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'champions'
    WHEN r_score >= 3 AND f_score >= 3 THEN 'loyal'
    WHEN r_score >= 4 AND f_score <= 2 THEN 'promising'
    WHEN r_score <= 2 AND f_score >= 3 THEN 'at_risk'
    ELSE 'others'
  END AS segment
FROM rfm_scored;