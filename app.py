"""Single Streamlit entry point for both partner dashboard experiences."""

import streamlit as st

from shared.routing import DASHBOARDS, resolve_dashboard


try:
    dashboard = resolve_dashboard(st.query_params.get("dashboard"))
except ValueError as exc:
    st.set_page_config(page_title="Merchant Dashboard", layout="wide")
    st.error(str(exc))
    st.stop()

# Register only the selected dashboard. Streamlit executes the page on every rerun,
# with native page/widget isolation and without importing both UIs at startup.
# Hidden navigation keeps the existing iframe layout free of additional menus.
script, title = DASHBOARDS[dashboard]
page = st.Page(script, title=title, default=True)
st.navigation([page], position="hidden").run()
