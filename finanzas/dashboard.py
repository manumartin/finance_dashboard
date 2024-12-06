"""A Streamlit dashboard for personal finance analysis and visualization.

This module provides interactive visualizations and analysis tools for personal financial data,
including expense tracking, income analysis, and balance projections. Features include:
- KPI displays for total income and expenses
- Interactive treemaps for expense and income breakdown
- Balance trend analysis with future projections
- Customizable date range and category filters
"""

import locale
from calendar import monthrange
from datetime import date, datetime

import numpy as np
import pandas as pd
import plotly.express as px  # type:  ignore
import streamlit as st

locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")  # Set locale to Spanish


def load_dataset(path: str) -> pd.DataFrame:
    """Load and preprocess the financial dataset from a CSV file."""
    df = pd.read_csv(path)
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    df["Saldo"] = convert_to_numeric(df["Saldo"])
    df["Importe"] = convert_to_numeric(df["Importe"])
    return df


def convert_to_numeric(series: pd.Series) -> pd.Series:
    if series.dtype == object:  # Only process strings
        return pd.to_numeric(series.str.replace("€", "").str.replace(".", "").str.replace(",", "."))
    return series


def get_date_range(df: pd.DataFrame) -> tuple[date, date]:
    """Extract the minimum and maximum dates from the dataset."""
    min_date = df["Fecha"].min().date()
    max_date = df["Fecha"].max().date()
    return min_date, max_date


def filter_data(
    df: pd.DataFrame,
    first_day: date,
    last_day: date,
) -> pd.DataFrame:
    """Filter dataset by date range."""
    filtered_df = df[(df["Fecha"] >= pd.Timestamp(first_day)) & (df["Fecha"] <= pd.Timestamp(last_day))]
    return filtered_df


def calculate_kpis(filtered_df: pd.DataFrame) -> tuple[float, float]:
    """Calculate total expenses and income from the filtered dataset."""
    total_expenses = filtered_df[filtered_df["Importe"] < 0]["Importe"].sum()
    total_income = filtered_df[filtered_df["Importe"] > 0]["Importe"].sum()
    return total_expenses, total_income


