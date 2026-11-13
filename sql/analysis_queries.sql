-- P17 — analysis queries: the whole report in SQL. Each query is run
-- against data/processed/traffic.db by src/checks.py and must agree
-- with the same numbers recomputed from the raw CSVs.
-- Run one query at a time (sqlite3 CLI: .read sql/analysis_queries.sql
-- only runs the first statement — use the Python sqlite3 module or
-- split on the "-- Q" markers).

-- Q1: sessions by channel, with share, conversion rate and revenue
SELECT
    channel,
    SUM(sessions) AS sessions,
    SUM(users) AS users,
    SUM(purchases) AS purchases,
    SUM(revenue_pkr) AS revenue_pkr,
    ROUND(100.0 * SUM(sessions)
        / (SELECT SUM(sessions) FROM fact_daily_traffic), 2) AS share_pct,
    ROUND(100.0 * SUM(purchases) / SUM(sessions), 2) AS conversion_rate_pct,
    ROUND(1.0 * SUM(revenue_pkr) / SUM(purchases), 0) AS avg_order_value_pkr
FROM fact_daily_traffic
GROUP BY channel
ORDER BY sessions DESC;

-- Q2: monthly trend (sessions, purchases, revenue, conversion rate)
SELECT
    month,
    SUM(sessions) AS sessions,
    SUM(users) AS users,
    SUM(purchases) AS purchases,
    SUM(revenue_pkr) AS revenue_pkr,
    ROUND(100.0 * SUM(purchases) / SUM(sessions), 2) AS conversion_rate_pct
FROM fact_daily_traffic
GROUP BY month
ORDER BY month;

-- Q3: the conversion funnel (whole period, all channels)
SELECT
    SUM(sessions) AS sessions,
    SUM(product_views) AS product_views,
    SUM(add_to_cart) AS add_to_cart,
    SUM(checkout_started) AS checkout_started,
    SUM(purchases) AS purchases,
    ROUND(100.0 * SUM(product_views) / SUM(sessions), 2) AS views_rate_pct,
    ROUND(100.0 * SUM(add_to_cart) / SUM(product_views), 2) AS cart_rate_pct,
    ROUND(100.0 * SUM(checkout_started) / SUM(add_to_cart), 2) AS checkout_rate_pct,
    ROUND(100.0 * SUM(purchases) / SUM(checkout_started), 2) AS purchase_rate_pct,
    ROUND(100.0 * SUM(purchases) / SUM(sessions), 2) AS overall_conversion_pct
FROM fact_daily_traffic;

-- Q4: top landing pages by sessions
SELECT
    landing_page,
    SUM(sessions) AS sessions,
    SUM(purchases) AS purchases,
    SUM(revenue_pkr) AS revenue_pkr,
    ROUND(100.0 * SUM(purchases) / SUM(sessions), 2) AS conversion_rate_pct
FROM fact_landing_pages
GROUP BY landing_page
ORDER BY sessions DESC;

-- Q5: device split
SELECT
    device,
    SUM(sessions) AS sessions,
    SUM(purchases) AS purchases,
    SUM(revenue_pkr) AS revenue_pkr,
    ROUND(100.0 * SUM(sessions)
        / (SELECT SUM(sessions) FROM fact_device_split), 2) AS share_pct,
    ROUND(100.0 * SUM(purchases) / SUM(sessions), 2) AS conversion_rate_pct
FROM fact_device_split
GROUP BY device
ORDER BY sessions DESC;

-- Q6: weekend (Fri–Sun) vs weekday
SELECT
    CASE WHEN CAST(strftime('%w', traffic_date) AS INTEGER) >= 5
              OR CAST(strftime('%w', traffic_date) AS INTEGER) = 0
         THEN 'weekend' ELSE 'weekday' END AS day_type,
    COUNT(DISTINCT traffic_date) AS days,
    SUM(sessions) AS sessions,
    SUM(purchases) AS purchases,
    SUM(revenue_pkr) AS revenue_pkr,
    ROUND(1.0 * SUM(sessions) / COUNT(DISTINCT traffic_date), 1) AS sessions_per_day,
    ROUND(100.0 * SUM(purchases) / SUM(sessions), 2) AS conversion_rate_pct
FROM fact_daily_traffic
GROUP BY day_type;

-- Q7: reconciliation — the three files must share the same totals
SELECT 'traffic' AS source, SUM(sessions) AS sessions,
       SUM(purchases) AS purchases, SUM(revenue_pkr) AS revenue_pkr
FROM fact_daily_traffic
UNION ALL
SELECT 'landing_pages', SUM(sessions), SUM(purchases), SUM(revenue_pkr)
FROM fact_landing_pages
UNION ALL
SELECT 'device_split', SUM(sessions), SUM(purchases), SUM(revenue_pkr)
FROM fact_device_split;
