# Compliance KPI Dashboard
End-to-end compliance analytics demo showing how synthetic payment transaction data can be surfaced
through SQL-based anomaly detection and a Power BI oversight dashboard.
![Dashboard screenshot](screenshots/dashboard-main.png)
## What this project demonstrates
- Python-based synthetic data generation with controllable anomaly injection
- PostgreSQL data modeling with analytic views (CTEs, window functions, aggregates)
- Power BI dashboard with DAX measures for risk scoring
- End-to-end reproducibility from raw data to visualization
## Stack
| Layer | Tool |
|---|---|
| Data generation | Python (pandas, numpy) |
| Storage | PostgreSQL (Supabase) |
| Modeling | SQL (views, CTEs, window functions) |
| Visualization | Power BI, DAX |
## Architecture

## Data model
### Source table: `transactions` (10,000 rows)
| Column | Type | Description |
|---|---|---|
| transaction_id | text | Unique identifier |
| payer_id | text | Payer reference (~2000 unique) |
| amount | numeric | Transaction amount CAD |
| payment_type | text | refund / credit / benefit |
| region | text | Canadian region |
| timestamp | timestamptz | Transaction time |
| flagged_manual | bool | Manual review flag |
### Views
- `vw_daily_kpis`: daily aggregates by region and payment_type
- `vw_anomaly_amount_outliers`: >3 std dev transactions
- `vw_anomaly_frequency_bursts`: 5+ transactions from same payer within 1 hour
- `vw_anomaly_region_mismatch`: region differs from payer's historical mode
- `vw_all_anomalies`: union of all three for unified dashboard
## DAX measures
- `Total Volume` = sum of amount
- `Flagged Count` = count where flagged_manual is true
- `Flagged Rate` = flagged count / total count
- `Risk Score` = flagged rate × total volume / 1,000,000 (proxy for aggregate exposure)
## How to reproduce
1. Clone this repo
2. Install Python dependencies: `pip install -r requirements.txt`
3. Generate data: `python generate_data.py`
4. Sign up for Supabase (free tier) and create a new project
5. Import `data/transactions.csv` into a table named `transactions`
6. Run the SQL files in order: `sql/01_daily_kpis.sql` then `sql/02_anomaly_detection.sql`
7. Open `dashboard.pbix` in Power BI Desktop and update the connection string
## What I learned
- **Window functions save a lot of code.** The frequency burst detection is 8 lines of SQL with a
window function vs. 40+ lines with self-joins.
- **Seeded randomness is critical for reproducibility.** Without a fixed seed, anomaly counts would
drift every run and dashboards would never match source data exactly.
- **DAX Risk Score is a simplification.** A real program would weight anomaly types differently
(frequency bursts are often more severe than region mismatches) and probably use historical
baselines per payer rather than global means.
## What I would add with more time
- Logistic regression classifier trained on `flagged_manual` to predict anomaly likelihood in real
time
- dbt to orchestrate the SQL views instead of raw CREATE VIEW statements
- Airflow DAG to schedule daily data refresh and alerting
- Unit tests on the Python generator using pytest

  ## License
MIT
