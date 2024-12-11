"""UI components for displaying KPIs."""
from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from finanzas.utils.calculations import calculate_kpis, format_date_range


def display_kpis(filtered_df: pd.DataFrame) -> None:
    """Calculate and display key performance indicators."""
    total_expenses, total_income = calculate_kpis(filtered_df)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Expenses", f"{abs(total_expenses):,.2f}€")
    with col2:
        st.metric("Total Income", f"{total_income:,.2f}€")


def display_date_range_info(first_day: date, last_day: date) -> None:
    """Display the current date range in a user-friendly format."""
    st.caption(f"Showing data from {format_date_range(first_day, last_day)}") 