"""Import wizard UI component for data import workflow."""

from __future__ import annotations

import io
from typing import TYPE_CHECKING, Literal

import pandas as pd
import streamlit as st

if TYPE_CHECKING:
    from finanzas.data.loader import DataLoader


def detect_file_format(file_content: bytes) -> Literal["caixabank", "native"]:
    """Detect the format of the uploaded CSV file."""
    # Read first few lines of the file
    content = file_content.decode("utf-8")
    headers = content.split("\n")[2].strip() if content else ""  # For CaixaBank, check 3rd line

    # Check for CaixaBank headers
    if all(header in headers for header in ["Concepto", "Fecha", "Importe", "Saldo"]):
        return "caixabank"
    # Check for native format headers
    if all(header in headers for header in ["Concept", "Date", "Amount", "Balance"]):
        return "native"
    # Default to native if unknown
    return "native"


def parse_caixabank_csv(file_content: bytes) -> pd.DataFrame:
    """Parse a Caixabank CSV file format into a pandas DataFrame."""
    # Read the CSV content, skipping the first two rows (first table)
    data = pd.read_csv(
        io.StringIO(file_content.decode("utf-8")),
        sep=";",
        skiprows=2,
        encoding="utf-8",
    )

    # Remove rows where all columns are empty or just separators
    data = data.dropna(how="all").reset_index(drop=True)

    # Remove rows where essential columns are empty
    data = data[
        data["Concepto"].notna() & data["Fecha"].notna() & data["Importe"].notna() & data["Saldo"].notna()
    ].reset_index(
        drop=True,
    )

    # Rename columns to match our format
    data = data.rename(columns={"Concepto": "Concept", "Fecha": "Date", "Importe": "Amount", "Saldo": "Balance"})

    # Convert date format
    data["Date"] = pd.to_datetime(data["Date"], format="%d/%m/%Y")

    # Clean and convert Amount
    data["Amount"] = data["Amount"].astype(float)

    # Clean and convert Balance (remove EUR suffix and handle decimal separator)
    data["Balance"] = (
        data["Balance"]
        .str.replace("EUR", "")  # Remove EUR suffix
        .str.replace(".", "")  # Remove thousand separator
        .str.replace(",", ".")  # Convert decimal separator
        .astype(float)
    )

    # Add required columns with default values
    data["Category"] = ""
    data["Subcategory"] = ""
    data["Subscription"] = False

    return data


def parse_native_csv(file_content: bytes) -> pd.DataFrame:
    """Parse a native format CSV file."""
    data = pd.read_csv(io.StringIO(file_content.decode("utf-8")))

    # Remove rows where all columns are empty
    data = data.dropna(how="all").reset_index(drop=True)

    # Remove rows where essential columns are empty
    data = data[
        data["Concept"].notna() & data["Date"].notna() & data["Amount"].notna() & data["Balance"].notna()
    ].reset_index(
        drop=True,
    )

    # Convert date format if it's not already datetime
    data["Date"] = pd.to_datetime(data["Date"])

    # Ensure numeric types
    data["Amount"] = data["Amount"].astype(float)
    data["Balance"] = data["Balance"].astype(float)

    # Ensure boolean type for Subscription
    data["Subscription"] = data["Subscription"].astype(bool)

    return data


def merge_transactions(existing_df: pd.DataFrame, new_df: pd.DataFrame) -> pd.DataFrame:
    """Merge new transactions with existing ones, avoiding duplicates."""

    # Create a unique key for each transaction
    def create_key(df: pd.DataFrame) -> pd.Series:
        return df["Concept"] + df["Date"].dt.strftime("%Y-%m-%d")

    if len(existing_df) > 0:
        existing_keys = set(create_key(existing_df))
        # Filter out transactions that already exist
        new_df = new_df[~create_key(new_df).isin(existing_keys)]
        # Concatenate with existing data
        return pd.concat([existing_df, new_df], ignore_index=True)

    return new_df


def import_data_page(data_loader: DataLoader) -> None:
    """Show the import wizard modal dialog."""
    # Show format help directly
    st.info(
        "Supported formats:\n\n"
        "• **CaixaBank CSV**: Standard CaixaBank export with columns: Concepto, Fecha, Importe, Saldo\n\n"
        "• **Native format**: CSV with columns: Concept, Date, Amount, Balance, Category, Subcategory, Subscription",
    )

    # File upload with automatic import
    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"], key="import_wizard_file")

    if uploaded_file is not None:
        try:
            # Read file content and detect format
            file_content = uploaded_file.read()
            file_format = detect_file_format(file_content)

            # Parse the file according to detected format
            if file_format == "caixabank":
                new_df = parse_caixabank_csv(file_content)
            elif file_format == "native":  # native format
                new_df = parse_native_csv(file_content)
            else:
                st.error("Unsupported file format")
                return

            # Always merge with existing data if present
            if data_loader.data is not None and len(data_loader.data.index) != 0:
                final_df = merge_transactions(data_loader.data, new_df)
                new_transactions = len(final_df) - len(data_loader.data)
                data_loader.data = final_df
                data_loader.update_categories()
                st.success(
                    f"Added {new_transactions} new transactions "
                    f"(skipped {len(new_df) - new_transactions} duplicates)",
                )
            else:
                # No existing data, just load the new data
                data_loader.data = new_df
                data_loader.update_categories()
                st.success(f"Loaded {len(new_df)} transactions")
                st.rerun()

        except Exception as e:  # noqa: BLE001
            st.error(f"Error importing file: {e!s}")