def create_treemap(df: pd.DataFrame, total: float, title: str) -> px.treemap:
    """Create a treemap visualization from a DataFrame."""
    df["Entry"] = df.apply(
        lambda x: f"{x['Concepto']} ({x['Importe']:,.2f}€) - {x['Fecha'].strftime('%d/%m/%Y')}",
        axis=1,
    )
    df["Total"] = f"Total {title}: {total:,.2f}€"
    fig = px.treemap(
        df,
        path=["Total", "Category", "Subcategory", "Entry"],
        values="Importe",
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
    st.set_page_config(page_title="Análisis Financiero", page_icon="", layout="wide")
    st.title("Panel Financiero")


def display_sidebar_filters(
    df: pd.DataFrame,
    min_date: date,
    max_date: date,
) -> tuple[date, date]:
    """Create sidebar filters and return selected options."""
    st.sidebar.header("Filtros")

    if min_date > max_date:
        min_date, max_date = max_date, min_date
    month_labels = [d.strftime("%B %Y").capitalize() for d in pd.date_range(start=min_date, end=max_date, freq="MS")]

    selected_month_range = st.sidebar.select_slider(
        "Seleccionar Rango de Meses",
        options=range(len(month_labels)),
        value=(0, len(month_labels) - 1),
        format_func=lambda x: month_labels[x],
    )

    months = pd.to_datetime(month_labels, format="%B %Y")
    first_day = datetime(months[selected_month_range[0]].year, months[selected_month_range[0]].month, 1).date()
    last_day = min(
        datetime(
            months[selected_month_range[1]].year,
            months[selected_month_range[1]].month,
            monthrange(
                months[selected_month_range[1]].year,
                months[selected_month_range[1]].month,
            )[1],
        ).date(),
        max_date,
    )

    return first_day, last_day


def display_kpis(filtered_df: pd.DataFrame) -> None:
    """Calculate and display key performance indicators."""
    total_expenses, total_income = calculate_kpis(filtered_df)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Gastos Totales", f"{abs(total_expenses):,.2f}€")
    with col2:
        st.metric("Ingresos Totales", f"{total_income:,.2f}€")


def format_date_range(first_day: date, last_day: date) -> str:
    """Format date range in a more natural way."""
    if first_day.year == last_day.year:
        if first_day.month == last_day.month:
            return f"{first_day.strftime('%d')} al {last_day.strftime('%d')} de {last_day.strftime('%B de %Y')}"
        return f"{first_day.strftime('%d de %B')} al {last_day.strftime('%d de %B de %Y')}"
    return f"{first_day.strftime('%d de %B de %Y')} al {last_day.strftime('%d de %B de %Y')}"


def display_treemaps(filtered_df: pd.DataFrame, total_expenses: float, total_income: float) -> None:
    """Display treemaps for income and expenses."""
    st.subheader("Desglose de Ingresos")
    earnings_df = filtered_df[filtered_df["Importe"] > 0].copy()
    earnings_treemap_fig = create_treemap(earnings_df, total_income, "Desglose de Ingresos")
    st.plotly_chart(earnings_treemap_fig, use_container_width=True)

    st.subheader("Desglose de Gastos")
    expenses_df = filtered_df[filtered_df["Importe"] < 0].copy()
    expenses_df["Importe"] = expenses_df["Importe"].abs()
    expenses_treemap_fig = create_treemap(expenses_df, abs(total_expenses), "Desglose de Gastos")
    st.plotly_chart(expenses_treemap_fig, use_container_width=True)


def calculate_monthly_averages(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate average monthly spending for each category/subcategory."""
    # Get number of unique months in the dataset
    num_months = df["Fecha"].dt.to_period("M").nunique()

    # Group by category and subcategory and calculate monthly averages
    monthly_avg = (
        df[df["Importe"] < 0]
        .groupby(["Category", "Subcategory"])["Importe"]
        .sum()
        .div(-num_months)  # Divide by number of months and make positive
        .reset_index()
    )
    return monthly_avg


def display_monthly_averages(filtered_df: pd.DataFrame) -> None:
    """Display treemap for average monthly spending."""
    st.subheader("Promedio Mensual de Gastos")

    monthly_avg_df = calculate_monthly_averages(filtered_df)
    total_monthly_avg = monthly_avg_df["Importe"].sum()

    # Create simplified entry labels for averages
    monthly_avg_df["Entry"] = monthly_avg_df.apply(
        lambda x: f"{x['Subcategory']} ({x['Importe']:,.2f}€/mes)",
        axis=1,
    )
    monthly_avg_df["Total"] = f"Promedio Mensual: {total_monthly_avg:,.2f}€"

    fig = px.treemap(
        monthly_avg_df,
        path=["Total", "Category", "Entry"],
        values="Importe",
        title="Promedio Mensual de Gastos por Categoría",
    )

    fig.update_traces(
        textinfo="label+value",
        texttemplate="%{label}<br>%{value:,.2f}€",
        hovertemplate="%{label}<br>%{value:,.2f}€/mes<extra></extra>",
    )
    fig.update_layout(height=600)

    st.plotly_chart(fig, use_container_width=True)


def display_trend_analysis(filtered_df: pd.DataFrame) -> None:
    """Display trend analysis and projection with an improved UI layout."""
    st.subheader("Análisis de Tendencia y Proyección de Saldo")

    # Prepare daily balance data
    trend_df = filtered_df.sort_values("Fecha").groupby("Fecha")["Saldo"].last().reset_index()
    current_balance = trend_df["Saldo"].iloc[-1]
    last_date = trend_df["Fecha"].max()

    # Calculate historical metrics
    days_in_data = (last_date - trend_df["Fecha"].min()).days + 1
    historical_daily_rate = (trend_df["Saldo"].iloc[-1] - trend_df["Saldo"].iloc[0]) / days_in_data
    historical_monthly_rate = historical_daily_rate * 30

    # Create three columns for better UI organization
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.metric("Saldo Actual", f"{current_balance:,.2f}€")

    with col2:
        st.metric(
            "Ritmo Histórico Mensual",
            f"{historical_monthly_rate:,.2f}€",
            delta=f"{historical_monthly_rate/current_balance*100:.1f}% mensual",
        )

    with col3:
        minimum_balance = st.number_input(
            "Saldo mínimo (€)",
            min_value=0,
            value=int(current_balance / 2),
            step=1000,
            format="%d",
        )

    # Projection controls in an expander
    with st.expander("Configurar Proyección", expanded=True):
        col1, col2 = st.columns([1, 1])
        with col1:
            projection_type = st.radio(
                "Tipo de Proyección",
                ["Histórica", "Personalizada"],
                horizontal=True,
            )

        with col2:
            monthly_rate = st.number_input(
                "Ritmo mensual objetivo (€)",
                value=int(historical_monthly_rate),
                step=100,
                format="%d",
                disabled=(projection_type == "Histórica"),
            )

    # Calculate target dates
    if projection_type == "Histórica":
        monthly_rate = historical_monthly_rate

    if monthly_rate != 0:
        # Calculate days to both minimum balance and zero
        days_to_min = abs((minimum_balance - current_balance) / (monthly_rate / 30))
        days_to_zero = abs((0 - current_balance) / (monthly_rate / 30))

        target_date = datetime.now().date() + pd.Timedelta(days=int(days_to_min))
        zero_date = datetime.now().date() + pd.Timedelta(days=int(days_to_zero))

        # Use the later date for projection
        projection_end_date = zero_date if monthly_rate < 0 else target_date

        st.info(
            f"Con un ritmo de ahorro de **{monthly_rate:,.0f}€/mes**, "
            f"alcanzarás el objetivo de **{minimum_balance:,.0f}€** "
            f"el **{target_date.strftime('%d/%m/%Y')}** "
            f"({int(days_to_min)} días)"
        )

    # Create the plot
    fig = px.line(
        trend_df,
        x="Fecha",
        y="Saldo",
        title="Evolución del Saldo y Proyección",
    )

    # Add projection line
    target_dates = pd.date_range(start=last_date, end=projection_end_date, freq="D")[1:]
    final_value = 0 if monthly_rate < 0 else minimum_balance
    target_values = np.linspace(current_balance, final_value, len(target_dates) + 1)[1:].round(2)
    fig.add_scatter(
        x=target_dates,
        y=target_values,
        line={"dash": "dot", "color": "green"},
        name=f"Proyección ({monthly_rate:,.0f}€/mes)",
    )

    # Add target balance line
    fig.add_hline(
        y=minimum_balance,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Objetivo: {minimum_balance:,.0f}€",
    )

    # Update layout with more detailed x-axis and vertical month lines
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Saldo (€)",
        hovermode="x unified",
        yaxis={
            "tickformat": ",d€",
            "ticksuffix": "€",
            "rangemode": "nonnegative",  # Forces y-axis to start at 0
        },
        xaxis={
            "dtick": "M1",
            "tickformat": "%b %Y",
            "showgrid": True,
            "gridcolor": "rgba(128, 128, 128, 0.2)",
            "gridwidth": 1,
        },
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255, 255, 255, 0.8)",
        ),
    )

    st.plotly_chart(fig, use_container_width=True)


def display_data_grid(df: pd.DataFrame) -> None:
    """Display the dataset in a grid format."""
    # Create a copy of the dataframe with formatted columns
    grid_df = df.copy()

    # Reorder and rename columns for better display
    columns = {
        "Fecha": "Fecha",
        "Concepto": "Concepto",
        "Category": "Categoría",
        "Subcategory": "Subcategoría",
        "Importe": "Importe",
        "Saldo": "Saldo",
    }

    grid_df = grid_df[columns.keys()].rename(columns=columns)

    # Display the grid with fixed headers and column configurations
    st.dataframe(
        grid_df,
        use_container_width=True,
        hide_index=True,
        height=400,
        column_config={
            "Fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
            "Importe": st.column_config.NumberColumn(
                "Importe",
                format="%.2f €",
            ),
            "Saldo": st.column_config.NumberColumn(
                "Saldo",
                format="%.2f €",
            ),
        },
    )


def main() -> None:
    """Run the Streamlit app."""
    st.set_page_config(page_title="Análisis Financiero", page_icon="💰", layout="wide")
    st.title("Panel Financiero")

    # Add file uploader in the sidebar
    st.sidebar.header("Datos")
    uploaded_file = st.sidebar.file_uploader(
        "Cargar dataset (CSV)",
        type="csv",
        help="Sube un archivo CSV con las columnas: Fecha, Concepto, Category, Subcategory, Importe, Saldo",
    )

    try:
        if uploaded_file is not None:
            df = load_dataset(uploaded_file)
        else:
            # Use default dataset if no file is uploaded
            dataset_path = "./data/fake_dataset.csv"
            df = load_dataset(dataset_path)
    except Exception as e:
        st.error(
            "Error al cargar el dataset. Asegúrate de que el archivo tiene el formato correcto: "
            "Fecha, Concepto, Category, Subcategory, Importe, Saldo"
        )
        st.exception(e)
        return

    min_date, max_date = get_date_range(df)
    first_day, last_day = display_sidebar_filters(df, min_date, max_date)

    filtered_df = filter_data(df, first_day, last_day)
    st.caption(f"Mostrando datos del {format_date_range(first_day, last_day)}")

    # Display KPIs above the tabs
    display_kpis(filtered_df)
    total_expenses, total_income = calculate_kpis(filtered_df)

    # Create tabs for different visualizations
    tab1, tab2, tab3, tab4 = st.tabs(
        ["Desglose de Gastos e Ingresos", "Promedios Mensuales", "Análisis de Tendencia", "Datos"]
    )

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
