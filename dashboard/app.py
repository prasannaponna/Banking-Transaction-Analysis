"""
Streamlit entry point (MEMBER 4).   Run from the project root with:

    streamlit run dashboard/app.py

The public landing page is shown first. Its login button opens a separate demo
login portal; after sign-in the regular six-page dashboard is shown.
"""
import sys
from pathlib import Path

# Make the project root importable (backend, analysis, utils, dashboard)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st  # noqa: E402

st.set_page_config(page_title="Banking Transaction Analysis", page_icon="🏦", layout="wide")

from backend.db_connection import check_connection  # noqa: E402
from dashboard import landing, login  # noqa: E402
from dashboard.auth import current_user, is_authenticated, logout  # noqa: E402
from dashboard.theme import apply_theme  # noqa: E402
from dashboard.pages import accounts, analysis, customers, dashboard, reports, transactions  # noqa: E402

apply_theme()

# ---------------------------------------------------------------------------
# Public area: landing page + separate login portal
# ---------------------------------------------------------------------------
if not is_authenticated():
    public_page = st.query_params.get("page", "home")
    if public_page == "login":
        login.render()
    else:
        landing.render()
    st.stop()

# ---------------------------------------------------------------------------
# Authenticated dashboard
# ---------------------------------------------------------------------------
if not check_connection():
    st.error("Could not connect to the database. Make sure MySQL is running, the banking_db database "
             "is created (see database/README.md) and the .env file has the correct settings.")
    st.stop()

user = current_user()
with st.sidebar:
    st.markdown(
        f'<div class="session-user"><strong>{user.get("username", "user")}</strong>'
        f'<span>{user.get("role", "Viewer")}</span></div>',
        unsafe_allow_html=True,
    )
    if st.button("Log out", use_container_width=True):
        logout()
        st.query_params.clear()
        st.rerun()

navigation = st.navigation([
    st.Page(dashboard.render, title="Dashboard", icon="📊", url_path="dashboard", default=True),
    st.Page(customers.render, title="Customers", icon="👥", url_path="customers"),
    st.Page(accounts.render, title="Accounts", icon="🏦", url_path="accounts"),
    st.Page(transactions.render, title="Transactions", icon="💸", url_path="transactions"),
    st.Page(analysis.render, title="Analysis", icon="📈", url_path="analysis"),
    st.Page(reports.render, title="Reports", icon="📄", url_path="reports"),
])
st.sidebar.caption("College demo project - not production banking software.")
navigation.run()
