# compliance-kpi-dashboard
End-to-end compliance analytics demo: synthetic payment data, SQL anomaly detection, Power BI oversight dashboard.


# Compliance KPI Dashboard

End-to-end compliance analytics demo: synthetic payment transaction data generated in Python, loaded into PostgreSQL, modeled with SQL views, and surfaced through a Power BI dashboard with DAX-based risk scoring measures.

## Status

This project is under active development.

- [x] Day 1: Synthetic data generator (Python)
- [ ] Day 2: PostgreSQL setup and daily KPI views
- [ ] Day 3: Anomaly detection SQL views
- [ ] Day 4: Power BI dashboard with DAX measures
- [ ] Day 5: Documentation and screenshots

## Why this exists

Inspired by federal payment integrity programs: the goal is to surface suspicious transactions to compliance officers fast enough to stop erroneous payments before they go out the door. This is a portfolio project that mirrors the pattern, not real data from any agency.

## Stack

- **Python** (pandas, numpy) for synthetic data generation
- **PostgreSQL** (via Supabase free tier) for storage and SQL modeling
- **Power BI** for the final dashboard and DAX measures

## How to reproduce

1. Clone this repo.
2. Install Python dependencies: `pip install -r requirements.txt`
3. Run the data generator: `python generate_data.py`
4. Output: `data/transactions.csv` with 10,000 rows.

## Data model

| Column | Type | Description |
|---|---|---|
| transaction_id | string | Unique identifier (TXN00000001 format) |
| payer_id | string | Payer reference (PAY000001 format, ~2000 unique payers) |
| amount | float | Transaction amount in CAD |
| payment_type | string | One of: refund, credit, benefit |
| region | string | Canadian region code |
| timestamp | datetime | When the transaction occurred |
| flagged_manual | bool | Whether a compliance officer manually reviewed this |

## Anomaly types injected

The generator seeds ~0.5% of records with realistic anomalies so downstream SQL views and dashboards have something to detect:

1. **Amount outliers:** transactions 3-5x the normal cap for their payment type
2. **Frequency bursts:** same payer receives 6+ transactions within an hour
3. **Unusual regions:** payer's region differs from their typical pattern

## License

MIT