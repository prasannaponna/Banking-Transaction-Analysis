"""Main dashboard page: KPI cards, charts, recent transactions, alerts (MEMBER 4)."""
import streamlit as st

from analysis.monthly_analysis import monthly_expenses, monthly_summary
from analysis.spending_analysis import category_expenses
from analysis.transaction_analysis import load_transactions, total_deposits, total_withdrawals
from analysis.unusual_transactions import unusual_transactions
from backend import account_service, balance_service, customer_service
from dashboard import theme
from dashboard.components import charts, tables
from utils.helpers import format_inr


def render():
    theme.page_header("📊", "Banking Transaction Dashboard", "Live overview of balances, cash flow, spending and unusual activity.")

    st.sidebar.header("Filters")
    filters = tables.transaction_filters(st.sidebar, "dash")
    settings = tables.unusual_settings(st.sidebar, "dash")

    df = tables.run_safely(load_transactions, default=None, **filters)
    if df is None:
        return

    # --- KPI cards ---
    customers_count = tables.run_safely(customer_service.count_customers, default=0)
    accounts_count = tables.run_safely(account_service.count_accounts, default=0)
    total_balance = tables.run_safely(balance_service.get_total_balance, default=0)

    row1 = st.columns(3)
    with row1[0]:
        theme.kpi_card("Total Customers", customers_count, "👥", "blue")
    with row1[1]:
        theme.kpi_card("Total Accounts", accounts_count, "🏦", "teal")
    with row1[2]:
        theme.kpi_card("Total Balance", format_inr(total_balance), "💰", "amber", "Active accounts only")
    row2 = st.columns(3)
    with row2[0]:
        theme.kpi_card("Total Deposits", format_inr(total_deposits(df)), "⬇️", "green")
    with row2[1]:
        theme.kpi_card("Total Withdrawals", format_inr(total_withdrawals(df)), "⬆️", "red")
    with row2[2]:
        theme.kpi_card("Total Transactions", len(df), "🔁", "blue")
    st.caption("Deposits, withdrawals and transaction count follow the filters in the sidebar.")

    # --- charts ---
    theme.section_title("📊", "Spending & Cash Flow")
    left, right = st.columns(2)
    with left:
        tables.show_chart(charts.monthly_expense_chart(monthly_expenses(df)), key="dash_monthly")
    with right:
        tables.show_chart(charts.income_vs_expense_chart(monthly_summary(df)), key="dash_income_expense")
    tables.show_chart(charts.category_pie_chart(category_expenses(df)), key="dash_category_chart")

    # --- recent transactions ---
    theme.section_title("🕒", "Recent Transactions")
    recent = df.head(10)[["transaction_id", "transaction_date", "account_number", "customer_name",
                          "transaction_type", "amount", "category", "description"]]
    tables.show_table(recent)

    # --- unusual transaction alerts ---
    theme.section_title("🚨", "Unusual Transaction Alerts")
    tables.show_unusual_transactions(unusual_transactions(df, **settings))
