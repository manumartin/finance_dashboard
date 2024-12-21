"""Data loading and preprocessing functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
import streamlit as st

if TYPE_CHECKING:
    from datetime import date


class DataLoader:
    """Handles loading and preprocessing of financial data."""

    def __init__(self) -> None:
        """Initialize the data loader."""
        self.data: pd.DataFrame | None = None
        self.filtered_df: pd.DataFrame | None = None
        self.categories: set[str] = set()
        self.subcategories: dict[str, set[str]] = {}
        self.hidden_entries: set[int] = set()  # Store indices of hidden entries

    def load_dataset(self, path: str | st.runtime.uploaded_file_manager.UploadedFile) -> None:
        """Load and preprocess the financial dataset from a CSV file or uploaded file."""
        # Only load from file if we don't have data yet
        if self.data is None:
            self.data = self._process_raw_data(pd.read_csv(path))
            self.update_categories()

    def _process_raw_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process the raw dataframe into the required format."""
        # Ensure all required columns exist
        required_columns = {"Date", "Description", "Category", "Subcategory", "Amount", "Balance"}
        missing_columns = required_columns - set(df.columns)
        if missing_columns:
            for col in missing_columns:
                df[col] = ""  # Add missing columns with empty values

        df["Date"] = pd.to_datetime(df["Date"])
        df["Balance"] = df["Balance"].astype(float)
        df["Amount"] = df["Amount"].astype(float)

        return df

    def reset_state(self) -> None:
        """Reset the loader's state."""
        self.data = None
        self.categories = set()
        self.subcategories = {}
        self.hidden_entries = set()

    def filter_data(self, first_day: date, last_day: date, *, show_hidden: bool = False) -> None:
        """Filter dataset by date range and hidden status."""
        if self.data is None:
            msg = "Data not loaded. Call load_dataset first."
            raise ValueError(msg)

        mask = (self.data["Date"] >= pd.Timestamp(first_day)) & (self.data["Date"] <= pd.Timestamp(last_day))

        if not show_hidden:
            mask = mask & ~self.data.index.isin(self.hidden_entries)

        self.filtered_df = self.data[mask]

    def hide_entry(self, index: int) -> None:
        """Hide a specific entry by its index."""
        if self.data is not None and index in self.data.index:
            self.hidden_entries.add(index)

    def unhide_entry(self, index: int) -> None:
        """Unhide a specific entry by its index."""
        self.hidden_entries.discard(index)

    def is_hidden(self, index: int) -> bool:
        """Check if an entry is hidden."""
        return index in self.hidden_entries

    def get_date_range(self) -> tuple[date, date]:
        """Extract the minimum and maximum dates from the dataset."""
        min_date = self.raw_data["Date"].min().date()
        max_date = self.raw_data["Date"].max().date()
        return min_date, max_date

    def calculate_monthly_averages(self) -> pd.DataFrame:
        """Calculate average monthly spending for each category/subcategory."""
        # Get number of unique months in the dataset
        num_months = self.raw_data["Date"].dt.to_period("M").nunique()

        # Group by category and subcategory and calculate monthly averages
        return (
            self.raw_data[self.raw_data["Amount"] < 0]
            .groupby(["Category", "Subcategory"])["Amount"]
            .sum()
            .div(-num_months)  # Divide by number of months and make positive
            .reset_index()
        )

    def calculate_kpis(self) -> tuple[float, float]:
        """Calculate total expenses and income from the filtered dataset."""
        total_expenses = self.filtered_data[self.filtered_data["Amount"] < 0]["Amount"].sum()
        total_income = self.filtered_data[self.filtered_data["Amount"] > 0]["Amount"].sum()
        return total_expenses, total_income

    def has_data(self) -> bool:
        """Check if data is loaded in the DataLoader."""
        return self.data is not None

    @property
    def raw_data(self) -> pd.DataFrame:
        """Get the raw dataset."""
        if self.data is None:
            msg = "Data not loaded. Call load_dataset first."
            raise ValueError(msg)
        return self.data

    @property
    def filtered_data(self) -> pd.DataFrame:
        """Get the filtered dataset."""
        if self.filtered_df is None:
            msg = "Filtered data not available. Call filter_data first."
            raise ValueError(msg)
        return self.filtered_df

    def update_categories(self) -> None:
        """Update categories and subcategories from the current data."""
        self.categories = set(self.raw_data["Category"].unique())
        self.subcategories = {
            category: set(self.raw_data[self.raw_data["Category"] == category]["Subcategory"].unique())
            for category in self.categories
        }
