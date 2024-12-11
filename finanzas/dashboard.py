"""A Streamlit dashboard for personal finance analysis and visualization.

This module provides interactive visualizations and analysis tools for personal financial data,
including expense tracking, income analysis, and balance projections. Features include:
- KPI displays for total income and expenses
- Interactive treemaps for expense and income breakdown
- Balance trend analysis with future projections
- Customizable date range and category filters
"""

from __future__ import annotations

import streamlit as st

from finanzas.data.loader import filter_data, load_dataset
from finanzas.ui.filters import display_sidebar_filters, get_date_range
from finanzas.ui.grid import display_data_grid
from finanzas.ui.kpis import display_date_range_info, display_kpis
from finanzas.ui.treemaps import display_monthly_averages, display_treemaps
from finanzas.ui.trends import display_trend_analysis


def setup_page() -> None:
    """Set up the Streamlit page configuration."""
    st.set_page_config(page_title="Financial Analysis", page_icon="", layout="wide")
    st.title("Financial Dashboard")


def main() -> None:
    """Run the Streamlit app."""
    setup_page()

    # Add file uploader in the sidebar
    st.sidebar.header("Data")
    uploaded_file = st.sidebar.file_uploader(
        "Load dataset (CSV)",
        type="csv",
        help="Upload a CSV file with columns: Date, Concept, Category, Subcategory, Amount, Balance",
    )

    try:
        if uploaded_file is not None:
            data = load_dataset(uploaded_file)
        else:
            # Use default dataset if no file is uploaded
            dataset_path = "./data/fake_dataset.csv"
            data = load_dataset(dataset_path)
    except Exception as e:  # noqa: BLE001
        st.error(
            f"Error loading dataset: {e!s}\n\n"
            "Please ensure the file exists and contains the required columns: "
            "Date, Description, Category, Subcategory, Amount, Balance",
        )
        return

    min_date, max_date = get_date_range(data)
    first_day, last_day, show_hidden = display_sidebar_filters(min_date, max_date)

    filtered_df = filter_data(data, first_day, last_day, show_hidden=show_hidden)
    display_date_range_info(first_day, last_day)

    # Display KPIs above the tabs
    display_kpis(filtered_df)

    # Create tabs for different visualizations
    tab1, tab2, tab3, tab4 = st.tabs(["Income and Expense Breakdown", "Monthly Averages", "Trend Analysis", "Data"])

    with tab1:
        display_treemaps(filtered_df)

    with tab2:
        display_monthly_averages(filtered_df)

    with tab3:
        display_trend_analysis(filtered_df)

    with tab4:
        display_data_grid(filtered_df)


if __name__ == "__main__":
    main()
