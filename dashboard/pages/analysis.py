"""Analysis page: statistics, monthly, category, income vs expense, unusual (MEMBER 4)."""
import streamlit as st

from analysis.monthly_analysis import monthly_expenses, monthly_income, monthly_summary
from analysis.spending_analysis import account_spending, category_expenses, income_vs_expense, top_spending_categories
from analysis.transaction_analysis import (average_transaction, largest_transaction, load_transactions,
                                           transaction_statistics)
from analysis.unusual_transactions import unusual_transactions
from dashboard import theme
from dashboard.components import charts, tables
from utils.helpers import format_inr


def render():
    theme.page_header("📈", "Transaction Analysis", "Statistics, monthly trends, category spending and unusual transactions.")
    st.sidebar.header("Filters")
    filters = tables.transaction_filters(st.sidebar, "ana")
    settings = tables.unusual_settings(st.sidebar, "ana")

    df = tables.run_safely(load_transactions, default=None, **filters)
    if df is None:
        return
    if df.empty:
        st.info("No transactions match the selected filters.")
        return

    stats_tab, monthly_tab, category_tab, balance_tab, unusual_tab = st.tabs(
        ["Statistics", "Monthly", "Categories", "Income vs Expense", "Unusual Transactions"])

    with stats_tab:
        largest = largest_transaction(df)
        cols = st.columns(2)
        cols[0].metric("Average transaction", format_inr(average_transaction(df)))
        cols[1].metric("Largest transaction", format_inr(largest["amount"]),
                       f"#{largest['transaction_id']} - {largest['category']}", delta_color="off")
        tables.show_table(transaction_statistics(df), money_columns=["sum", "mean", "median", "min", "max"])
        tables.show_chart(charts.amount_histogram(df), key="ana_hist")

    with monthly_tab:
        tables.show_chart(charts.monthly_expense_chart(monthly_expenses(df)), key="ana_month_exp")
        tables.show_chart(charts.monthly_net_chart(monthly_summary(df)), key="ana_month_net")
        left, right = st.columns(2)
        with left:
            st.write("**Monthly expenses**")
            tables.show_table(monthly_expenses(df))
        with right:
            st.write("**Monthly income**")
            tables.show_table(monthly_income(df))

    with category_tab:
        categories = category_expenses(df)
        left, right = st.columns(2)
        with left:
            tables.show_chart(charts.category_bar_chart(categories), key="ana_cat_bar")
        with right:
            tables.show_chart(charts.category_pie_chart(categories), key="ana_cat_pie")
        st.write("**Top 5 spending categories**")
        tables.show_table(top_spending_categories(df, 5), money_columns=["expense"])

    with balance_tab:
        totals = income_vs_expense(df)
        cols = st.columns(3)
        cols[0].metric("Total Income", format_inr(totals["total_income"]))
        cols[1].metric("Total Expense", format_inr(totals["total_expense"]))
        cols[2].metric("Net Balance", format_inr(totals["net_balance"]))
        tables.show_chart(charts.income_vs_expense_chart(monthly_summary(df)), key="ana_inc_exp")
        tables.show_chart(charts.account_comparison_chart(account_spending(df)), key="ana_accounts")

    with unusual_tab:
        st.write("Change the rule thresholds in the sidebar (Unusual transaction settings).")
        tables.show_unusual_transactions(unusual_transactions(df, **settings))
