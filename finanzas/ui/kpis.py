"""UI components for displaying KPIs."""

from __future__ import annotations

from typing import TYPE_CHECKING

import streamlit as st

from finanzas.utils.formatting import format_date_range

if TYPE_CHECKING:
    from datetime import date

    from finanzas.data.loader import DataLoader


def display_kpis(data: DataLoader) -> None:
    """Calculate and display key performance indicators."""
    total_expenses, total_income = data.calculate_kpis()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Expenses", f"{abs(total_expenses):,.2f}€")
    with col2:
        st.metric("Total Income", f"{total_income:,.2f}€")


def display_date_range_info(first_day: date, last_day: date) -> None:
    """Display the current date range in a user-friendly format."""
    st.caption(f"Showing data from {format_date_range(first_day, last_day)}")
