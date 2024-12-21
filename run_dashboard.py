"""Launch the financial dashboard."""

import logging

import streamlit as st

from finanzas.data.loader import DataLoader

PAGES = {
    "Dataset": st.Page("finanzas/ui/dataset.py", title="Data", icon="🗃️"),
    "Dashboard": st.Page("finanzas/ui/dashboard.py", title="Analysis", icon="📊"),
}

logging.basicConfig(level=logging.WARNING)
# logging.getLogger("finanzas.ui.ai_categorization").setLevel(logging.DEBUG)
# logging.getLogger("finanzas.utils.ai").setLevel(logging.DEBUG)


def main() -> None:
    """Run the Streamlit app."""
    st.set_page_config(page_title="Financial Analysis", page_icon="", layout="wide")

    if "data_loader" not in st.session_state:
        st.session_state.data_loader = DataLoader()
    pg = st.navigation({"Menu": list(PAGES.values())})
    pg.run()


if __name__ == "__main__":
    main()
