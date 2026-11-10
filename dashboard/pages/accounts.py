"""Account management page (MEMBER 4)."""
import pandas as pd
import streamlit as st

from backend import account_service, customer_service
from dashboard import theme
from dashboard.components import tables
from utils.helpers import format_inr
from utils.validators import VALID_ACCOUNT_TYPES


def render():
    theme.page_header("🏦", "Accounts", "Open, update, deactivate or delete customer accounts.")
    view_tab, open_tab, manage_tab, recycle_tab = st.tabs(
        ["View / Search", "Open Account", "Update / Deactivate", "Recently Deleted"]
    )

    with view_tab:
        keyword = st.text_input("Search by account number, customer name, type or status", key="account_search")
        status = st.selectbox("Status", ["All", "ACTIVE", "INACTIVE"], key="account_status_filter")
        if keyword.strip():
            records = tables.run_safely(account_service.search_accounts, keyword, default=[])
        else:
            records = tables.run_safely(account_service.get_all_accounts, default=[])
        if status != "All":
            records = [r for r in records if r["status"] == status]
        st.write(f"{len(records)} account(s) found")
        tables.show_table(tables.records_to_df(records))

    with open_tab:
        customers = tables.run_safely(customer_service.get_all_customers, default=[])
        if not customers:
            st.info("Add a customer first.")
        else:
            lookup = {f"#{c['customer_id']} - {c['name']}": c["customer_id"] for c in customers}
            with st.form("open_account_form", clear_on_submit=True):
                customer_label = st.selectbox("Customer", list(lookup))
                account_type = st.selectbox("Account type", list(VALID_ACCOUNT_TYPES))
                opening_balance = st.number_input("Opening balance (₹)", min_value=0.0, step=500.0, format="%.2f")
                account_number = st.text_input("Account number (leave empty to generate automatically)")
                submitted = st.form_submit_button("Open account")
            if submitted:
                new_id = tables.run_safely(account_service.create_account, lookup[customer_label], account_type,
                                           opening_balance, account_number.strip() or None)
                if new_id:
                    st.success(f"Account opened with ID {new_id}.")

    with manage_tab:
        options = tables.account_options()
        if not options:
            st.info("No accounts yet.")
            return
        label = st.selectbox("Choose an account", list(options), key="account_manage_select")
        account_id = options[label]
        account = tables.run_safely(account_service.get_account, account_id)
        if not account:
            return
        st.write(f"**Balance:** {format_inr(account['balance'])}  |  **Status:** {account['status']}")

        with st.form(f"update_account_form_{account_id}"):
            types = list(VALID_ACCOUNT_TYPES)
            new_type = st.selectbox("Account type", types, index=types.index(account["account_type"]))
            update_clicked = st.form_submit_button("Update account type")
        if update_clicked and tables.run_safely(account_service.update_account, account_id, account_type=new_type):
            st.success("Account updated.")

        if account["status"] == "ACTIVE":
            if st.button("Deactivate account", key=f"deactivate_{account_id}"):
                if tables.run_safely(account_service.deactivate_account, account_id):
                    st.success("Account deactivated. Its history is kept.")
        else:
            if st.button("Activate account", key=f"activate_{account_id}"):
                if tables.run_safely(account_service.activate_account, account_id):
                    st.success("Account activated.")

        st.divider()
        with st.expander("Delete account permanently", icon="⚠️"):
            tx_count = tables.run_safely(account_service.count_transactions, account_id, default=0)
            st.warning(
                "The account and its transactions are moved to the **Recently Deleted** tab "
                "first, so you can restore them. Nothing is lost unless you delete it there "
                "permanently. Deactivate the account instead if you only want to stop using it."
            )
            if tx_count:
                st.write(f"This account has **{tx_count}** transaction(s).")
                delete_history = st.checkbox(
                    f"Also delete all {tx_count} transaction(s)",
                    key=f"delete_tx_{account_id}",
                    help="Required: MySQL will not delete an account that still has transactions.",
                )
            else:
                delete_history = True
                st.write("This account has no transactions.")

            confirmed = st.checkbox(
                "I understand this cannot be undone",
                key=f"confirm_delete_{account_id}",
            )
            if st.button(
                "Delete account permanently",
                key=f"delete_{account_id}",
                type="primary",
                disabled=not confirmed,
            ):
                if tables.run_safely(account_service.delete_account, account_id, delete_history):
                    st.success("Account moved to Recently Deleted. You can restore it from there.")
                    st.rerun()

    with recycle_tab:
        deleted = tables.run_safely(account_service.get_deleted_accounts, default=[])
        if not deleted:
            st.info(
                "No deleted accounts. When you delete an account it is kept here with its "
                "transactions, so you can restore it if you change your mind."
            )
        else:
            st.caption(
                "Deleted accounts are kept here together with their transactions. "
                "**Restore** brings the account back with its full history; "
                "**Delete permanently** removes it for good."
            )
            display = pd.DataFrame([
                {
                    "Bin ID": row["id"],
                    "Account number": row["account_number"],
                    "Customer": row["customer_name"],
                    "Type": row["account_type"],
                    "Balance": float(row["balance"]),
                    "Transactions": row["transaction_count"],
                    "Deleted at": row["deleted_at"],
                    "Status": "Restored" if row["restored_at"] else "In recycle bin",
                }
                for row in deleted
            ])
            tables.show_table(display, money_columns=["Balance"])

            pending = [row for row in deleted if row["restored_at"] is None]
            if not pending:
                st.info("Every deleted account has been restored or permanently deleted.")
            else:
                lookup = {
                    f"Bin #{row['id']} - {row['account_number']} - {row['customer_name']} "
                    f"({row['transaction_count']} transactions)": row["id"]
                    for row in pending
                }
                choice = st.selectbox(
                    "Choose a deleted account", list(lookup), key="recycle_select"
                )
                archive_id = lookup[choice]

                restore_col, purge_col = st.columns(2)
                with restore_col:
                    if st.button("Restore account", key=f"restore_{archive_id}", type="primary"):
                        new_id = tables.run_safely(account_service.restore_account, archive_id)
                        if new_id:
                            st.success(f"Account restored with ID {new_id} and all its transactions.")
                            st.rerun()
                with purge_col:
                    confirmed = st.checkbox(
                        "I understand this cannot be undone",
                        key=f"confirm_purge_{archive_id}",
                    )
                    if st.button(
                        "Delete permanently",
                        key=f"purge_{archive_id}",
                        disabled=not confirmed,
                    ):
                        if tables.run_safely(account_service.purge_deleted_account, archive_id):
                            st.success("Deleted permanently.")
                            st.rerun()
