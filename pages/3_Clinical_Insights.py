from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.queries.clinical import (
    get_numeric_observation_boxplot_data,
    get_numeric_observation_type_summary,
    get_top_conditions,
    get_top_observation_types,
    get_clinical_kpis,
)
from src.queries.encounters import get_available_years

from components.headers import render_section_header, render_title_header
from components.colors import bar_chart_color

st.set_page_config(page_title="Clinical Insights", page_icon="🩺", layout="wide")

project_root = Path(__file__).resolve().parents[1]
db_path = project_root / "data" / "db" / "healthcare_reporting.db"

# st.title("🩺 Clinical Insights")
render_title_header("🩺 Clinical Insights")
st.markdown(
    """
    Clinical reporting view focused on condition prevalence, observation patterns,
    and numeric observation behavior.
    """
)


def render_flashcard(title: str, value: str) -> None:
    st.markdown(
        f"""
        <div style="
            background-color: #F7F9FC;
            padding: 1rem 1.1rem;
            border-radius: 16px;
            border: 1px solid #e5e7eb;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
            min-height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
        ">
            <div style="
                font-size: 0.95rem;
                color: #6b7280;
                margin-bottom: 0.45rem;
                font-weight: 600;
            ">
                {title}
            </div>
            <div style="
                font-size: 2rem;
                font-weight: 700;
                color: #111827;
                line-height: 1.15;
            ">
                {value}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
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
        "clinical_kpis": get_clinical_kpis(database_path, selected_years=years),
        "top_conditions": get_top_conditions(
            database_path, selected_years=years, limit=15
        ),
        "top_observation_types": get_top_observation_types(
            database_path, selected_years=years, limit=30
        ),
        "numeric_observation_summary": get_numeric_observation_type_summary(
            database_path, selected_years=years, limit=15
        ),
        "numeric_observation_boxplot": get_numeric_observation_boxplot_data(
            database_path, selected_years=years, top_n=5
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

df_clinical_kpis = data["clinical_kpis"]
df_top_conditions = data["top_conditions"]
df_top_observation_types = data["top_observation_types"]
df_numeric_observation_summary = data["numeric_observation_summary"]
df_numeric_observation_boxplot = data["numeric_observation_boxplot"]

if selected_years:
    st.info(f"Year filter applied: {', '.join(selected_years)}")
else:
    st.info("Showing all available years.")

# -----------------------------
# Derivations used in multiple charts
# -----------------------------
df_condition_ratio = pd.DataFrame()
if not df_top_conditions.empty:
    df_condition_ratio = df_top_conditions.copy()
    df_condition_ratio["records_per_patient"] = (
        df_condition_ratio["condition_count"] / df_condition_ratio["patient_count"]
    ).round(2)

df_observation_summary = pd.DataFrame()
if not df_top_observation_types.empty:
    df_observation_summary = (
        df_top_observation_types.groupby("observation_description", as_index=False)[
            "observation_count"
        ]
        .sum()
        .sort_values("observation_count", ascending=False)
        .head(15)
    )

# -----------------------------
# kpi row 1
# -----------------------------
# st.markdown("### Clinical Overview")
render_section_header("Clinical Demographic Overview")

kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

if not df_clinical_kpis.empty:
    row = df_clinical_kpis.iloc[0]

    avg_pain = row["avg_pain_score"]
    avg_bmi = row["avg_bmi"]
    avg_weight = row["avg_weight"]
    avg_height = row["avg_height"]

    with kpi_col1:
        render_flashcard(
            "Average Pain Severity (0–10)",
            f"{avg_pain:,.2f}" if avg_pain is not None else "N/A",
        )

    with kpi_col2:
        render_flashcard(
            "Average BMI (kg/m<sup>2</sup>)",
            f"{avg_bmi:,.2f}" if avg_bmi is not None else "N/A",
        )

    with kpi_col3:
        render_flashcard(
            "Average Body Weight (kg)",
            f"{avg_weight:,.2f}" if avg_weight is not None else "N/A",
        )

    with kpi_col4:
        render_flashcard(
            "Average Body Height (cm)",
            f"{avg_height:,.2f}" if avg_height is not None else "N/A",
        )

st.divider()

# -----------------------------
# Row 1
# -----------------------------
render_section_header("Charts")
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.subheader("Top Conditions by Record Count")
    if not df_top_conditions.empty:
        fig_conditions = px.bar(
            df_top_conditions,
            x="condition_count",
            y="condition_description",
            orientation="h",
            title="Top Conditions by Record Count",
            color_discrete_sequence=bar_chart_color,
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
    st.subheader("Top Conditions by Distinct Patients")
    if not df_top_conditions.empty:
        fig_condition_patients = px.bar(
            df_top_conditions,
            x="patient_count",
            y="condition_description",
            orientation="h",
            title="Top Conditions by Distinct Patient Count",
            color_discrete_sequence=bar_chart_color,
        )
        fig_condition_patients.update_layout(
            xaxis_title="Patient Count",
            yaxis_title="Condition",
            yaxis={"categoryorder": "total ascending"},
        )
        st.plotly_chart(fig_condition_patients, use_container_width=True)
    else:
        st.info("No condition patient-count data available for the selected filter.")

# -----------------------------
# Row 2
# -----------------------------
row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.subheader("Top Observation Types")
    if not df_observation_summary.empty:
        fig_obs = px.bar(
            df_observation_summary,
            x="observation_count",
            y="observation_description",
            orientation="h",
            title="Top Observation Types by Count",
            color_discrete_sequence=bar_chart_color,
        )
        fig_obs.update_layout(
            xaxis_title="Observation Count",
            yaxis_title="Observation Type",
            yaxis={"categoryorder": "total ascending"},
        )
        st.plotly_chart(fig_obs, use_container_width=True)
    else:
        st.info("No observation data available for the selected filter.")

with row2_col2:
    st.subheader("Numeric Observation Summary Scatter")
    if not df_numeric_observation_summary.empty:
        fig_scatter = px.scatter(
            df_numeric_observation_summary,
            x="observation_count",
            y="avg_value",
            size="observation_count",
            hover_name="observation_description",
            title="Average Numeric Value vs Observation Volume",
            color_discrete_sequence=["#385001"],
        )
        fig_scatter.update_layout(
            xaxis_title="Observation Count",
            yaxis_title="Average Numeric Value",
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        st.caption(
            "Each point is a numeric observation type. Interpret average values cautiously across different units."
        )
    else:
        st.info("No numeric observation summary available for the selected filter.")

# -----------------------------
# Row 3
# -----------------------------
row3_col1, row3_col2 = st.columns(2)

with row3_col1:
    st.subheader("Numeric Observation Boxplot")
    if not df_numeric_observation_boxplot.empty:
        fig_box = px.box(
            df_numeric_observation_boxplot,
            x="observation_description",
            y="value_numeric",
            title="Distribution of Numeric Values for Top Observation Types",
            points=False,
            color_discrete_sequence=["#385001"],
        )
        fig_box.update_layout(
            xaxis_title="Observation Type",
            yaxis_title="Numeric Value",
        )
        st.plotly_chart(fig_box, use_container_width=True)
        st.caption(
            "Boxplot shown for the top numeric observation types by frequency. Values may span different units."
        )
    else:
        st.info(
            "No numeric observation boxplot data available for the selected filter."
        )

with row3_col2:
    st.subheader("Condition Record Intensity")
    if not df_condition_ratio.empty:
        fig_ratio = px.bar(
            df_condition_ratio,
            x="records_per_patient",
            y="condition_description",
            orientation="h",
            title="Condition Records per Distinct Patient",
            color_discrete_sequence=bar_chart_color,
        )
        fig_ratio.update_layout(
            xaxis_title="Records per Patient",
            yaxis_title="Condition",
            yaxis={"categoryorder": "total ascending"},
        )
        st.plotly_chart(fig_ratio, use_container_width=True)
    else:
        st.info("No condition intensity data available for the selected filter.")

st.divider()

render_section_header("Tables")
with st.expander("View clinical summary tables"):
    st.markdown("**Top conditions**")
    st.dataframe(df_top_conditions, use_container_width=True)

    st.markdown("**Top observation types**")
    st.dataframe(df_top_observation_types, use_container_width=True)

    st.markdown("**Numeric observation summary**")
    st.dataframe(df_numeric_observation_summary, use_container_width=True)
