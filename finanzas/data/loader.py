"""Data loading and preprocessing functionality."""
from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st


def load_dataset(path: str | st.runtime.uploaded_file_manager.UploadedFile) -> pd.DataFrame:
    """Load and preprocess the financial dataset from a CSV file or uploaded file."""
    # Reset data if a new file is uploaded
    if isinstance(path, st.runtime.uploaded_file_manager.UploadedFile):
        if "previous_file" not in st.session_state or st.session_state.previous_file != path.name:
            st.session_state.data = None
            st.session_state.previous_file = path.name
            # Reset categories and subcategories
            st.session_state.categories = set()
            st.session_state.subcategories = {}

    # Initialize the data in session state if it doesn't exist
    if "data" not in st.session_state or st.session_state.data is None:
        data = pd.read_csv(path)
        data["Date"] = pd.to_datetime(data["Date"])
        data["Balance"] = data["Balance"].astype(float)
        data["Amount"] = data["Amount"].astype(float)
        # Add a "Hidden" column initialized to False
        if "Hidden" not in data.columns:
            data["Hidden"] = False
        st.session_state.data = data

        # Initialize categories and subcategories from the data
        st.session_state.categories = set(data["Category"].unique())
        st.session_state.subcategories = {
            category: set(data[data["Category"] == category]["Subcategory"].unique())
            for category in st.session_state.categories
        }

    return st.session_state.data


def filter_data(df: pd.DataFrame, first_day: date, last_day: date, *, show_hidden: bool) -> pd.DataFrame:
    """Filter dataset by date range and hidden status."""
    filtered_df = df[(df["Date"] >= pd.Timestamp(first_day)) & (df["Date"] <= pd.Timestamp(last_day))]
    if not show_hidden:
        filtered_df = filtered_df[~filtered_df["Hidden"]]
    return filtered_df 