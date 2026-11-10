"""Report page: preview and CSV download (MEMBER 4)."""
import streamlit as st

from analysis.report_generator import REPORT_NAMES, build_report, report_file_name, to_csv_bytes
from analysis.transaction_analysis import load_transactions
from dashboard import theme
from dashboard.components import tables


def render():
    theme.page_header("📄", "Reports", "Preview reports and download them as CSV.")
    st.sidebar.header("Report filters")
    filters = tables.transaction_filters(st.sidebar, "rep")
    settings = tables.unusual_settings(st.sidebar, "rep")

    report_name = st.selectbox("Choose a report", REPORT_NAMES)
    df = tables.run_safely(load_transactions, default=None, **filters)
    if df is None:
        return

    report = build_report(report_name, df, **settings)
    st.write(f"**{report_name}** - {len(report)} row(s)")
    tables.show_table(report)

    st.download_button("⬇️ Download CSV", data=to_csv_bytes(report), file_name=report_file_name(report_name),
                       mime="text/csv", disabled=report.empty)
