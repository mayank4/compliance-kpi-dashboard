"""
generate_data.py
Generates synthetic payment transaction data for the Compliance KPI Dashboard.

Produces 10,000 realistic-looking transaction records simulating a federal
payment program (similar in shape to the kind of data used in payment integrity
oversight). Injects a small percentage of anomalies so the SQL anomaly
detection views and Power BI dashboard have something real to flag.

Usage:
    python generate_data.py

Output:
    data/transactions.csv
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
NUM_TRANSACTIONS = 10_000
ANOMALY_RATE = 0.005          # 0.5% of records will be anomalous
RANDOM_SEED = 42              # reproducibility: same input always produces same output
OUTPUT_PATH = "data/transactions.csv"

# Simulated payment program parameters
PAYMENT_TYPES = ["refund", "credit", "benefit"]
PAYMENT_TYPE_WEIGHTS = [0.25, 0.30, 0.45]  # benefits most common, refunds least
REGIONS = ["Ontario", "Quebec", "BC", "Alberta", "Atlantic", "Prairies", "Territories"]
REGION_WEIGHTS = [0.38, 0.22, 0.13, 0.11, 0.07, 0.07, 0.02]  # rough population-weighted
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2025, 12, 31)

# Amount ranges by payment type (min, mean, max in dollars)
# Normal distribution parameters tuned per payment type to look realistic
AMOUNT_PARAMS = {
    "refund":  {"mean": 850,  "std": 400,  "min": 50,   "max": 5_000},
    "credit":  {"mean": 1_500, "std": 700,  "min": 100,  "max": 10_000},
    "benefit": {"mean": 2_200, "std": 900,  "min": 200,  "max": 15_000},
}

# -----------------------------------------------------------------------------
# Main generation logic
# -----------------------------------------------------------------------------

def generate_normal_transactions(n: int, rng: np.random.Generator) -> pd.DataFrame:
    """Generate n 'clean' transactions with no injected anomalies."""

    # Payer IDs: simulate 2,000 unique payers, so each makes ~5 transactions on average
    payer_ids = rng.choice(
        [f"PAY{str(i).zfill(6)}" for i in range(1, 2001)],
        size=n,
        replace=True,
    )

    # Payment types drawn with realistic frequency weights
    payment_types = rng.choice(PAYMENT_TYPES, size=n, p=PAYMENT_TYPE_WEIGHTS)

    # Regions weighted by approximate population share
    regions = rng.choice(REGIONS, size=n, p=REGION_WEIGHTS)

    # Amounts: draw from normal distribution per payment type, then clip to min/max
    amounts = np.zeros(n)
    for ptype in PAYMENT_TYPES:
        mask = payment_types == ptype
        params = AMOUNT_PARAMS[ptype]
        raw = rng.normal(loc=params["mean"], scale=params["std"], size=mask.sum())
        amounts[mask] = np.clip(raw, params["min"], params["max"])

    # Timestamps: uniformly distributed between START_DATE and END_DATE
    total_seconds = int((END_DATE - START_DATE).total_seconds())
    random_seconds = rng.integers(0, total_seconds, size=n)
    timestamps = [START_DATE + timedelta(seconds=int(s)) for s in random_seconds]

    # flagged_manual starts False for all (this column represents human review)
    flagged_manual = np.zeros(n, dtype=bool)

    df = pd.DataFrame({
        "payer_id": payer_ids,
        "amount": np.round(amounts, 2),
        "payment_type": payment_types,
        "region": regions,
        "timestamp": timestamps,
        "flagged_manual": flagged_manual,
    })

    return df


def inject_anomalies(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """
    Inject three types of anomalies into ~0.5% of records total.

    Anomaly types (documented for the interview):
    1. Amount outliers  : transactions with abnormally high amounts (3x the normal cap)
    2. Frequency burst  : same payer_id receives 5+ transactions within 1 hour
    3. Wrong region     : region doesn't match historical pattern for that payer
    """

    num_anomalies = int(len(df) * ANOMALY_RATE)

    # Split anomaly budget roughly evenly across the 3 types
    n_amount = num_anomalies // 3
    n_frequency = num_anomalies // 3
    n_region = num_anomalies - n_amount - n_frequency  # remainder goes here

    # --- Anomaly 1: abnormally high amounts ---
    outlier_idx = rng.choice(df.index, size=n_amount, replace=False)
    for idx in outlier_idx:
        ptype = df.at[idx, "payment_type"]
        # Amount becomes 3x to 5x the payment type's normal max
        multiplier = rng.uniform(3.0, 5.0)
        df.at[idx, "amount"] = round(AMOUNT_PARAMS[ptype]["max"] * multiplier, 2)
        df.at[idx, "flagged_manual"] = True  # mark as manually reviewed (for realism)

    # --- Anomaly 2: frequency burst ---
    # Pick a few payer_ids and cram 5-8 transactions into a 1-hour window
    num_bursts = max(1, n_frequency // 6)  # each burst = ~6 transactions
    burst_payers = rng.choice(df["payer_id"].unique(), size=num_bursts, replace=False)
    for payer in burst_payers:
        burst_time = START_DATE + timedelta(
            seconds=int(rng.integers(0, int((END_DATE - START_DATE).total_seconds())))
        )
        payer_rows = df[df["payer_id"] == payer].index[:6]  # affect up to 6 of their txns
        for i, idx in enumerate(payer_rows):
            df.at[idx, "timestamp"] = burst_time + timedelta(minutes=int(i * 8))

    # --- Anomaly 3: unusual region for payer ---
    region_idx = rng.choice(df.index, size=n_region, replace=False)
    for idx in region_idx:
        current_region = df.at[idx, "region"]
        # Assign a random other region (excluding current and Territories which is rare)
        other_regions = [r for r in REGIONS if r != current_region and r != "Territories"]
        df.at[idx, "region"] = rng.choice(other_regions)

    return df


def main():
    # Set seed for reproducibility
    rng = np.random.default_rng(RANDOM_SEED)

    print(f"Generating {NUM_TRANSACTIONS:,} transactions...")
    df = generate_normal_transactions(NUM_TRANSACTIONS, rng)

    print(f"Injecting anomalies at {ANOMALY_RATE:.1%} rate...")
    df = inject_anomalies(df, rng)

    # Add a sequential transaction_id AFTER anomaly injection
    # (so IDs are clean 1, 2, 3... regardless of row reordering)
    df = df.sort_values("timestamp").reset_index(drop=True)
    df.insert(0, "transaction_id", [f"TXN{str(i).zfill(8)}" for i in range(1, len(df) + 1)])

    # Save to CSV
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved {len(df):,} rows to {OUTPUT_PATH}")

    # Quick summary for sanity check
    print("\nSummary:")
    print(f"  Date range      : {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"  Unique payers   : {df['payer_id'].nunique():,}")
    print(f"  Payment types   : {df['payment_type'].value_counts().to_dict()}")
    print(f"  Total amount    : ${df['amount'].sum():,.2f}")
    print(f"  Flagged (manual): {df['flagged_manual'].sum()} transactions")
    print(f"  Max amount seen : ${df['amount'].max():,.2f}")


if __name__ == "__main__":
    main()