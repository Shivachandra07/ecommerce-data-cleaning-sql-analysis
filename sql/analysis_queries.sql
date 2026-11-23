-- Business analysis queries: joins, CTEs and window functions.
-- Dates are stored as ISO text (YYYY-MM-DD), so substr(order_date, 1, 7) gives
-- the month in both PostgreSQL and SQLite.

-- 1. Monthly revenue trend
SELECT substr(o.order_date, 1, 7)        AS month,
       COUNT(DISTINCT o.order_id)        AS orders,
       ROUND(SUM(o.total_amount), 2)     AS revenue
FROM orders o
WHERE o.status = 'completed'
GROUP BY substr(o.order_date, 1, 7)
ORDER BY month;

-- 2. Top 10 products by revenue
SELECT o.product_name,
       o.category,
       SUM(o.quantity)                AS units_sold,
       ROUND(SUM(o.total_amount), 2)  AS revenue
FROM orders o
WHERE o.status = 'completed'
GROUP BY o.product_name, o.category
ORDER BY revenue DESC
LIMIT 10;

-- 3. Repeat vs one-time customers (CTE)
WITH per_customer AS (
    SELECT customer_id,
           COUNT(*)                     AS order_count,
           ROUND(SUM(total_amount), 2)  AS lifetime_value
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
)
SELECT CASE WHEN order_count > 1 THEN 'repeat customer' ELSE 'one-time customer' END AS segment,
       COUNT(*)                AS customers,
       ROUND(SUM(lifetime_value), 2) AS total_revenue,
       ROUND(AVG(lifetime_value), 2) AS avg_lifetime_value
FROM per_customer
GROUP BY segment
ORDER BY total_revenue DESC;

-- 4. Repeat customer retention rate
WITH per_customer AS (
    SELECT customer_id, COUNT(*) AS order_count
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
)
SELECT COUNT(*)                                                     AS purchasing_customers,
       SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END)             AS repeat_customers,
       ROUND(100.0 * SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS repeat_rate_pct
FROM per_customer;

-- 5. Top 10 customers by lifetime value (window function RANK)
WITH per_customer AS (
    SELECT o.customer_id,
           c.full_name,
           c.country,
           COUNT(*)                    AS orders,
           ROUND(SUM(o.total_amount), 2) AS lifetime_value
    FROM orders o
    JOIN customers c ON c.customer_id = o.customer_id
    WHERE o.status = 'completed'
    GROUP BY o.customer_id, c.full_name, c.country
)
SELECT RANK() OVER (ORDER BY lifetime_value DESC) AS rank,
       customer_id,
       full_name,
       country,
       orders,
       lifetime_value
FROM per_customer
ORDER BY lifetime_value DESC
LIMIT 10;

-- 6. Month-over-month revenue growth (window function LAG)
WITH monthly AS (
    SELECT substr(order_date, 1, 7) AS month,
           SUM(total_amount)        AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY substr(order_date, 1, 7)
)
SELECT month,
       ROUND(revenue, 2) AS revenue,
       ROUND(revenue - LAG(revenue) OVER (ORDER BY month), 2) AS change_vs_prev_month,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
             / NULLIF(LAG(revenue) OVER (ORDER BY month), 0), 1) AS growth_pct
FROM monthly
ORDER BY month;

-- 7. Revenue by country (join + aggregation)
SELECT c.country,
       COUNT(DISTINCT o.order_id)        AS orders,
       COUNT(DISTINCT o.customer_id)     AS customers,
       ROUND(SUM(o.total_amount), 2)     AS revenue
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
WHERE o.status = 'completed'
GROUP BY c.country
ORDER BY revenue DESC;

-- 8. Category mix as a share of revenue (CTE + window function)
WITH category_revenue AS (
    SELECT category, SUM(total_amount) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY category
)
SELECT category,
       ROUND(revenue, 2) AS revenue,
       ROUND(100.0 * revenue / SUM(revenue) OVER (), 2) AS pct_of_total
FROM category_revenue
ORDER BY revenue DESC;

-- 9. Average order value by month
SELECT substr(order_date, 1, 7)                     AS month,
       ROUND(AVG(total_amount), 2)                  AS avg_order_value,
       ROUND(SUM(total_amount) / COUNT(*), 2)       AS revenue_per_order
FROM orders
WHERE status = 'completed'
GROUP BY substr(order_date, 1, 7)
ORDER BY month;
