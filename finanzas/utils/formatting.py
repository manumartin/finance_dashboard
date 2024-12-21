"""Utility functions for formatting and display."""

from __future__ import annotations

from datetime import date


def format_date_range(first_day: date, last_day: date) -> str:
    """Format date range in a more natural way.

    Args:
        first_day: Start date of the range
        last_day: End date of the range

    Returns:
        A formatted string representing the date range in a natural way

    """
    if first_day.year == last_day.year:
        if first_day.month == last_day.month:
            return f"{first_day.strftime('%d')} to {last_day.strftime('%d')} of {last_day.strftime('%B %Y')}"
        return f"{first_day.strftime('%d %B')} to {last_day.strftime('%d %B %Y')}"
    return f"{first_day.strftime('%d %B %Y')} to {last_day.strftime('%d %B %Y')}"
