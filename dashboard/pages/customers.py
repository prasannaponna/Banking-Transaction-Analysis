"""Customer management page (MEMBER 4)."""
import streamlit as st

from backend import customer_service
from dashboard import theme
from dashboard.components import tables


def _customer_label(customer):
    return f"#{customer['customer_id']} - {customer['name']} ({customer['phone']})"


def render():
    theme.page_header("👥", "Customers", "Add, search and manage customer records.")
    view_tab, add_tab, edit_tab = st.tabs(["View / Search", "Add Customer", "Edit / Delete"])

    with view_tab:
        keyword = st.text_input("Search by name, phone, email or ID", key="customer_search")
        if keyword.strip():
            records = tables.run_safely(customer_service.search_customers, keyword, default=[])
        else:
            records = tables.run_safely(customer_service.get_all_customers, default=[])
        st.write(f"{len(records)} customer(s) found")
        tables.show_table(tables.records_to_df(records))

    with add_tab:
        with st.form("add_customer_form", clear_on_submit=True):
            name = st.text_input("Full name")
            phone = st.text_input("Phone (10 digits)")
            email = st.text_input("Email")
            address = st.text_input("Address (optional)")
            submitted = st.form_submit_button("Add customer")
        if submitted:
            new_id = tables.run_safely(customer_service.create_customer, name, phone, email, address)
            if new_id:
                st.success(f"Customer added with ID {new_id}.")

    with edit_tab:
        customers = tables.run_safely(customer_service.get_all_customers, default=[])
        if not customers:
            st.info("No customers yet.")
            return
        lookup = {_customer_label(c): c for c in customers}
        selected = lookup[st.selectbox("Choose a customer", list(lookup), key="customer_edit_select")]
        cid = selected["customer_id"]

        with st.form(f"edit_customer_form_{cid}"):
            name = st.text_input("Full name", value=selected["name"], key=f"cust_name_{cid}")
            phone = st.text_input("Phone", value=selected["phone"], key=f"cust_phone_{cid}")
            email = st.text_input("Email", value=selected["email"], key=f"cust_email_{cid}")
            address = st.text_input("Address", value=selected["address"] or "", key=f"cust_address_{cid}")
            update_clicked = st.form_submit_button("Update customer")
        if update_clicked:
            if tables.run_safely(customer_service.update_customer, cid, name, phone, email, address):
                st.success("Customer updated. Reload the list to see the change.")

        st.divider()
        st.subheader("Delete customer")
        st.caption("A customer who still has accounts cannot be deleted.")
        confirm = st.checkbox("I understand this cannot be undone", key=f"cust_confirm_{cid}")
        if st.button("Delete customer", disabled=not confirm, key=f"cust_delete_{cid}"):
            if tables.run_safely(customer_service.delete_customer, cid):
                st.success("Customer deleted. Reload the page to refresh the list.")
