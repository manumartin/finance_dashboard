"""A Streamlit dashboard for personal finance analysis and visualization.

This module provides interactive visualizations and analysis tools for personal financial data,
including expense tracking, income analysis, and balance projections. Features include:
- KPI displays for total income and expenses
- Interactive treemaps for expense and income breakdown
- Balance trend analysis with future projections
- Customizable date range and category filters
"""

from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, timezone

import numpy as np
import pandas as pd
import plotly.express as px  # type: ignore[import-untyped]
import streamlit as st


def load_dataset(path: str | st.runtime.uploaded_file_manager.UploadedFile) -> pd.DataFrame:
    """Load and preprocess the financial dataset from a CSV file or uploaded file."""

    def convert_to_numeric(series: pd.Series) -> pd.Series:
        if series.dtype == object:  # Only process strings
            return pd.to_numeric(series.str.replace("€", "").str.replace(".", "").str.replace(",", "."))
        return series

    # Both string paths and uploaded files can be read directly by pd.read_csv
    data = pd.read_csv(path)
    data["Date"] = pd.to_datetime(data["Date"])
    data["Balance"] = convert_to_numeric(data["Balance"])
    data["Amount"] = convert_to_numeric(data["Amount"])
    return data


def get_date_range(df: pd.DataFrame) -> tuple[date, date]:
    """Extract the minimum and maximum dates from the dataset."""
    min_date = df["Date"].min().date()
    max_date = df["Date"].max().date()
    return min_date, max_date


def filter_data(
    df: pd.DataFrame,
    first_day: date,
    last_day: date,
) -> pd.DataFrame:
    """Filter dataset by date range."""
    return df[(df["Date"] >= pd.Timestamp(first_day)) & (df["Date"] <= pd.Timestamp(last_day))]


def calculate_kpis(filtered_df: pd.DataFrame) -> tuple[float, float]:
    """Calculate total expenses and income from the filtered dataset."""
    total_expenses = filtered_df[filtered_df["Amount"] < 0]["Amount"].sum()
    total_income = filtered_df[filtered_df["Amount"] > 0]["Amount"].sum()
    return total_expenses, total_income


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
        texttemplate="%{label}<br>%{value:,.2f}€",
        hovertemplate="%{label}<br>%{value:,.2f}€<extra></extra>",
    )
    fig.update_layout(height=800)
    return fig


def setup_page() -> None:
    """Set up the Streamlit page configuration."""
    st.set_page_config(page_title="Financial Analysis", page_icon="", layout="wide")
    st.title("Financial Dashboard")


def display_sidebar_filters(
    min_date: date,
    max_date: date,
) -> tuple[date, date]:
    """Create sidebar filters and return selected options."""
    st.sidebar.header("Filters")

    if min_date > max_date:
        min_date, max_date = max_date, min_date
    month_labels = [d.strftime("%B %Y").capitalize() for d in pd.date_range(start=min_date, end=max_date, freq="MS")]

    selected_month_range = st.sidebar.select_slider(
        "Select Month Range",
        options=range(len(month_labels)),
        value=(0, len(month_labels) - 1),
        format_func=lambda x: month_labels[x],
    )

    months = pd.to_datetime(month_labels, format="%B %Y")
    first_day = datetime(
        months[selected_month_range[0]].year,
        months[selected_month_range[0]].month,
        1,
        tzinfo=timezone.utc,
    ).date()
    last_day = min(
        datetime(
            months[selected_month_range[1]].year,
            months[selected_month_range[1]].month,
            monthrange(
                months[selected_month_range[1]].year,
                months[selected_month_range[1]].month,
            )[1],
            tzinfo=timezone.utc,
        ).date(),
        max_date,
    )

    return first_day, last_day


def display_kpis(filtered_df: pd.DataFrame) -> None:
    """Calculate and display key performance indicators."""
    total_expenses, total_income = calculate_kpis(filtered_df)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Expenses", f"{abs(total_expenses):,.2f}€")
    with col2:
        st.metric("Total Income", f"{total_income:,.2f}€")


def format_date_range(first_day: date, last_day: date) -> str:
    """Format date range in a more natural way."""
    if first_day.year == last_day.year:
        if first_day.month == last_day.month:
            return f"{first_day.strftime('%d')} to {last_day.strftime('%d')} of {last_day.strftime('%B %Y')}"
        return f"{first_day.strftime('%d %B')} to {last_day.strftime('%d %B %Y')}"
    return f"{first_day.strftime('%d %B %Y')} to {last_day.strftime('%d %B %Y')}"


def display_treemaps(filtered_df: pd.DataFrame, total_expenses: float, total_income: float) -> None:
    """Display treemaps for income and expenses."""
    st.subheader("Income Breakdown")
    earnings_df = filtered_df[filtered_df["Amount"] > 0].copy()
    earnings_treemap_fig = create_treemap(earnings_df, total_income, "Income Breakdown")
    st.plotly_chart(earnings_treemap_fig, use_container_width=True)

    st.subheader("Expense Breakdown")
    expenses_df = filtered_df[filtered_df["Amount"] < 0].copy()
    expenses_df["Amount"] = expenses_df["Amount"].abs()
    expenses_treemap_fig = create_treemap(expenses_df, abs(total_expenses), "Expense Breakdown")
    st.plotly_chart(expenses_treemap_fig, use_container_width=True)


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


def display_trend_analysis(filtered_df: pd.DataFrame) -> None:
    """Display trend analysis and projection with an improved UI layout."""
    st.subheader("Balance Trend Analysis and Projection")

    # Prepare daily balance data
    trend_df = filtered_df.sort_values("Date").groupby("Date")["Balance"].last().reset_index()
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
                f"**{minimum_balance:,.0f}€** because the balance is moving in the opposite direction."
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


def display_data_grid(df: pd.DataFrame) -> None:
    """Display the dataset in a grid format."""
    # Create a copy of the dataframe with formatted columns
    grid_df = df.copy()

    # Reorder and rename columns for better display
    columns = {
        "Date": "Date",
        "Concept": "Concept",
        "Category": "Category",
        "Subcategory": "Subcategory",
        "Amount": "Amount",
        "Balance": "Balance",
    }

    grid_df = grid_df[columns.keys()].rename(columns=columns)

    # Display the grid with fixed headers and column configurations
    st.dataframe(
        grid_df,
        use_container_width=True,
        hide_index=True,
        height=400,
        column_config={
            "Date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
            "Amount": st.column_config.NumberColumn(
                "Amount",
                format="%.2f €",
            ),
            "Balance": st.column_config.NumberColumn(
                "Balance",
                format="%.2f €",
            ),
        },
    )


def main() -> None:
    """Run the Streamlit app."""
    st.set_page_config(page_title="Financial Analysis", page_icon="💰", layout="wide")
    st.title("Financial Dashboard")

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
    first_day, last_day = display_sidebar_filters(min_date, max_date)

    filtered_df = filter_data(data, first_day, last_day)
    st.caption(f"Showing data from {format_date_range(first_day, last_day)}")

    # Display KPIs above the tabs
    display_kpis(filtered_df)
    total_expenses, total_income = calculate_kpis(filtered_df)

    # Create tabs for different visualizations
    tab1, tab2, tab3, tab4 = st.tabs(["Income and Expense Breakdown", "Monthly Averages", "Trend Analysis", "Data"])

    with tab1:
        display_treemaps(filtered_df, total_expenses, total_income)

    with tab2:
        display_monthly_averages(filtered_df)

    with tab3:
        display_trend_analysis(filtered_df)

    with tab4:
        display_data_grid(filtered_df)


if __name__ == "__main__":
    main()
