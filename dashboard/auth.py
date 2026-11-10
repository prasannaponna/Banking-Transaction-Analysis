"""Demo authentication helpers for the Banking Transaction Analysis app.

The project intentionally has no production authentication. This module keeps
the small session-based demo gate in one place so the landing page, the login
portal and the dashboard all use the same credentials.
"""
from __future__ import annotations

import hmac

import streamlit as st

DEMO_USERS = {
    "admin": {"password": "admin@123", "role": "Admin"},
    "member1": {"password": "backend", "role": "Member 1 - Backend"},
    "member2": {"password": "database", "role": "Member 2 - Database"},
    "member3": {"password": "analysis", "role": "Member 3 - Data Analysis"},
    "member4": {"password": "dashboard", "role": "Member 4 - Dashboard"},
    "viewer": {"password": "viewer", "role": "Viewer"},
}

PUBLIC_PAGE_CSS = """
<style>
section[data-testid="stSidebar"] { display: none; }
[data-testid="collapsedControl"] { display: none; }
.block-container { padding-top: 1.4rem; }
</style>
"""


def is_authenticated() -> bool:
    """Return True when a demo user has signed in for this session."""
    return bool(st.session_state.get("authenticated"))


def current_user() -> dict:
    return st.session_state.get("user", {})


def logout() -> None:
    for key in ("authenticated", "user", "login_error"):
        st.session_state.pop(key, None)


def attempt_login(username: str, password: str, selected_role: str = "") -> bool:
    """Validate a demo account and start an authenticated session."""
    user = DEMO_USERS.get(username.strip().lower())
    if not user or not hmac.compare_digest(user["password"], password):
        return False
    st.session_state.authenticated = True
    st.session_state.user = {
        "username": username.strip().lower(),
        "role": selected_role or user["role"],
        "account_role": user["role"],
    }
    return True
