"""UI components for trend analysis and projections."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
import plotly.express as px  # type: ignore[import-untyped]
import streamlit as st

if TYPE_CHECKING:
    from finanzas.data.loader import DataLoader


def display_trend_analysis(loader: DataLoader) -> None:
    """Display trend analysis and projection with an improved UI layout."""
    st.subheader("Balance Trend Analysis and Projection")

    # Prepare daily balance data
    trend_df = (
        loader.filtered_data.sort_values("Date")
        .groupby("Date")["Balance"]
        .last()
        .reset_index()
    )
    current_balance = trend_df["Balance"].iloc[-1]
    last_date = trend_df["Date"].max()

    # Calculate historical metrics
    days_in_data = (last_date - trend_df["Date"].min()).days + 1
    historical_daily_rate = (trend_df["Balance"].iloc[-1] - trend_df["Balance"].iloc[0]) / days_in_data
    historical_monthly_rate = historical_daily_rate * 30

    # Create three columns for better UI organization
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.metric("Current Balance", f"{current_balance:,.2f}€")

    with col2:
        st.metric(
            "Historical Monthly Rate",
            f"{historical_monthly_rate:,.2f}€",
            delta=f"{historical_monthly_rate/current_balance*100:.1f}% monthly",
        )

    with col3:
        minimum_balance = st.number_input(
            "Target Balance(€)",
            value=int(current_balance * 2) if current_balance > 0 else 1000,
            step=1000,
            format="%d",
        )

    # Projection controls in an expander
    with st.expander("Configure Projection", expanded=True):
        col1, col2 = st.columns([1, 1])
        with col1:
            projection_type = st.radio(
                "Projection Type",
                ["Historical", "Custom"],
                horizontal=True,
            )

        with col2:
            monthly_rate = st.number_input(
                "Custom monthly rate (€)",
                value=int(historical_monthly_rate),
                step=100,
                format="%d",
                disabled=(projection_type == "Historical"),
            )

    # Calculate target dates
    if projection_type == "Historical":
        monthly_rate = historical_monthly_rate

    if monthly_rate != 0:
        # Calculate direction of movement needed and actual movement
        target_direction = 1 if minimum_balance > current_balance else -1
        rate_direction = 1 if monthly_rate > 0 else -1

        # Check if we're moving in the wrong direction
        if target_direction != rate_direction:
            st.warning(
                "⚠️ With the current monthly rate of "
                f"**{monthly_rate:,.0f}€**, you will never reach the target of "
                f"**{minimum_balance:,.0f}€** because the balance is moving in the opposite direction.",
            )
        else:
            # Calculate days to target
            effective_rate = abs(monthly_rate)
            days_to_target = abs((minimum_balance - current_balance) / (effective_rate / 30))
            target_date = datetime.now(tz=timezone.utc).date() + pd.Timedelta(days=int(days_to_target))

            direction_text = "increase" if target_direction > 0 else "decrease"
            st.info(
                f"With a monthly {direction_text} of **{effective_rate:,.0f}€**, "
                f"you will reach the target of **{minimum_balance:,.0f}€** "
                f"on **{target_date.strftime('%d/%m/%Y')}** "
                f"({int(days_to_target)} days)",
            )

        # Create the plot
        fig = px.line(
            trend_df,
            x="Date",
            y="Balance",
            title="Balance Evolution and Projection",
        )

        # Add projection line only if we're moving in the right direction
        if target_direction == rate_direction:
            target_dates = pd.date_range(start=last_date, end=target_date, freq="D")[1:]
            target_values = np.linspace(current_balance, minimum_balance, len(target_dates) + 1)[1:].round(2)
            fig.add_scatter(
                x=target_dates,
                y=target_values,
                line={"dash": "dot", "color": "green"},
                name=f"Projection ({monthly_rate:,.0f}€/month)",
            )

        # Add target balance line
        fig.add_hline(
            y=minimum_balance,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Target: {minimum_balance:,.0f}€",
        )

        # Update layout with more detailed x-axis and vertical month lines
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Balance (€)",
            hovermode="x unified",
            yaxis={
                "tickformat": ",d€",
                "ticksuffix": "€",
            },
            xaxis={
                "dtick": "M1",
                "tickformat": "%b %Y",
                "showgrid": True,
                "gridcolor": "rgba(128, 128, 128, 0.2)",
                "gridwidth": 1,
            },
            legend={
                "yanchor": "top",
                "y": 0.99,
                "xanchor": "left",
                "x": 0.01,
                "bgcolor": "rgba(255, 255, 255, 0.8)",
            },
        )

        st.plotly_chart(fig, use_container_width=True)
