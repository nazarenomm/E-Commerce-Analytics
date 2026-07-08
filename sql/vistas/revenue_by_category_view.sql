CREATE VIEW revenue_by_category AS
SELECT
  COALESCE(p.category_name, 'unknown') AS category,
  COUNT(DISTINCT oi.order_id)          AS order_count,
  SUM(oi.price)                        AS total_revenue,
  ROUND(AVG(oi.price), 2)              AS avg_item_price,
  ROUND(AVG(r.score), 2)        AS avg_review_score
FROM order_items oi
JOIN products p USING (product_id)
JOIN orders o USING (order_id)
LEFT JOIN order_reviews r USING (order_id)
WHERE o.status NOT IN ('canceled', 'unavailable')
GROUP BY category
ORDER BY total_revenue DESC;