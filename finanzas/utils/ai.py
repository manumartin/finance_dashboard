"""AI-powered categorization functionality."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

import openai
import streamlit as st

if TYPE_CHECKING:
    import pandas as pd

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.propagate = False


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
        msg = "OpenAI API key not found in secrets"
        raise ValueError(msg)

    # Build a more structured context
    context: dict[str, str | dict] = {
        "role": "You are a financial categorization assistant.",
        "task": "Categorize financial transactions into appropriate categories and subcategories.",
    }

    if use_existing_only:
        context["constraints"] = {
            "categories": list(existing_categories),
            "category_subcategories": {cat: list(subcats) for cat, subcats in existing_subcategories.items()},
            "important": "You must ONLY use categories and subcategories from the provided lists. \
                Don't create new ones.",
        }

    # Format transactions for the prompt
    transactions = [{"concept": row["Concept"], "amount": f"{row['Amount']:,.2f}€"} for _, row in rows.iterrows()]

    prompt = {
        "context": context,
        "transactions": transactions,
    }

    logger.debug("Starting OpenAI suggestions request")
    logger.debug("Processing %d transactions", len(rows))

    try:
        # Log the API request details
        logger.debug("Request details:")
        logger.debug(json.dumps(prompt, indent=2))

        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a financial categorization assistant. "
                        "You MUST return responses in valid JSON format only. "
                        "Each response should be a json with a list of categorization items, like this:"
                        "{\n"
                        '  "categorizations": [\n'
                        "    {\n"
                        '      "category": "Food",\n'
                        '      "subcategory": "Groceries"\n'
                        "    },\n"
                        "    {\n"
                        '      "category": "Transport",\n'
                        '    "subcategory": "Public Transport"\n'
                        "  }\n"
                        "]"
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(prompt, indent=2),
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )

        if not response.choices or not response.choices[0].message or not response.choices[0].message.content:
            st.error("Received empty response from OpenAI")
            return []

        logger.debug("OpenAI API response:")
        logger.debug(json.dumps(response.choices[0].message.content, indent=2))

        # Parse JSON response
        try:
            result = json.loads(response.choices[0].message.content)
            suggestions = [
                {"Category": item["category"], "Subcategory": item["subcategory"]} for item in result["categorizations"]
            ]
        except (json.JSONDecodeError, KeyError):
            logger.exception("Failed to parse OpenAI response")
            return []

        logger.debug("Processed suggestions:")
        logger.debug(json.dumps(suggestions, indent=2))

    except openai.OpenAIError:
        logger.exception("OpenAI API error")
        raise
    except Exception:
        logger.exception("Unexpected error in get_openai_suggestions")
        raise
    else:
        logger.debug("OpenAI suggestions request completed successfully")
        return suggestions


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
