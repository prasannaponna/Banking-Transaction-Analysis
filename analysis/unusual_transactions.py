"""
Unusual transaction detection (MEMBER 3).

IMPORTANT: this is a simple, rule-based "unusual transaction detection" feature made
for a college project. It is NOT a real banking fraud detection system. A flagged
transaction is only *unusual*, not necessarily wrong or fraudulent.

Rules (every threshold can be changed):
  1. HIGH vs NORMAL : amount is more than `z_threshold` standard deviations above the
                      average amount of the same account and same transaction type.
  2. HIGH AMOUNT    : amount is at least `amount_threshold` rupees.
  3. FREQUENCY      : `max_transactions` or more transactions on one account within
                      `window_minutes` minutes (the transaction that reaches the limit
                      and the ones after it are flagged).
"""
import numpy as np
import pandas as pd

OUTPUT_COLUMNS = ["transaction_id", "account_number", "customer_name", "transaction_date",
                  "transaction_type", "amount", "category", "reason"]

DEFAULT_Z_THRESHOLD = 3.0
DEFAULT_AMOUNT_THRESHOLD = 50000.0
DEFAULT_MAX_TRANSACTIONS = 5
DEFAULT_WINDOW_MINUTES = 60
MIN_HISTORY = 8  # rule 1 needs at least this many past transactions to know what "normal" is
IGNORED_CATEGORIES = ("Opening Balance",)


def _rule_high_vs_normal(df, z_threshold):
    reasons = {}
    for (_, _), group in df.groupby(["account_id", "transaction_type"]):
        if len(group) < MIN_HISTORY:
            continue
        mean, std = group["amount"].mean(), group["amount"].std(ddof=0)
        if std == 0:
            continue
        for index, row in group.iterrows():
            if (row["amount"] - mean) / std > z_threshold:
                reasons.setdefault(index, []).append(
                    f"Transaction is significantly higher than the account's normal "
                    f"{row['transaction_type'].lower()} amount (average ₹{mean:,.0f}).")
    return reasons


def _rule_high_amount(df, amount_threshold):
    reasons = {}
    for index in df.index[df["amount"] >= amount_threshold]:
        reasons.setdefault(index, []).append(f"Amount is above the configured limit of ₹{amount_threshold:,.0f}.")
    return reasons


def _rule_frequency(df, max_transactions, window_minutes):
    reasons = {}
    window = np.timedelta64(int(window_minutes), "m")
    for _, group in df.groupby("account_id"):
        group = group.sort_values("transaction_date")
        times = group["transaction_date"].to_numpy(dtype="datetime64[ns]")
        for position, index in enumerate(group.index):
            start = np.searchsorted(times, times[position] - window, side="left")
            count = position - start + 1
            if count >= max_transactions:
                reasons.setdefault(index, []).append(
                    f"{count} transactions on this account within {int(window_minutes)} minutes (too frequent).")
    return reasons


def unusual_transactions(df, z_threshold=DEFAULT_Z_THRESHOLD, amount_threshold=DEFAULT_AMOUNT_THRESHOLD,
                         max_transactions=DEFAULT_MAX_TRANSACTIONS, window_minutes=DEFAULT_WINDOW_MINUTES):
    """Return the flagged transactions with a `reason` column (empty DataFrame if none)."""
    if df.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    data = df[~df["category"].isin(IGNORED_CATEGORIES)]

    all_reasons = {}
    for found in (_rule_high_vs_normal(data, z_threshold),
                  _rule_high_amount(data, amount_threshold),
                  _rule_frequency(data, max_transactions, window_minutes)):
        for index, messages in found.items():
            all_reasons.setdefault(index, []).extend(messages)
    if not all_reasons:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    flagged = data.loc[list(all_reasons)].copy()
    flagged["reason"] = [" ".join(all_reasons[index]) for index in flagged.index]
    return flagged[OUTPUT_COLUMNS].sort_values("transaction_date", ascending=False).reset_index(drop=True)
