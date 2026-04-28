-- 02_anomaly_detection.sql
-- Three anomaly detection views mirroring payment-integrity oversight patterns.
-- Anomaly 1: amount outliers (>3 std dev from mean for that payment_type)
CREATE OR REPLACE VIEW vw_anomaly_amount_outliers AS
WITH type_stats AS (
SELECT
payment_type,
AVG(amount) AS mean_amount,
STDDEV(amount) AS std_amount
FROM transactions
GROUP BY payment_type
) SELECT
t.transaction_id,
t.payer_id,
t.amount,
t.payment_type,
t.region,
t.timestamp,
ROUND(((t.amount - s.mean_amount) / NULLIF(s.std_amount, 0))::numeric, 2) AS z_score,
'amount_outlier' AS anomaly_type
FROM transactions t
JOIN type_stats s ON t.payment_type = s.payment_type
WHERE ABS((t.amount - s.mean_amount) / NULLIF(s.std_amount, 0)) > 3
ORDER BY ABS((t.amount - s.mean_amount) / NULLIF(s.std_amount, 0)) DESC;
-- Anomaly 2: frequency bursts (same payer 5+ transactions within 1 hour)
CREATE OR REPLACE VIEW vw_anomaly_frequency_bursts AS
WITH rolling_counts AS (
SELECT
transaction_id,
payer_id,
timestamp,
amount,
payment_type,
COUNT(*) OVER (
PARTITION BY payer_id
ORDER BY timestamp
RANGE BETWEEN INTERVAL '1 hour' PRECEDING AND CURRENT ROW
) AS txns_last_hour
FROM transactions
) SELECT
transaction_id,
payer_id,
timestamp,
amount,
payment_type,
txns_last_hour,
'frequency_burst' AS anomaly_type
FROM rolling_counts
WHERE txns_last_hour >= 5
ORDER BY txns_last_hour DESC, payer_id, timestamp;
-- Anomaly 3: payer region mismatch (region differs from their historical mode)
CREATE OR REPLACE VIEW vw_anomaly_region_mismatch AS
WITH payer_modes AS (
SELECT DISTINCT ON (payer_id)
payer_id,
region AS typical_region
FROM (
SELECT payer_id, region, COUNT(*) AS cnt
FROM transactions
GROUP BY payer_id, region
) ranked
ORDER BY payer_id, cnt DESC
) SELECT
t.transaction_id,
t.payer_id,
t.region AS transaction_region,
p.typical_region,
t.amount,
t.timestamp,
'region_mismatch' AS anomaly_type
FROM transactions t
JOIN payer_modes p ON t.payer_id = p.payer_id
WHERE t.region != p.typical_region
ORDER BY t.timestamp DESC;
-- Union view combining all anomalies for easy dashboard consumption
CREATE OR REPLACE VIEW vw_all_anomalies AS
SELECT transaction_id, payer_id, amount, timestamp, anomaly_type
FROM vw_anomaly_amount_outliers
UNION ALL
SELECT transaction_id, payer_id, amount, timestamp, anomaly_type
FROM vw_anomaly_frequency_bursts
UNION ALL
SELECT transaction_id, payer_id, amount, timestamp, anomaly_type
FROM vw_anomaly_region_mismatch;
