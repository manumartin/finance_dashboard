"""AI categorization dialog for transaction categorization."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import openai
import pandas as pd
import streamlit as st

from finanzas.utils.ai import apply_suggestions_to_similar, get_openai_suggestions

if TYPE_CHECKING:
    from finanzas.data.loader import DataLoader

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.propagate = False


def show_ai_categorization_tab(data: DataLoader) -> None:
    """Show the AI categorization tab interface."""
    if not data.has_data():
        st.warning("No data loaded yet. Please import data to get started.")
        return

    # Initialize session state variables
    if "processing" not in st.session_state:
        st.session_state.processing = False
    if "processed_count" not in st.session_state:
        st.session_state.processed_count = 0
    if "total_items" not in st.session_state:
        st.session_state.total_items = len(data.raw_data)

    # Configuration options
    use_existing_only = st.checkbox(
        "Limit suggestions to existing categories",
        value=True,
        help="If checked, AI will only suggest categories and subcategories that already exist in the dataset",
    )

    apply_to_similar = st.checkbox(
        "Apply to identical transactions",
        value=True,
        help="Apply categories to other transactions with the same concept",
    )

    # Process control buttons
    col1, col2 = st.columns([1, 5])
    with col1:
        if not st.session_state.processing:
            if st.button("Start Processing", type="primary"):
                logger.info("Starting AI categorization process")
                st.session_state.processing = True
                st.session_state.processed_count = 0
                st.rerun()
        elif st.button("Stop Processing", type="secondary"):
            logger.info("Stopping AI categorization process")
            st.session_state.processing = False
            st.rerun()

    # Progress tracking
    if st.session_state.processing:
        progress = st.progress(0, text="Starting categorization...")

        batch_size = 20
        grid_df = data.raw_data.copy()
        successful_suggestions = []
        successful_rows = []

        # Get uncategorized transactions (where Category is empty or null)
        uncategorized = grid_df[grid_df["Category"].isna() | (grid_df["Category"] == "")]
        logger.info("Found %d uncategorized transactions", len(uncategorized))

        for i in range(0, len(uncategorized), batch_size):
            if not st.session_state.processing:
                logger.warning("Processing stopped by user")
                st.warning("Processing stopped by user")
                break

            batch = uncategorized.iloc[i : i + batch_size]
            logger.debug("Processing batch %d, size: %d", i // batch_size + 1, len(batch))

            try:
                logger.debug("Existing categories: %s", data.categories)
                logger.debug("Use existing only: %s", use_existing_only)

                suggestions = get_openai_suggestions(
                    batch,
                    data.categories,
                    data.subcategories,
                    use_existing_only=use_existing_only,
                )
                logger.debug("Received suggestions: %s", suggestions)

                # Apply suggestions and track successful ones
                for (idx, row), suggestion in zip(batch.iterrows(), suggestions):
                    logger.debug("Applying suggestion for transaction %s: %s", idx, suggestion)
                    data.raw_data.loc[idx, "Category"] = suggestion["Category"]
                    data.raw_data.loc[idx, "Subcategory"] = suggestion["Subcategory"]

                    # Track successful suggestion and its corresponding row
                    successful_suggestions.append(suggestion)
                    successful_rows.append(row)

                    if apply_to_similar:
                        logger.debug("Applying suggestion to similar transactions with concept: %s", row["Concept"])
                        data.data = apply_suggestions_to_similar(
                            data.raw_data,
                            row["Concept"],
                            suggestion["Category"],
                            suggestion["Subcategory"],
                        )

                # Update progress
                st.session_state.processed_count += len(batch)
                progress_pct = min(st.session_state.processed_count / len(uncategorized), 1.0)
                progress.progress(
                    progress_pct,
                    f"Processed {st.session_state.processed_count} of {len(uncategorized)} transactions...",
                )

            except (openai.OpenAIError, ValueError) as e:
                logger.exception("Error processing batch")
                st.error(f"Error processing batch: {e!s}")
                st.session_state.processing = False
                break

        if st.session_state.processed_count >= len(uncategorized):
            logger.info("AI categorization completed successfully")
            data.update_categories()

            # Show final results with successful suggestions only
            if successful_suggestions and successful_rows:
                show_categorization_results(successful_suggestions, pd.DataFrame(successful_rows))

            st.session_state.processing = False


def show_categorization_results(suggestions: list[dict[str, str]], rows: pd.DataFrame) -> None:
    """Show the results of AI categorization in a grid with feedback."""
    if not suggestions:
        st.error("No categorizations were generated.")
        return

    st.success(f"✅ Successfully categorized {len(suggestions)} transactions!")

    # Create a DataFrame with the original data and suggestions
    results_df = pd.DataFrame(
        {
            "Concept": rows["Concept"].tolist(),
            "Amount": rows["Amount"].tolist(),
            "Suggested Category": [s["Category"] for s in suggestions],
            "Suggested Subcategory": [s["Subcategory"] for s in suggestions],
        },
    )

    # Show the results in a grid
    st.dataframe(
        results_df,
        column_config={
            "Amount": st.column_config.NumberColumn("Amount", format="%.2f €"),
        },
        hide_index=True,
    )
