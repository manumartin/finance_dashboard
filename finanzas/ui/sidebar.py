"""UI components for the sidebar, including data loading and filtering."""

from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, timezone

import pandas as pd
import streamlit as st


def display_sidebar_filters(
    min_date: date,
    max_date: date,
) -> tuple[date, date, bool]:
    """Create sidebar filters and return selected options."""
    st.sidebar.header("Filters")

    if min_date > max_date:
        min_date, max_date = max_date, min_date
    month_labels = [d.strftime("%B %Y").capitalize() for d in pd.date_range(start=min_date, end=max_date, freq="MS")]

    selected_month_range = st.sidebar.select_slider(
        "Select Month Range",
        options=range(len(month_labels)),
        value=(0, len(month_labels) - 1),
        format_func=lambda x: month_labels[x],
    )

    months = pd.to_datetime(month_labels, format="%B %Y")
    first_day = datetime(
        months[selected_month_range[0]].year,
        months[selected_month_range[0]].month,
        1,
        tzinfo=timezone.utc,
    ).date()
    last_day = min(
        datetime(
            months[selected_month_range[1]].year,
            months[selected_month_range[1]].month,
            monthrange(
                months[selected_month_range[1]].year,
                months[selected_month_range[1]].month,
            )[1],
            tzinfo=timezone.utc,
        ).date(),
        max_date,
    )

    # Add a checkbox to show/hide hidden entries
    show_hidden = st.sidebar.checkbox("Show Hidden Entries", value=False)

    return first_day, last_day, show_hidden
