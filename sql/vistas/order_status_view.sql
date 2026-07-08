CREATE VIEW order_status_distribution AS
SELECT
  status,
  COUNT(*) AS order_count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_of_total
FROM orders
GROUP BY status
ORDER BY order_count DESC;