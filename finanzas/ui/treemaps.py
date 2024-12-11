"""UI components for treemap visualizations."""
from __future__ import annotations

import pandas as pd
import plotly.express as px  # type: ignore[import-untyped]
import streamlit as st

from finanzas.utils.calculations import calculate_kpis, calculate_monthly_averages


def create_treemap(df: pd.DataFrame, total: float, title: str) -> px.treemap:
    """Create a treemap visualization from a DataFrame."""
    df["Entry"] = df.apply(
        lambda x: f"{x['Concept']} ({x['Amount']:,.2f}€) - {x['Date'].strftime('%d/%m/%Y')}",
        axis=1,
    )
    df["Total"] = f"Total {title}: {total:,.2f}€"
    fig = px.treemap(
        df,
        path=["Total", "Category", "Subcategory", "Entry"],
        values="Amount",
        title=title,
    )
    fig.update_traces(
        textinfo="label+value",
        texttemplate="%{label}<br>%{value:,.2f}",
        hovertemplate="%{label}<br>%{value:,.2f}€<extra></extra>",
    )
    fig.update_layout(height=800)
    return fig


def display_treemaps(filtered_df: pd.DataFrame) -> None:
    """Display treemaps for income and expenses."""
    total_expenses, total_income = calculate_kpis(filtered_df)

    st.subheader("Income Breakdown")
    earnings_df = filtered_df[filtered_df["Amount"] > 0].copy()
    earnings_treemap_fig = create_treemap(earnings_df, total_income, "Income Breakdown")
    st.plotly_chart(earnings_treemap_fig, use_container_width=True)

    st.subheader("Expense Breakdown")
    expenses_df = filtered_df[filtered_df["Amount"] < 0].copy()
    expenses_df["Amount"] = expenses_df["Amount"].abs()
    expenses_treemap_fig = create_treemap(expenses_df, abs(total_expenses), "Expense Breakdown")
    st.plotly_chart(expenses_treemap_fig, use_container_width=True)


def display_monthly_averages(filtered_df: pd.DataFrame) -> None:
    """Display treemap for average monthly spending."""
    st.subheader("Monthly Average Expenses")

    monthly_avg_df = calculate_monthly_averages(filtered_df)
    total_monthly_avg = monthly_avg_df["Amount"].sum()

    # Create simplified entry labels for averages
    monthly_avg_df["Entry"] = monthly_avg_df.apply(
        lambda x: f"{x['Subcategory']} ({x['Amount']:,.2f}€/month)",
        axis=1,
    )
    monthly_avg_df["Total"] = f"Monthly Average: {total_monthly_avg:,.2f}€"

    fig = px.treemap(
        monthly_avg_df,
        path=["Total", "Category", "Entry"],
        values="Amount",
        title="Monthly Average Expenses by Category",
    )

    fig.update_traces(
        textinfo="label+value",
        texttemplate="%{label}<br>%{value:,.2f}€",
        hovertemplate="%{label}<br>%{value:,.2f}€/month<extra></extra>",
    )
    fig.update_layout(height=600)

    st.plotly_chart(fig, use_container_width=True) 