"""Month-wise analysis (MEMBER 3). Months are shown as 'YYYY-MM'."""
import pandas as pd


def _with_month(df):
    df = df.copy()
    df["month"] = df["transaction_date"].dt.strftime("%Y-%m")
    return df


def _monthly_total(df, transaction_type, column_name):
    part = _with_month(df[df["transaction_type"] == transaction_type])
    if part.empty:
        return pd.DataFrame({"month": [], column_name: []})
    result = part.groupby("month", as_index=False)["amount"].sum()
    return result.rename(columns={"amount": column_name}).sort_values("month").reset_index(drop=True)


def monthly_expenses(df):
    """Total withdrawals per month -> columns: month, expense."""
    return _monthly_total(df, "WITHDRAWAL", "expense")


def monthly_income(df):
    """Total deposits per month -> columns: month, income."""
    return _monthly_total(df, "DEPOSIT", "income")


def monthly_summary(df):
    """Income, expense and net for every month -> columns: month, income, expense, net."""
    summary = pd.merge(monthly_income(df), monthly_expenses(df), on="month", how="outer")
    if summary.empty:
        return pd.DataFrame(columns=["month", "income", "expense", "net"])
    summary = summary.fillna(0.0).sort_values("month").reset_index(drop=True)
    summary["net"] = summary["income"] - summary["expense"]
    return summary
