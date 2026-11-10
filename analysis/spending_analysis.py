"""Category-wise spending and income vs expense (MEMBER 3)."""
import pandas as pd

from analysis.transaction_analysis import total_deposits, total_withdrawals


def category_expenses(df):
    """Total withdrawals per category (largest first) -> columns: category, expense, transactions."""
    expenses = df[df["transaction_type"] == "WITHDRAWAL"]
    if expenses.empty:
        return pd.DataFrame({"category": [], "expense": [], "transactions": []})
    result = (expenses.groupby("category")["amount"].agg(["sum", "count"]).reset_index()
              .rename(columns={"sum": "expense", "count": "transactions"})
              .sort_values("expense", ascending=False).reset_index(drop=True))
    return result


def top_spending_categories(df, top_n=5):
    return category_expenses(df).head(top_n)


def income_vs_expense(df):
    """Dictionary with total_income, total_expense and net_balance."""
    income, expense = total_deposits(df), total_withdrawals(df)
    return {"total_income": income, "total_expense": expense, "net_balance": income - expense}


def account_spending(df):
    """Total income and expense of each account -> useful for comparing accounts."""
    if df.empty:
        return pd.DataFrame(columns=["account_number", "customer_name", "income", "expense"])
    table = (df.pivot_table(index=["account_number", "customer_name"], columns="transaction_type",
                            values="amount", aggfunc="sum", fill_value=0.0).reset_index())
    for column in ("DEPOSIT", "WITHDRAWAL"):
        if column not in table.columns:
            table[column] = 0.0
    table = table.rename(columns={"DEPOSIT": "income", "WITHDRAWAL": "expense"})
    table.columns.name = None
    return table[["account_number", "customer_name", "income", "expense"]]
