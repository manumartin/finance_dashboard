"""UI components for data grid and AI suggestions."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from finanzas.utils.ai import get_openai_suggestions, apply_suggestions_to_similar


def display_data_grid(df: pd.DataFrame) -> None:
    """Display the dataset in a grid format with the ability to hide entries and search."""
    # Add a search box
    search_term = st.text_input("Search", value="", help="Search for entries by concept, category, or subcategory")

    # Create a copy for display but maintain index relationship
    grid_df = df.copy()

    # Add selection column if it doesn't exist
    if "Selected" not in grid_df.columns:
        grid_df["Selected"] = False

    # Filter the DataFrame based on the search term
    if search_term:
        grid_df = grid_df[
            grid_df["Concept"].str.contains(search_term, case=False, na=False)
            | grid_df["Category"].str.contains(search_term, case=False, na=False)
            | grid_df["Subcategory"].str.contains(search_term, case=False, na=False)
        ]

    # Show count summary
    total_items = len(df)
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
                options=sorted(df["Category"].unique()),
                required=True,
            ),
            "Subcategory": st.column_config.SelectboxColumn(
                "Subcategory",
                options=sorted(df["Subcategory"].unique()),
                required=True,
            ),
            "Hidden": st.column_config.CheckboxColumn("Hidden"),
            "Selected": st.column_config.CheckboxColumn("Select"),
        },
        disabled=["Date", "Amount", "Balance"],
    )

    # Get selected rows
    selected_rows = edited_df[edited_df["Selected"]].index.tolist()

    # Update the session state data with the edited values
    if edited_df is not None and not edited_df.empty:
        st.session_state.data.loc[edited_df.index, "Hidden"] = edited_df["Hidden"]
        st.session_state.data.loc[edited_df.index, "Category"] = edited_df["Category"]
        st.session_state.data.loc[edited_df.index, "Subcategory"] = edited_df["Subcategory"]

    display_ai_suggestions_section(grid_df, selected_rows)


def display_ai_suggestions_section(grid_df: pd.DataFrame, selected_rows: list[int]) -> None:
    """Display and handle AI suggestions for categorization."""
    with st.container():
        st.markdown("---")  # Add a visual separator
        st.subheader("AI Category Suggestions")

        # Initialize session state for suggestions view
        if "showing_suggestions" not in st.session_state:
            st.session_state.showing_suggestions = False
        if "current_suggestions" not in st.session_state:
            st.session_state.current_suggestions = None

        col1, col2 = st.columns([3, 1])

        with col1:
            use_existing_only = st.checkbox(
                "Limit suggestions to existing categories",
                value=True,
                help="If checked, AI will only suggest categories and subcategories that already exist in the dataset",
            )

        with col2:
            if not st.session_state.showing_suggestions:
                if st.button("Get AI Suggestions for Selected", type="primary", disabled=not selected_rows):
                    selected_df = grid_df.iloc[selected_rows]

                    if len(selected_df) == 0:
                        st.warning("Please select at least one row to get suggestions")
                    else:
                        with st.spinner("Getting AI suggestions..."):
                            try:
                                suggestions = get_openai_suggestions(
                                    selected_df,
                                    set(grid_df["Category"].unique()),
                                    st.session_state.subcategories,
                                    use_existing_only=use_existing_only,
                                )
                                if suggestions:
                                    st.session_state.showing_suggestions = True
                                    st.session_state.current_suggestions = {
                                        "selected_df": selected_df,
                                        "suggestions": suggestions,
                                    }
                                    st.rerun()
                                else:
                                    st.warning("No suggestions received from AI")

                            except Exception as e:
                                st.error(f"Error getting suggestions: {str(e)}")

        _handle_suggestions_preview()


def _handle_suggestions_preview() -> None:
    """Handle the preview and application of AI suggestions."""
    if st.session_state.showing_suggestions and st.session_state.current_suggestions:
        selected_df = st.session_state.current_suggestions["selected_df"]
        suggestions = st.session_state.current_suggestions["suggestions"]

        # Create a preview of changes
        changes_preview = []
        for row, suggestion in zip(selected_df.itertuples(), suggestions):
            changes_preview.append(
                {
                    "Concept": row.Concept,
                    "Current Category": row.Category,
                    "Current Subcategory": row.Subcategory,
                    "Suggested Category": suggestion["Category"],
                    "Suggested Subcategory": suggestion["Subcategory"],
                }
            )

        preview_df = pd.DataFrame(changes_preview)
        st.write("Preview of suggested changes:")
        st.dataframe(preview_df, use_container_width=True)

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            apply_to_similar = st.checkbox(
                "Apply to identical transactions",
                value=True,
                help="Apply these categories to other transactions with the same concept",
            )

        with col2:
            if st.button("Apply Changes", type="primary"):
                # Apply changes to selected rows
                for row, suggestion in zip(selected_df.itertuples(), suggestions):
                    st.session_state.data.loc[row.Index, "Category"] = suggestion["Category"]
                    st.session_state.data.loc[row.Index, "Subcategory"] = suggestion["Subcategory"]

                    if apply_to_similar:
                        st.session_state.data = apply_suggestions_to_similar(
                            st.session_state.data,
                            row.Concept,
                            suggestion["Category"],
                            suggestion["Subcategory"],
                        )

                st.session_state.showing_suggestions = False
                st.session_state.current_suggestions = None
                st.success("Changes applied successfully!")
                st.rerun()

        with col3:
            if st.button("Cancel", type="secondary"):
                st.session_state.showing_suggestions = False
                st.session_state.current_suggestions = None
                st.rerun() 