"""Utility functions for financial calculations."""
from __future__ import annotations

from datetime import date

import pandas as pd


def calculate_kpis(filtered_df: pd.DataFrame) -> tuple[float, float]:
    """Calculate total expenses and income from the filtered dataset."""
    total_expenses = filtered_df[filtered_df["Amount"] < 0]["Amount"].sum()
    total_income = filtered_df[filtered_df["Amount"] > 0]["Amount"].sum()
    return total_expenses, total_income


def calculate_monthly_averages(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate average monthly spending for each category/subcategory."""
    # Get number of unique months in the dataset
    num_months = df["Date"].dt.to_period("M").nunique()

    # Group by category and subcategory and calculate monthly averages
    return (
        df[df["Amount"] < 0]
        .groupby(["Category", "Subcategory"])["Amount"]
        .sum()
        .div(-num_months)  # Divide by number of months and make positive
        .reset_index()
    )


def format_date_range(first_day: date, last_day: date) -> str:
    """Format date range in a more natural way."""
    if first_day.year == last_day.year:
        if first_day.month == last_day.month:
            return f"{first_day.strftime('%d')} to {last_day.strftime('%d')} of {last_day.strftime('%B %Y')}"
        return f"{first_day.strftime('%d %B')} to {last_day.strftime('%d %B %Y')}"
    return f"{first_day.strftime('%d %B %Y')} to {last_day.strftime('%d %B %Y')}" 