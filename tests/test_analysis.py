"""Analysis tests with a small hand-made DataFrame (no database needed)."""
import pandas as pd

from analysis.monthly_analysis import monthly_expenses, monthly_income, monthly_summary
from analysis.report_generator import build_report, to_csv_bytes
from analysis.spending_analysis import category_expenses, income_vs_expense, top_spending_categories
from analysis.transaction_analysis import (average_transaction, calculate_balance, largest_transaction,
                                           prepare_dataframe, total_deposits, total_withdrawals,
                                           transaction_statistics)
from analysis.unusual_transactions import unusual_transactions


def make_df():
    rows = [
        (1, 1, "2026-01-01 09:00", "DEPOSIT", 10000, "Salary"),
        (2, 1, "2026-01-05 12:00", "WITHDRAWAL", 1000, "Food"),
        (3, 1, "2026-01-20 12:00", "WITHDRAWAL", 3000, "Shopping"),
        (4, 1, "2026-02-01 09:00", "DEPOSIT", 10000, "Salary"),
        (5, 1, "2026-02-10 12:00", "WITHDRAWAL", 2000, "Food"),
    ]
    records = [{"transaction_id": i, "account_id": a, "account_number": f"100000000{a}", "customer_name": "Test",
                "transaction_date": d, "transaction_type": t, "amount": amt, "category": c,
                "description": "", "reference_number": f"R{i}"} for i, a, d, t, amt, c in rows]
    return prepare_dataframe(records)


def make_history_df():
    """20 small daily withdrawals plus one huge one (id 999)."""
    records = []
    for i in range(20):
        records.append({"transaction_id": i + 1, "account_id": 1, "account_number": "1000000001",
                        "customer_name": "T", "transaction_date": f"2026-02-{i + 1:02d} 10:00",
                        "transaction_type": "WITHDRAWAL", "amount": 500 + i * 10, "category": "Food",
                        "description": "", "reference_number": f"H{i}"})
    records.append({"transaction_id": 999, "account_id": 1, "account_number": "1000000001",
                    "customer_name": "T", "transaction_date": "2026-03-01 10:00",
                    "transaction_type": "WITHDRAWAL", "amount": 9000, "category": "Shopping",
                    "description": "", "reference_number": "H999"})
    return prepare_dataframe(records)


def test_totals_and_balance():
    df = make_df()
    assert total_deposits(df) == 20000
    assert total_withdrawals(df) == 6000
    assert calculate_balance(df) == 14000


def test_average_and_largest():
    df = make_df()
    assert average_transaction(df) == 5200
    assert largest_transaction(df)["amount"] == 10000
    assert largest_transaction(df.iloc[0:0]) is None


def test_statistics():
    stats = transaction_statistics(make_df()).set_index("type")
    assert stats.loc["ALL", "count"] == 5
    assert stats.loc["WITHDRAWAL", "sum"] == 6000
    assert stats.loc["DEPOSIT", "mean"] == 10000
    assert stats.loc["WITHDRAWAL", "min"] == 1000 and stats.loc["WITHDRAWAL", "max"] == 3000


def test_monthly_analysis():
    df = make_df()
    expenses = monthly_expenses(df).set_index("month")["expense"]
    assert expenses["2026-01"] == 4000 and expenses["2026-02"] == 2000
    assert monthly_income(df).set_index("month")["income"]["2026-01"] == 10000
    summary = monthly_summary(df).set_index("month")
    assert summary.loc["2026-01", "net"] == 6000


def test_category_analysis_and_income_vs_expense():
    df = make_df()
    categories = category_expenses(df).set_index("category")["expense"]
    assert categories["Food"] == 3000 and categories["Shopping"] == 3000
    assert len(top_spending_categories(df, 1)) == 1
    assert income_vs_expense(df) == {"total_income": 20000.0, "total_expense": 6000.0, "net_balance": 14000.0}


def test_empty_dataframe_does_not_crash():
    empty = make_df().iloc[0:0]
    assert total_deposits(empty) == 0 and average_transaction(empty) == 0
    assert monthly_summary(empty).empty and category_expenses(empty).empty
    assert unusual_transactions(empty).empty
    assert build_report("Transaction report", empty).empty


def test_unusual_amount_much_higher_than_normal():
    flagged = unusual_transactions(make_history_df(), amount_threshold=1_000_000)
    assert list(flagged["transaction_id"]) == [999]
    assert "significantly higher" in flagged.iloc[0]["reason"]


def test_unusual_amount_threshold_is_configurable():
    df = make_df()
    assert len(unusual_transactions(df, amount_threshold=5000)) == 2          # both 10,000 salaries
    assert unusual_transactions(df, amount_threshold=50000).empty


def test_unusual_frequency_rule():
    records = [{"transaction_id": i, "account_id": 2, "account_number": "1000000002", "customer_name": "T",
                "transaction_date": f"2026-04-01 10:{i * 5:02d}", "transaction_type": "WITHDRAWAL",
                "amount": 100, "category": "Food", "description": "", "reference_number": f"F{i}"}
               for i in range(1, 8)]
    flagged = unusual_transactions(prepare_dataframe(records), max_transactions=5, window_minutes=60)
    assert len(flagged) == 3  # the 5th, 6th and 7th transaction within one hour
    assert "too frequent" in flagged.iloc[0]["reason"]


def test_csv_export_is_bytes():
    data = to_csv_bytes(build_report("Transaction report", make_df()))
    assert isinstance(data, bytes) and b"transaction_id" in data
