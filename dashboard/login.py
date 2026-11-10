"""Separate demo login portal for the Banking Transaction Analysis app."""
from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from dashboard.auth import PUBLIC_PAGE_CSS, attempt_login


def _tame_password_manager() -> None:
    """Stop browsers from offering to generate a new strong password on login."""
    components.html(
        """
        <script>
        (function () {
          const doc = window.parent.document;
          function apply() {
            doc.querySelectorAll('input[type="password"]').forEach(function (el) {
              el.setAttribute('autocomplete', 'current-password');
              el.setAttribute('name', 'password');
            });
            doc.querySelectorAll('input[type="text"][aria-label="Username"]').forEach(function (el) {
              el.setAttribute('autocomplete', 'username');
              el.setAttribute('name', 'username');
            });
          }
          apply();
          setTimeout(apply, 300);
          setTimeout(apply, 1200);
        })();
        </script>
        """,
        height=0,
        width=0,
    )


def render() -> None:
    """Render a plain username/password login page."""
    st.markdown(PUBLIC_PAGE_CSS, unsafe_allow_html=True)

    if st.button("← Back to landing page", key="back_to_landing"):
        st.query_params["page"] = "home"
        st.rerun()

    left, center, right = st.columns([1, 1.1, 1])
    with center:
        st.markdown('<div class="lp-login-title">Login</div>', unsafe_allow_html=True)
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", use_container_width=True)

        if submitted:
            if attempt_login(username, password):
                st.query_params.clear()
                st.rerun()
            else:
                st.error("Invalid username or password.")

    _tame_password_manager()
