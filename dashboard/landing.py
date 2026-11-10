"""Public landing page shown before the demo login portal."""
from __future__ import annotations

from html import escape

import streamlit as st

from dashboard.auth import PUBLIC_PAGE_CSS

FEATURES = [
    ("👥", "Customer management", "Create, read, update, search and delete/deactivate customers with validation for name, phone and email."),
    ("🏦", "Account management", "Open savings or current accounts, set an opening balance, search, update and activate/deactivate accounts safely."),
    ("💸", "Transaction engine", "Record deposits and withdrawals, edit or delete entries, and search/filter the complete transaction history."),
    ("🛡️", "Balance integrity", "Deposits and withdrawals update the stored balance in one database transaction; insufficient-balance withdrawals are rejected."),
    ("📊", "Data analysis", "Totals, average, largest transaction, descriptive statistics, monthly income/expense, category spending and per-account totals."),
    ("🚨", "Unusual transactions", "Three configurable rules: high relative amount, high absolute amount and rapid transaction frequency. Rule-based, not fraud detection."),
    ("📈", "Interactive dashboard", "Six Streamlit pages with KPI cards, Plotly charts, recent transactions, alerts and sidebar filters for account, date, type and category."),
    ("📄", "CSV reports", "Preview and download transaction, monthly spending, category spending and unusual transaction reports."),
]

ANALYSIS_POINTS = [
    ("🧮", "Core metrics", "Totals, average, largest transaction, descriptive statistics and balance from deposits minus withdrawals."),
    ("📅", "Monthly analysis", "Monthly income, monthly expenses and net cash flow, including months with only deposits or only withdrawals."),
    ("🏷️", "Category spending", "Category-wise expenses, top categories, income vs expense and per-account income/expense totals."),
    ("🚨", "Unusual rules", "Z-score above normal, amount at or above a configured limit, and too many transactions in a short window."),
    ("📄", "Report tables", "Stable DataFrames for transaction, monthly spending, category spending and unusual transaction reports."),
    ("📥", "CSV export", "UTF-8 BOM encoding so Excel displays the rupee symbol correctly."),
]


def _stats_html() -> str:
    stats = [
        ("3", "Database tables"),
        ("6", "Dashboard pages"),
        ("4", "CSV report types"),
        ("38", "Automated tests"),
    ]
    cells = "".join(
        f'<div class="lp-stat"><div class="lp-stat-num">{value}</div>'
        f'<div class="lp-stat-label">{label}</div></div>'
        for value, label in stats
    )
    return f'<div class="lp-stats">{cells}</div>'


def _feature_card(icon: str, title: str, text: str) -> str:
    return (
        f'<div class="lp-card"><div class="lp-card-icon">{icon}</div>'
        f'<h3>{escape(title)}</h3><p>{escape(text)}</p></div>'
    )


def render() -> None:
    """Render the public landing page with a button to the separate login portal."""
    st.markdown(PUBLIC_PAGE_CSS, unsafe_allow_html=True)

    with st.container(key="lp-hero-box"):
        st.markdown(
            '<h1 class="lp-title">Banking Transaction<br><span>Analysis System</span></h1>',
            unsafe_allow_html=True,
        )
        if st.button("Open login portal →", type="primary", key="landing_login"):
            st.query_params["page"] = "login"
            st.rerun()

    st.markdown(_stats_html(), unsafe_allow_html=True)

    st.markdown('<div id="features"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="lp-section-head"><div class="lp-kicker">All features</div>'
        '<h2>Everything the application can do</h2>'
        '<p>From customer onboarding to CSV reports, the project covers the complete small-banking workflow and the analytics on top of it.</p></div>',
        unsafe_allow_html=True,
    )
    for start in range(0, len(FEATURES), 3):
        cols = st.columns(3, gap="medium")
        for col, (icon, title, text) in zip(cols, FEATURES[start:start + 3]):
            with col:
                st.markdown(_feature_card(icon, title, text), unsafe_allow_html=True)

    st.markdown(
        '<div class="lp-section-head"><div class="lp-kicker">Analysis and reporting</div>'
        '<h2>Turn raw transactions into useful answers</h2>'
        '<p>The analysis layer works on DataFrames, so every metric can be tested without a database and reused by every page.</p></div>',
        unsafe_allow_html=True,
    )
    for start in range(0, len(ANALYSIS_POINTS), 3):
        cols = st.columns(3, gap="medium")
        for col, (icon, title, text) in zip(cols, ANALYSIS_POINTS[start:start + 3]):
            with col:
                st.markdown(_feature_card(icon, title, text), unsafe_allow_html=True)

    st.markdown(
        '<div class="lp-bottom-cta">'
        '<div class="lp-kicker">Ready to continue?</div>'
        '<h2>Open the dashboard</h2>'
        '<p>Use the separate login portal to start a demo session.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    b1, b2, b3 = st.columns([1, 0.9, 1])
    with b2:
        if st.button("Open login portal →", type="primary", use_container_width=True, key="landing_login_bottom"):
            st.query_params["page"] = "login"
            st.rerun()

    st.markdown(
        '<div class="lp-footer">BankLens · Banking Transaction Analysis System · 2026 · '
        'Python · MySQL · Pandas · Plotly · Streamlit</div>',
        unsafe_allow_html=True,
    )
