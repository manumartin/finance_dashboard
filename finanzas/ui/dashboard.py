"""Dashboard page."""

from __future__ import annotations

import streamlit as st

from finanzas.ui.kpis import display_date_range_info, display_kpis
from finanzas.ui.sidebar import display_sidebar_filters
from finanzas.ui.treemaps import display_monthly_averages, display_treemaps
from finanzas.ui.trends import display_trend_analysis
from run_dashboard import PAGES


def dashboard_page() -> None:
    """Display the main financial dashboard with KPIs, charts, and analysis."""
    data_loader = st.session_state.data_loader

    st.title("Financial Dashboard")

    if not data_loader.has_data():
        st.warning("No data loaded yet. Please import data to get started.")
        st.page_link(PAGES["Dataset"], label="Import Data", icon="📥")
        st.stop()

    min_date, max_date = data_loader.get_date_range()
    first_day, last_day, show_hidden = display_sidebar_filters(min_date, max_date)

    data_loader.filter_data(
        first_day,
        last_day,
        show_hidden=show_hidden,
    )
    display_date_range_info(first_day, last_day)

    display_kpis(data_loader)

    tab1, tab2, tab3 = st.tabs(["Income and Expense Breakdown", "Monthly Averages", "Trend Analysis"])

    with tab1:
        display_treemaps(data_loader)

    with tab2:
        display_monthly_averages(data_loader)

    with tab3:
        display_trend_analysis(data_loader)


dashboard_page()
