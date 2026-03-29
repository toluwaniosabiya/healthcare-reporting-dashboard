from __future__ import annotations

from pathlib import Path

import plotly.express as px
import streamlit as st
import pandas as pd

from src.queries.encounters import (
    get_available_years,
    get_encounter_class_summary,
    get_top_encounter_types,
    get_top_organizations,
)
from src.queries.overview import (
    get_data_quality_summary,
    get_overview_metrics,
    get_patient_utilization_pct,
    get_top_conditions,
)
from components.headers import render_section_header, render_title_header
from components.colors import bar_chart_color

st.set_page_config(page_title="Executive Overview", page_icon="📊", layout="wide")

project_root = Path(__file__).resolve().parents[1]
db_path = project_root / "data" / "db" / "healthcare_reporting.db"

render_title_header("📊 Executive Overview")
# st.title("📊 Executive Overview")
st.markdown(
    """
    A high-level summary of operational activity, clinical context, and data quality
    from the FHIR-derived reporting database.
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
def load_overview_data(database_path: str, selected_years: tuple[str, ...]) -> dict:
    years = list(selected_years)
    return {
        "metrics": get_overview_metrics(database_path, selected_years=years),
        "top_encounter_types": get_top_encounter_types(
            database_path, selected_years=years, limit=10
        ),
        "top_conditions": get_top_conditions(
            database_path, selected_years=years, limit=10
        ),
        "encounter_class_summary": get_encounter_class_summary(
            database_path, selected_years=years
        ),
        "top_organizations": get_top_organizations(
            database_path, selected_years=years, limit=10
        ),
        "data_quality_summary": get_data_quality_summary(database_path),
    }


@st.cache_data
def load_patient_utilization(
    database_path: str,
    threshold: int,
    selected_years: tuple[str, ...],
):
    years = list(selected_years)
    return get_patient_utilization_pct(
        database_path,
        threshold=threshold,
        selected_years=years,
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


data = load_overview_data(str(db_path), tuple(selected_years))

df_metrics = data["metrics"]
df_top_encounter_types = data["top_encounter_types"]
df_top_conditions = data["top_conditions"]
df_encounter_class_summary = data["encounter_class_summary"]
df_top_organizations = data["top_organizations"]
df_data_quality_summary = data["data_quality_summary"]

if df_metrics.empty:
    st.warning("No overview data available.")
    st.stop()

metrics_row = df_metrics.iloc[0]

if selected_years:
    st.info(f"Year filter applied: {', '.join(selected_years)}")
else:
    st.info("Showing all available years.")

# -----------------------------
# Row 1 KPI flashcards
# -----------------------------
render_section_header("Overview")
row1_col1, row1_col2, row1_col3, row1_col4 = st.columns(4)

with row1_col1:
    render_flashcard("Total Patients", f"{int(metrics_row['total_patients']):,}")

with row1_col2:
    render_flashcard("Total Encounters", f"{int(metrics_row['total_encounters']):,}")

with row1_col3:
    render_flashcard("Total Conditions", f"{int(metrics_row['total_conditions']):,}")

with row1_col4:
    render_flashcard(
        "Total Observations", f"{int(metrics_row['total_observations']):,}"
    )

st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

# -----------------------------
# Row 2 KPI flashcards
# -----------------------------
row2_col1, row2_col2, row2_col3, row2_col4 = st.columns(4)

avg_encounters = metrics_row["avg_encounters_per_patient"]
avg_duration = metrics_row["avg_encounter_duration_minutes"]
completeness_pct = metrics_row["encounter_data_completeness_pct"]

with row2_col1:
    render_flashcard(
        "Avg Encounters / Patient",
        f"{avg_encounters:,.2f}" if avg_encounters is not None else "N/A",
    )

with row2_col2:
    render_flashcard(
        "Avg Encounter Duration (mins)",
        f"{avg_duration:,.2f}" if avg_duration is not None else "N/A",
    )

with row2_col3:
    render_flashcard(
        "Total Data Quality Issues",
        f"{int(metrics_row['total_data_quality_issues']):,}",
    )

with row2_col4:
    render_flashcard(
        "Encounter Data Completeness (%)",
        f"{completeness_pct:,.2f}%" if completeness_pct is not None else "N/A",
    )

st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

# -----------------------------
# Row 3 centered utilization KPI + slider
# -----------------------------
left_spacer, center_col, right_spacer = st.columns([1, 2, 1])

with center_col:
    st.markdown("### Patient Utilization")
    utilization_threshold = st.slider(
        "Patients with at least this many encounters",
        min_value=0,
        max_value=30,
        value=5,
        step=1,
    )

    df_utilization = load_patient_utilization(
        str(db_path),
        threshold=utilization_threshold,
        selected_years=tuple(selected_years),
    )

    utilization_value = "N/A"
    if not df_utilization.empty:
        utilization_pct = df_utilization.iloc[0]["patient_utilization_pct"]
        utilization_value = (
            f"{utilization_pct:,.2f}%" if utilization_pct is not None else "N/A"
        )

    render_flashcard(
        f"Patient Utilization (%): ≥ {utilization_threshold} Encounters",
        utilization_value,
    )

st.divider()

# -----------------------------
# Executive charts
# -----------------------------
render_section_header("Charts")
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("Top Encounter Types")
    if not df_top_encounter_types.empty:
        fig_encounter_types = px.bar(
            df_top_encounter_types,
            x="encounter_count",
            y="encounter_type",
            orientation="h",
            title="Top 10 Encounter Types",
            color_discrete_sequence=bar_chart_color,
        )
        fig_encounter_types.update_layout(
            xaxis_title="Encounter Count",
            yaxis_title="Encounter Type",
            yaxis={"categoryorder": "total ascending"},
        )
        st.plotly_chart(fig_encounter_types, use_container_width=True)
    else:
        st.info("No encounter type data available for the selected filter.")

with chart_col2:
    st.subheader("Top Conditions")
    if not df_top_conditions.empty:
        fig_conditions = px.bar(
            df_top_conditions,
            x="condition_count",
            y="condition_description",
            orientation="h",
            title="Top 10 Conditions",
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

chart_col3, chart_col4 = st.columns(2)

with chart_col3:
    st.subheader("Encounter Class Distribution")
    if not df_encounter_class_summary.empty:
        df_class_donut = df_encounter_class_summary.copy()

        df_class_donut["encounter_class"] = df_class_donut["encounter_class"].fillna(
            "Unknown"
        )

        df_class_donut = df_class_donut.sort_values(
            "encounter_count", ascending=False
        ).reset_index(drop=True)

        top_n = 5

        if len(df_class_donut) > top_n:
            df_top = df_class_donut.head(top_n).copy()
            others_count = df_class_donut.iloc[top_n:]["encounter_count"].sum()

            df_class_donut = df_top.copy()

            if others_count > 0:
                df_class_donut = pd.concat(
                    [
                        df_class_donut,
                        pd.DataFrame(
                            {
                                "encounter_class": ["Others"],
                                "encounter_count": [others_count],
                            }
                        ),
                    ],
                    ignore_index=True,
                )

        fig_class = px.pie(
            df_class_donut,
            names="encounter_class",
            values="encounter_count",
            hole=0.55,
            title="Encounter Class Distribution",
            color_discrete_sequence=[
                "#01762C",  # green for predominant class
                "#0EDAC2",  # teal
                "#C83B3B",  # lime
                "#F59E0B",  # amber
                "#8B5CF6",  # violet
                "#94A3B8",  # slate for Others
            ],
        )
        fig_class.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_class, use_container_width=True)
    else:
        st.info("No encounter class data available for the selected filter.")

with chart_col4:
    st.subheader("Top Organizations")
    if not df_top_organizations.empty:
        fig_orgs = px.bar(
            df_top_organizations,
            x="encounter_count",
            y="organization_name",
            orientation="h",
            title="Top Organizations by Encounter Volume",
            color_discrete_sequence=bar_chart_color,
        )
        fig_orgs.update_layout(
            xaxis_title="Encounter Count",
            yaxis_title="Organization",
            yaxis={"categoryorder": "total ascending"},
        )
        st.plotly_chart(fig_orgs, use_container_width=True)
    else:
        st.info("No organization data available for the selected filter.")

# -----------------------------
# Conditional data quality chart
# -----------------------------
if (
    not df_data_quality_summary.empty
    and df_data_quality_summary["issue_type"].nunique() > 1
):
    st.divider()
    st.subheader("Data Quality Issues by Type")

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

st.divider()

render_section_header("Data Quality")
st.subheader("Data Quality Summary")
if not df_data_quality_summary.empty:
    with st.expander("View data quality summary table", expanded=False):
        st.dataframe(df_data_quality_summary, use_container_width=True)
else:
    st.success("No data quality issues found in the current audit output.")

with st.expander("Metric definitions"):
    st.markdown(
        """
        - **Total Patients**: Distinct patients with encounters in the selected year(s), or all patients in the unfiltered overview  
        - **Total Encounters**: Count of encounters in the selected year(s), or all encounters in the unfiltered overview  
        - **Total Conditions**: Count of conditions using recorded or onset year in the selected year(s)  
        - **Total Observations**: Count of observations in the selected year(s)  
        - **Avg Encounters / Patient**: Total encounters divided by distinct patients in encounters for the selected year(s)  
        - **Avg Encounter Duration (mins)**: Mean duration of encounters with valid start and end timestamps  
        - **Total Data Quality Issues**: Count of audit records generated by quality checks  
        - **Encounter Data Completeness (%)**: Percentage of encounters with non-null start, end, and duration fields  
        - **Patient Utilization (%)**: Percentage of patients with at least the selected number of encounters in the current filter scope  
        """
    )
