CREATE VIEW seller_rankings AS
WITH seller_stats AS (
  SELECT
    s.seller_id,
    COUNT(DISTINCT oi.order_id) AS total_orders,
    SUM(oi.price) AS total_revenue,
    ROUND(AVG(r.score), 2) AS avg_review_score
  FROM sellers s
  JOIN order_items oi USING (seller_id)
  JOIN orders o USING (order_id)
  LEFT JOIN order_reviews r USING (order_id)
  WHERE o.status NOT IN ('canceled', 'unavailable')
  GROUP BY s.seller_id
)
SELECT
  seller_id,
  total_orders,
  total_revenue,
  avg_review_score,
  ROUND(PERCENT_RANK() OVER (ORDER BY total_orders)::numeric, 4) AS volume_percentile,
  ROUND(PERCENT_RANK() OVER (ORDER BY avg_review_score)::numeric, 4) AS quality_percentile
FROM seller_stats
ORDER BY total_revenue DESC;