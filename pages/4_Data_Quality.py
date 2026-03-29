from __future__ import annotations

from pathlib import Path

import plotly.express as px
import streamlit as st

from src.queries.encounters import get_available_years
from src.queries.overview import (
    get_data_quality_summary,
    get_top_observation_types,
)

from components.headers import render_section_header, render_title_header
from components.colors import bar_chart_color

st.set_page_config(page_title="Data Quality", page_icon="🧪", layout="wide")

project_root = Path(__file__).resolve().parents[1]
db_path = project_root / "data" / "db" / "healthcare_reporting.db"

# st.title("🧪 Data Quality")
render_title_header("🧪 Data Quality")
st.markdown(
    """
    Data quality and reporting-readiness view focused on audit issues and observation structure.
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
def load_data_quality_data(database_path: str, selected_years: tuple[str, ...]) -> dict:
    years = list(selected_years)
    return {
        "data_quality_summary": get_data_quality_summary(database_path),
        "top_observation_types": get_top_observation_types(
            database_path, selected_years=years, limit=50
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
        st.caption(
            f"Showing observation structure for {len(selected_years)} selected year(s)."
        )
    else:
        st.caption("Showing all years.")


data = load_data_quality_data(str(db_path), tuple(selected_years))

df_data_quality_summary = data["data_quality_summary"]
df_top_observation_types = data["top_observation_types"]

if selected_years:
    st.info(
        f"Year filter applied to observation structure: {', '.join(selected_years)}. "
        "Audit summary remains global for now."
    )
else:
    st.info("Showing all available years. Audit summary remains global.")

render_section_header("Charts")
row1_col1, row1_col2 = st.columns(2)

if df_data_quality_summary["issue_type"].nunique() > 1:
    with row1_col1:
        st.subheader("Data Quality Issues by Type")
        if not df_data_quality_summary.empty:
            fig_dq = px.bar(
                df_data_quality_summary,
                x="issue_count",
                y="issue_type",
                color="source_table",
                orientation="h",
                title="Data Quality Issues by Type",
                color_discrete_sequence=bar_chart_color,
            )
            fig_dq.update_layout(
                xaxis_title="Issue Count",
                yaxis_title="Issue Type",
                yaxis={"categoryorder": "total ascending"},
            )
            st.plotly_chart(fig_dq, use_container_width=True)
        else:
            st.success("No data quality issues found.")

if df_data_quality_summary["source_table"].nunique() > 1:
    with row1_col2:
        st.subheader("Issues by Severity")
        if not df_data_quality_summary.empty:
            severity_summary = (
                df_data_quality_summary.groupby("issue_severity", as_index=False)[
                    "issue_count"
                ]
                .sum()
                .sort_values("issue_count", ascending=False)
            )

            fig_severity = px.bar(
                severity_summary,
                x="issue_severity",
                y="issue_count",
                title="Data Quality Issues by Severity",
                color_discrete_sequence=bar_chart_color,
            )
            fig_severity.update_layout(
                xaxis_title="Issue Severity",
                yaxis_title="Issue Count",
                xaxis={"type": "category"},
            )
            st.plotly_chart(fig_severity, use_container_width=True)
        else:
            st.success("No severity distribution to display.")

st.divider()

st.subheader("Observation Structure Profile")
if not df_top_observation_types.empty:
    value_mix = (
        df_top_observation_types.groupby("value_category", as_index=False)[
            "observation_count"
        ]
        .sum()
        .sort_values("observation_count", ascending=False)
    )

    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        fig_value_mix = px.pie(
            value_mix,
            names="value_category",
            values="observation_count",
            title="Observation Value Type Distribution",
            color_discrete_sequence=[
                "#01762C",  # green for predominant class
                "#0EDAC2",  # teal
                "#C83B3B",  # lime
                "#F59E0B",  # amber
                "#8B5CF6",  # violet
                "#94A3B8",  # slate for Others
            ],
        )
        st.plotly_chart(fig_value_mix, use_container_width=True)

    with row2_col2:
        fig_value_bar = px.bar(
            value_mix,
            x="value_category",
            y="observation_count",
            title="Observation Counts by Value Type",
            color_discrete_sequence=bar_chart_color,
        )
        fig_value_bar.update_layout(
            xaxis_title="Value Type",
            yaxis_title="Observation Count",
            xaxis={"type": "category"},
        )
        st.plotly_chart(fig_value_bar, use_container_width=True)
else:
    st.info("No observation structure data available for the selected filter.")

st.divider()

render_section_header("Tables")
with st.expander("View data quality summary table"):
    if not df_data_quality_summary.empty:
        st.dataframe(df_data_quality_summary, use_container_width=True)
    else:
        st.info("No data quality summary available.")

with st.expander("View observation structure table"):
    if not df_top_observation_types.empty:
        st.dataframe(df_top_observation_types, use_container_width=True)
    else:
        st.info("No observation structure table available.")
