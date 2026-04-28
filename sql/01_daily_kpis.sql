-- 01_daily_kpis.sql
-- Daily KPI rollup view for the compliance dashboard.
-- Aggregates volume, count, and flagged counts by date, region, and payment_type.
CREATE OR REPLACE VIEW vw_daily_kpis AS
SELECT
DATE(timestamp) AS txn_date,
region,
payment_type,
COUNT(*) AS txn_count,
SUM(amount) AS total_amount,
AVG(amount) AS avg_amount,
MIN(amount) AS min_amount,
MAX(amount) AS max_amount,
SUM(CASE WHEN flagged_manual THEN 1 ELSE 0 END) AS flagged_count,
ROUND(
100.0 * SUM(CASE WHEN flagged_manual THEN 1 ELSE 0 END) / COUNT(*),
2
) AS flagged_pct
FROM transactions
GROUP BY DATE(timestamp), region, payment_type
ORDER BY txn_date DESC, region, payment_type;