"""Transaction management page: view/search/filter, add, edit, delete (MEMBER 4)."""
from datetime import date, datetime

import streamlit as st

from backend import account_service, balance_service, transaction_service
from dashboard import theme
from dashboard.components import tables
from utils.helpers import ALL_CATEGORIES, format_inr


def _view_tab():
    st.sidebar.header("Transaction filters")
    filters = tables.transaction_filters(st.sidebar, "tx")

    cols = st.columns([2, 1, 1])
    keyword = cols[0].text_input("Search (description, reference, category, account number)", key="tx_keyword")
    min_amount = cols[1].number_input("Min amount (₹)", min_value=0.0, value=0.0, step=100.0, key="tx_min")
    max_amount = cols[2].number_input("Max amount (₹, 0 = no limit)", min_value=0.0, value=0.0, step=100.0,
                                      key="tx_max")

    records = tables.run_safely(
        transaction_service.get_transactions, default=[],
        keyword=keyword, min_amount=min_amount or None, max_amount=max_amount or None, **filters)
    st.write(f"{len(records)} transaction(s) found")
    tables.show_table(tables.records_to_df(records))


def _add_tab():
    options = tables.account_options(only_active=True)
    if not options:
        st.info("No active accounts. Open an account first.")
        return
    with st.form("add_transaction_form", clear_on_submit=True):
        account_label = st.selectbox("Account", list(options))
        transaction_type = st.selectbox("Transaction type", ["DEPOSIT", "WITHDRAWAL"])
        amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0, format="%.2f")
        date_col, time_col = st.columns(2)
        tx_date = date_col.date_input("Date", value=date.today(), max_value=date.today())
        tx_time = time_col.time_input("Time", value=datetime.now().time())
        category = st.selectbox("Category", ALL_CATEGORIES, index=ALL_CATEGORIES.index("Other"))
        custom_category = st.text_input("Or type a new category (optional)")
        description = st.text_input("Description (optional)")
        submitted = st.form_submit_button("Add transaction")

    if submitted:
        account_id = options[account_label]
        new_id = tables.run_safely(
            transaction_service.add_transaction, account_id, transaction_type, amount,
            datetime.combine(tx_date, tx_time), custom_category.strip() or category, description)
        if new_id:
            balance = tables.run_safely(balance_service.get_account_balance, account_id, default=0)
            st.success(f"Transaction #{new_id} saved. New account balance: {format_inr(balance)}")


def _edit_tab():
    recent = tables.run_safely(transaction_service.get_transactions, default=[], limit=200)
    if not recent:
        st.info("No transactions yet.")
        return
    st.caption("Showing the 200 most recent transactions.")
    lookup = {f"#{r['transaction_id']} | {r['transaction_date']:%Y-%m-%d} | {r['transaction_type']} | "
              f"₹{float(r['amount']):,.2f} | {r['category']} | {r['account_number']}": r for r in recent}
    selected = lookup[st.selectbox("Choose a transaction", list(lookup), key="tx_edit_select")]
    tid = selected["transaction_id"]

    types = ["DEPOSIT", "WITHDRAWAL"]
    with st.form(f"edit_transaction_form_{tid}"):
        new_type = st.selectbox("Transaction type", types, index=types.index(selected["transaction_type"]),
                                key=f"tx_type_{tid}")
        new_amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0, format="%.2f",
                                     value=float(selected["amount"]), key=f"tx_amount_{tid}")
        new_date = st.date_input("Date", value=selected["transaction_date"].date(), max_value=date.today(),
                                 key=f"tx_date_{tid}")
        new_category = st.text_input("Category", value=selected["category"], key=f"tx_category_{tid}")
        new_description = st.text_input("Description", value=selected["description"] or "",
                                        key=f"tx_description_{tid}")
        update_clicked = st.form_submit_button("Update transaction")
    if update_clicked:
        # keep the original time of day, change only the date
        new_datetime = datetime.combine(new_date, selected["transaction_date"].time())
        if tables.run_safely(transaction_service.update_transaction, tid, new_type, new_amount,
                             new_datetime, new_category, new_description):
            st.success("Transaction updated and balance recalculated.")

    st.divider()
    st.subheader("Delete transaction")
    confirm = st.checkbox("I understand this cannot be undone", key=f"tx_confirm_{tid}")
    if st.button("Delete transaction", disabled=not confirm, key=f"tx_delete_{tid}"):
        if tables.run_safely(transaction_service.delete_transaction, tid):
            st.success("Transaction deleted and balance recalculated. Reload the page to refresh the list.")


def render():
    theme.page_header("💸", "Transactions", "Search, record and correct deposits and withdrawals.")
    view_tab, add_tab, edit_tab = st.tabs(["View / Search / Filter", "Add Transaction", "Edit / Delete"])
    with view_tab:
        _view_tab()
    with add_tab:
        _add_tab()
    with edit_tab:
        _edit_tab()
