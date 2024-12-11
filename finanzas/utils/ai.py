"""AI-powered categorization functionality."""
from __future__ import annotations

import openai
import pandas as pd
import streamlit as st


def get_openai_suggestions(
    rows: pd.DataFrame,
    existing_categories: set[str],
    existing_subcategories: dict[str, set[str]],
    *,
    use_existing_only: bool = False,
) -> list[dict[str, str]]:
    """Get category and subcategory suggestions from OpenAI for selected rows."""
    api_key = st.secrets.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not found in secrets")

    context = "You are a financial categorization assistant. "
    if use_existing_only:
        context += f"\nExisting categories: {', '.join(existing_categories)}"
        context += "\nExisting subcategories per category:"
        for cat, subcats in existing_subcategories.items():
            context += f"\n- {cat}: {', '.join(subcats)}"
        context += "\nPlease only use these existing categories and subcategories."

    entries = (
        rows[["Concept", "Amount"]]
        .apply(
            lambda x: f"- Concept: {x['Concept']}, Amount: {x['Amount']:,.2f}€",
            axis=1,
        )
        .tolist()
    )

    prompt = (
        f"{context}\n\n"
        "Please suggest appropriate categories and subcategories for these financial entries:\n"
        f"{chr(10).join(entries)}\n\n"
        "Respond in this format for each entry:\n"
        "1. Category: [category], Subcategory: [subcategory]"
    )

    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        if not response.choices or not response.choices[0].message or not response.choices[0].message.content:
            st.error("Received empty response from OpenAI")
            return []

        suggestions = []
        lines = response.choices[0].message.content.strip().split("\n")

        for line in lines:
            if not line.strip():
                continue

            try:
                cat_part = line.split("Category:")[1].split(",")[0].strip()
                subcat_part = line.split("Subcategory:")[1].strip()
                suggestions.append(
                    {
                        "Category": cat_part,
                        "Subcategory": subcat_part,
                    }
                )
            except IndexError:
                continue

        return suggestions

    except Exception as e:
        st.error(f"Error getting suggestions from OpenAI: {str(e)}")
        return []


def apply_suggestions_to_similar(
    df: pd.DataFrame,
    concept: str,
    category: str,
    subcategory: str,
) -> pd.DataFrame:
    """Find entries with identical concepts and apply the same categorization."""
    mask = df["Concept"] == concept
    df.loc[mask, "Category"] = category
    df.loc[mask, "Subcategory"] = subcategory
    return df 