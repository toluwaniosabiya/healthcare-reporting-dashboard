from __future__ import annotations

from pathlib import Path

import plotly.express as px
import streamlit as st

from src.queries.encounters import get_available_years
from src.queries.overview import (
    get_top_conditions,
    get_top_observation_types,
)

st.set_page_config(page_title="Clinical Insights", page_icon="🩺", layout="wide")

project_root = Path(__file__).resolve().parents[1]
db_path = project_root / "data" / "db" / "healthcare_reporting.db"

st.title("🩺 Clinical Insights")
st.markdown(
    """
    Clinical reporting view focused on condition prevalence, observation patterns,
    and the mix of numeric versus text-based observations.
    """
)

if not db_path.exists():
    st.error("Database not found.")
    st.info("Run `python -m scripts.run_pipeline` to build the reporting database.")
    st.stop()


@st.cache_data
def load_available_years(database_path: str) -> list[str]:
    return get_available_years(database_path)


@st.cache_data
def load_clinical_data(database_path: str, selected_years: tuple[str, ...]) -> dict:
    years = list(selected_years)
    return {
        "top_conditions": get_top_conditions(
            database_path, selected_years=years, limit=15
        ),
        "top_observation_types": get_top_observation_types(
            database_path, selected_years=years, limit=20
        ),
    }


available_years = load_available_years(str(db_path))

with st.sidebar:
    st.header("Filters")

    selected_years = st.multiselect(
        "Select year(s)",
        options=available_years,
        default=[],
        help="Leave empty to show all years.",
    )

    if selected_years:
        st.caption(f"Showing data for {len(selected_years)} selected year(s).")
    else:
        st.caption("Showing all years.")


data = load_clinical_data(str(db_path), tuple(selected_years))

df_top_conditions = data["top_conditions"]
df_top_observation_types = data["top_observation_types"]

if selected_years:
    st.info(f"Year filter applied: {', '.join(selected_years)}")
else:
    st.info("Showing all available years.")

row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.subheader("Top Conditions")
    if not df_top_conditions.empty:
        fig_conditions = px.bar(
            df_top_conditions,
            x="condition_count",
            y="condition_description",
            orientation="h",
            title="Top Conditions by Record Count",
        )
        fig_conditions.update_layout(
            xaxis_title="Condition Count",
            yaxis_title="Condition",
            yaxis={"categoryorder": "total ascending"},
        )
        st.plotly_chart(fig_conditions, use_container_width=True)
    else:
        st.info("No condition data available for the selected filter.")

with row1_col2:
    st.subheader("Top Observation Types")
    if not df_top_observation_types.empty:
        obs_summary = (
            df_top_observation_types.groupby("observation_description", as_index=False)[
                "observation_count"
            ]
            .sum()
            .sort_values("observation_count", ascending=False)
            .head(15)
        )

        fig_obs = px.bar(
            obs_summary,
            x="observation_count",
            y="observation_description",
            orientation="h",
            title="Top Observation Types by Count",
        )
        fig_obs.update_layout(
            xaxis_title="Observation Count",
            yaxis_title="Observation Type",
            yaxis={"categoryorder": "total ascending"},
        )
        st.plotly_chart(fig_obs, use_container_width=True)
    else:
        st.info("No observation data available for the selected filter.")

st.divider()

row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.subheader("Condition Summary Table")
    if not df_top_conditions.empty:
        st.dataframe(df_top_conditions, use_container_width=True)
    else:
        st.info("No condition summary available.")

with row2_col2:
    st.subheader("Observation Value Category Mix")
    if not df_top_observation_types.empty:
        value_mix = (
            df_top_observation_types.groupby("value_category", as_index=False)[
                "observation_count"
            ]
            .sum()
            .sort_values("observation_count", ascending=False)
        )

        fig_value_mix = px.pie(
            value_mix,
            names="value_category",
            values="observation_count",
            title="Observation Value Category Mix",
        )
        st.plotly_chart(fig_value_mix, use_container_width=True)

        with st.expander("View observation type summary table"):
            st.dataframe(df_top_observation_types, use_container_width=True)
    else:
        st.info("No observation value category data available.")
