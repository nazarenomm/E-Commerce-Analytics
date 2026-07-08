CREATE VIEW revenue_by_state AS
SELECT
  c.state AS uf,
  COUNT(DISTINCT o.order_id) AS order_count,
  SUM(p.value)                AS total_revenue,
  ROUND(SUM(p.value) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value
FROM orders o
JOIN customers c USING (customer_id)
JOIN order_payments p USING (order_id)
WHERE o.status NOT IN ('canceled', 'unavailable')
GROUP BY c.state
ORDER BY total_revenue DESC;