"""UI components for data grid and AI suggestions."""

from __future__ import annotations

from typing import TYPE_CHECKING

import streamlit as st

from finanzas.ui.ai_categorization import show_ai_categorization_tab
from finanzas.ui.import_data import import_data_page

if TYPE_CHECKING:
    from finanzas.data.loader import DataLoader


def dataset_page() -> None:
    """Display the dataset in a grid format with tabs for data view and AI categorization."""
    st.title("Data Management")

    data: DataLoader = st.session_state.data_loader

    tab_dataset, tab_import, tab_ai = st.tabs(["Data", "Import Data", "AI Categorization"])

    with tab_dataset:
        show_dataset_tab(data)

    with tab_import:
        show_import_data_tab(data)

    with tab_ai:
        show_ai_categorization_tab(data)


def show_import_data_tab(data: DataLoader) -> None:
    """Display the import data tab."""
    import_data_page(data)


def show_dataset_tab(data: DataLoader) -> None:
    """Display the dataset view tab with search and grid functionality."""
    if not data.has_data():
        st.warning("No data loaded yet. Please import data to get started.")
        return

    # Add a search box
    search_term = st.text_input("Search", value="", help="Search for entries by concept, category, or subcategory")

    grid_df = data.raw_data.copy()

    # Filter the DataFrame based on the search term
    if search_term:
        grid_df = grid_df[
            grid_df["Concept"].str.contains(search_term, case=False, na=False)
            | grid_df["Category"].str.contains(search_term, case=False, na=False)
            | grid_df["Subcategory"].str.contains(search_term, case=False, na=False)
        ]

    # Show count summary
    total_items = len(data.raw_data)
    filtered_items = len(grid_df)
    st.caption(f"Showing {filtered_items} of {total_items} items")

    # Display the grid with fixed headers and column configurations
    edited_df = st.data_editor(
        grid_df,
        use_container_width=True,
        height=400,
        column_config={
            "Date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
            "Amount": st.column_config.NumberColumn("Amount", format="%.2f €"),
            "Balance": st.column_config.NumberColumn("Balance", format="%.2f €"),
            "Category": st.column_config.SelectboxColumn(
                "Category",
                options=sorted(data.raw_data["Category"].unique()),
                required=True,
            ),
            "Subcategory": st.column_config.SelectboxColumn(
                "Subcategory",
                options=sorted(data.raw_data["Subcategory"].unique()),
                required=True,
            ),
        },
        disabled=["Date", "Amount", "Balance"],
    )

    # Update the session state data with the edited values
    if edited_df is not None and not edited_df.empty:
        data.raw_data.loc[edited_df.index, "Category"] = edited_df["Category"]
        data.raw_data.loc[edited_df.index, "Subcategory"] = edited_df["Subcategory"]


dataset_page()
