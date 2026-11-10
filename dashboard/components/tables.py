"""Shared Streamlit widgets: tables, filters, error handling (MEMBER 4)."""
from datetime import date

import pandas as pd
import streamlit as st

from analysis import unusual_transactions as unusual
from backend import account_service, transaction_service
from backend.db_connection import DatabaseError
from utils.helpers import format_inr
from utils.validators import ValidationError

MONEY_COLUMNS = ("amount", "balance", "income", "expense", "net", "sum", "mean", "median", "min", "max")


def run_safely(function, *args, default=None, **kwargs):
    """Call a backend function; show a friendly message instead of crashing."""
    try:
        return function(*args, **kwargs)
    except (ValidationError, DatabaseError) as error:
        st.error(str(error))
    except Exception:  # unexpected bug: do not show technical details to the user
        st.error("Something went wrong. Please try again.")
    return default


def records_to_df(records):
    """List of dicts from the backend -> DataFrame (Decimal money values become floats)."""
    df = pd.DataFrame(records)
    for column in df.columns:
        if column in ("amount", "balance"):
            df[column] = df[column].astype(float)
    return df


def show_table(df, money_columns=None, **kwargs):
    """Show a DataFrame as a nice full-width table with ₹ formatting."""
    if df is None or df.empty:
        st.info("No records to show.")
        return
    columns = money_columns if money_columns is not None else [c for c in df.columns if c in MONEY_COLUMNS]
    config = {c: st.column_config.NumberColumn(c.replace("_", " ").title(), format="₹%.2f")
              for c in columns if c in df.columns and c != "count"}
    try:
        st.dataframe(df, hide_index=True, column_config=config, width="stretch", **kwargs)
    except TypeError:  # older Streamlit versions only accept use_container_width
        st.dataframe(df, hide_index=True, column_config=config, use_container_width=True, **kwargs)


def show_chart(figure, key=None):
    """Draw a Plotly figure at full width (works on old and new Streamlit versions)."""
    try:
        st.plotly_chart(figure, width="stretch", key=key)
    except TypeError:  # older Streamlit versions only accept use_container_width
        st.plotly_chart(figure, use_container_width=True, key=key)


def show_money(label, amount):
    st.metric(label, format_inr(amount))


def account_options(only_active=False):
    """{label: account_id} for dropdowns."""
    accounts = run_safely(account_service.get_all_accounts, "ACTIVE" if only_active else None, default=[])
    return {f"{a['account_number']} - {a['customer_name']} ({a['account_type']})": a["account_id"]
            for a in accounts}


def transaction_filters(container, key_prefix):
    """
    Draw Account / Date range / Type / Category filters inside `container`
    (for example st.sidebar) and return a dict that can be passed to
    transaction_service.get_transactions() or analysis.load_transactions().
    """
    accounts = account_options()
    account_label = container.selectbox("Account", ["All accounts"] + list(accounts), key=f"{key_prefix}_account")

    start_date = end_date = None
    bounds = run_safely(transaction_service.get_date_range, default=None)
    if bounds:
        chosen = container.date_input("Date range", value=(bounds[0], max(bounds[1], date.today())),
                                      key=f"{key_prefix}_dates")
        if isinstance(chosen, (tuple, list)):
            if len(chosen) == 2:
                start_date, end_date = chosen
            elif len(chosen) == 1:
                start_date = end_date = chosen[0]
        else:
            start_date = end_date = chosen

    type_label = container.selectbox("Transaction type", ["All", "DEPOSIT", "WITHDRAWAL"], key=f"{key_prefix}_type")
    categories = run_safely(transaction_service.get_categories, default=[])
    category_label = container.selectbox("Category", ["All"] + categories, key=f"{key_prefix}_category")

    return {
        "account_id": accounts.get(account_label),
        "start_date": start_date,
        "end_date": end_date,
        "transaction_type": None if type_label == "All" else type_label,
        "category": None if category_label == "All" else category_label,
    }


def unusual_settings(container, key_prefix):
    """Configurable thresholds for the unusual-transaction rules. Returns keyword arguments."""
    with container.expander("Unusual transaction settings"):
        z_threshold = st.number_input("Higher than normal (std. deviations)", min_value=1.0, max_value=10.0,
                                      value=unusual.DEFAULT_Z_THRESHOLD, step=0.5, key=f"{key_prefix}_z")
        amount_threshold = st.number_input("Amount limit (₹)", min_value=1000.0,
                                           value=unusual.DEFAULT_AMOUNT_THRESHOLD, step=5000.0,
                                           key=f"{key_prefix}_limit")
        max_transactions = st.number_input("Max transactions in time window", min_value=2, max_value=50,
                                           value=unusual.DEFAULT_MAX_TRANSACTIONS, step=1, key=f"{key_prefix}_max")
        window_minutes = st.number_input("Time window (minutes)", min_value=5, max_value=1440,
                                         value=unusual.DEFAULT_WINDOW_MINUTES, step=5, key=f"{key_prefix}_window")
    return {"z_threshold": float(z_threshold), "amount_threshold": float(amount_threshold),
            "max_transactions": int(max_transactions), "window_minutes": int(window_minutes)}


def show_unusual_transactions(flagged_df):
    """Show alerts for flagged transactions (used on the dashboard and analysis page)."""
    st.caption("Rule-based unusual transaction detection for a college project - "
               "this is NOT a real banking fraud detection system.")
    if flagged_df.empty:
        st.success("No unusual transactions found with the current settings.")
        return
    st.warning(f"{len(flagged_df)} unusual transaction(s) flagged.")
    show_table(flagged_df)
