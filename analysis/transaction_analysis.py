"""
Core transaction analysis with Pandas / NumPy (MEMBER 3).

All analysis functions take a DataFrame with these columns:
transaction_id, account_id, account_number, customer_name, transaction_date,
transaction_type, amount, category, description, reference_number
Only load_transactions() talks to the backend; everything else is pure Pandas,
so it can be tested without a database.
"""
import numpy as np
import pandas as pd

COLUMNS = ["transaction_id", "account_id", "account_number", "customer_name", "transaction_date",
           "transaction_type", "amount", "category", "description", "reference_number"]


def prepare_dataframe(records):
    """Turn a list of dicts (or a DataFrame) into a clean DataFrame with correct data types."""
    df = pd.DataFrame(records)
    for column in COLUMNS:
        if column not in df.columns:
            df[column] = None
    df = df[COLUMNS].copy()
    df["transaction_date"] = pd.to_datetime(df["transaction_date"])
    df["amount"] = pd.to_numeric(df["amount"].astype(str), errors="coerce").astype(float)
    return df


def load_transactions(**filters):
    """Fetch transactions from MySQL (optionally filtered) as a DataFrame."""
    from backend.transaction_service import get_transactions  # imported here to keep analysis DB-free
    return prepare_dataframe(get_transactions(**filters))


def total_deposits(df):
    return float(df.loc[df["transaction_type"] == "DEPOSIT", "amount"].sum())


def total_withdrawals(df):
    return float(df.loc[df["transaction_type"] == "WITHDRAWAL", "amount"].sum())


def calculate_balance(df):
    """Deposits minus withdrawals of the given transactions."""
    return total_deposits(df) - total_withdrawals(df)


def average_transaction(df):
    return float(df["amount"].mean()) if not df.empty else 0.0


def largest_transaction(df):
    """Return the largest transaction as a dict, or None if there is no data."""
    if df.empty:
        return None
    return df.loc[df["amount"].idxmax()].to_dict()


def transaction_statistics(df):
    """count, sum, mean, median, min, max for all / deposits / withdrawals (one row each)."""
    groups = {"ALL": df,
              "DEPOSIT": df[df["transaction_type"] == "DEPOSIT"],
              "WITHDRAWAL": df[df["transaction_type"] == "WITHDRAWAL"]}
    rows = {}
    for name, part in groups.items():
        values = part["amount"].to_numpy(dtype=float)
        if len(values) == 0:
            rows[name] = {"count": 0, "sum": 0.0, "mean": 0.0, "median": 0.0, "min": 0.0, "max": 0.0}
        else:
            rows[name] = {"count": int(len(values)), "sum": float(np.sum(values)),
                          "mean": float(np.mean(values)), "median": float(np.median(values)),
                          "min": float(np.min(values)), "max": float(np.max(values))}
    table = pd.DataFrame(rows).T.rename_axis("type").reset_index()
    table["count"] = table["count"].astype(int)
    return table
