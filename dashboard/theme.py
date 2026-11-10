"""Theme helpers: loads the custom CSS and renders small HTML components."""
from html import escape
from pathlib import Path

import streamlit as st

CSS_FILE = Path(__file__).resolve().parent / "assets" / "style.css"


def apply_theme():
    """Inject the custom stylesheet and the sidebar brand block. Call once in app.py."""
    try:
        css = CSS_FILE.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except OSError:
        pass  # the app still works with Streamlit's default look
    st.sidebar.markdown(
        '<div class="brand"><div class="brand-logo">🏦</div>'
        '<div><div class="brand-name">BankLens</div>'
        '<div class="brand-tag">Transaction Analysis</div></div></div>',
        unsafe_allow_html=True,
    )


def page_header(icon, title, subtitle=""):
    """Gradient hero banner shown at the top of every page."""
    sub = f'<p class="hero-sub">{escape(subtitle)}</p>' if subtitle else ""
    st.markdown(
        f'<div class="hero"><h1 class="hero-title"><span>{icon}</span>{escape(title)}</h1>{sub}</div>',
        unsafe_allow_html=True,
    )


def section_title(icon, text):
    st.markdown(f'<div class="section-title"><span>{icon}</span>{escape(text)}</div>', unsafe_allow_html=True)


def kpi_card(label, value, icon="💰", tone="teal", note=""):
    """HTML KPI card. tone: teal | green | red | blue | amber."""
    note_html = f'<div class="kpi-note">{escape(note)}</div>' if note else ""
    st.markdown(
        f'<div class="kpi {escape(tone)}"><div class="kpi-top">'
        f'<span class="kpi-label">{escape(str(label))}</span><span class="kpi-icon">{icon}</span></div>'
        f'<div class="kpi-value">{escape(str(value))}</div>{note_html}</div>',
        unsafe_allow_html=True,
    )
