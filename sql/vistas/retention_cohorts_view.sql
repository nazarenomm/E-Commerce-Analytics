CREATE VIEW retention_cohorts AS
WITH cohorts AS (
  SELECT
    c.customer_unique_id,
    DATE_TRUNC('month', MIN(o.purchase_timestamp)) AS cohort_month
  FROM orders o
  JOIN customers c USING (customer_id)
  GROUP BY c.customer_unique_id
),
activity AS (
  SELECT
    c.customer_unique_id,
    co.cohort_month,
    DATE_TRUNC('month', o.purchase_timestamp) AS activity_month,
    EXTRACT(YEAR FROM AGE(
      DATE_TRUNC('month', o.purchase_timestamp),
      co.cohort_month
    )) * 12 +
    EXTRACT(MONTH FROM AGE(
      DATE_TRUNC('month', o.purchase_timestamp),
      co.cohort_month
    )) AS period_number
  FROM orders o
  JOIN customers c USING (customer_id)
  JOIN cohorts co USING (customer_unique_id)
)
SELECT
  cohort_month,
  period_number,
  COUNT(DISTINCT customer_unique_id) AS users,
  ROUND(COUNT(DISTINCT customer_unique_id) * 100.0 /
    FIRST_VALUE(COUNT(DISTINCT customer_unique_id)) OVER (
      PARTITION BY cohort_month ORDER BY period_number
    ), 2) AS retention_pct
FROM activity
GROUP BY cohort_month, period_number
ORDER BY cohort_month, period_number;