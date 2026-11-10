"""Build report tables and CSV bytes for download (MEMBER 3)."""
import pandas as pd

from analysis.monthly_analysis import monthly_summary
from analysis.spending_analysis import category_expenses
from analysis.unusual_transactions import unusual_transactions

REPORT_NAMES = ["Transaction report", "Monthly spending report",
                "Category spending report", "Unusual transaction report"]


def transaction_report(df):
    """All given transactions, newest first."""
    columns = ["transaction_id", "transaction_date", "account_number", "customer_name",
               "transaction_type", "amount", "category", "description", "reference_number"]
    return df[columns].sort_values("transaction_date", ascending=False).reset_index(drop=True)


def monthly_spending_report(df):
    return monthly_summary(df)


def category_spending_report(df):
    return category_expenses(df)


def unusual_transaction_report(df, **settings):
    return unusual_transactions(df, **settings)


def build_report(report_name, df, **unusual_settings):
    """Return the DataFrame for one of REPORT_NAMES."""
    if report_name == "Transaction report":
        return transaction_report(df)
    if report_name == "Monthly spending report":
        return monthly_spending_report(df)
    if report_name == "Category spending report":
        return category_spending_report(df)
    if report_name == "Unusual transaction report":
        return unusual_transaction_report(df, **unusual_settings)
    raise ValueError(f"Unknown report: {report_name}")


def to_csv_bytes(report_df):
    """CSV as bytes with a BOM so Excel shows the ₹ sign correctly."""
    return report_df.to_csv(index=False).encode("utf-8-sig")


def report_file_name(report_name):
    return report_name.lower().replace(" ", "_") + ".csv"
