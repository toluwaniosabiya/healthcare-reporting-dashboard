from __future__ import annotations

from pathlib import Path

import plotly.express as px
import streamlit as st

# from io import StringIO

from src.queries.overview import (
    get_available_years,
    get_data_quality_summary,
    get_encounters_by_month,
    get_encounters_by_year,
    get_overview_metrics,
    get_top_conditions,
    get_top_encounter_types,
)

st.set_page_config(page_title="Executive Overview", page_icon="📊", layout="wide")

project_root = Path(__file__).resolve().parents[1]
db_path = project_root / "data" / "db" / "healthcare_reporting.db"

st.title("📊 Executive Overview")
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


@st.cache_data
def load_overview_data(database_path: str, selected_years: tuple[str, ...]) -> dict:
    years = list(selected_years)

    return {
        "metrics": get_overview_metrics(database_path, selected_years=years),
        "encounters_by_year": get_encounters_by_year(
            database_path, selected_years=years
        ),
        "encounters_by_month": get_encounters_by_month(
            database_path, selected_years=years
        ),
        "top_encounter_types": get_top_encounter_types(
            database_path, selected_years=years, limit=10
        ),
        "top_conditions": get_top_conditions(
            database_path, selected_years=years, limit=10
        ),
        "data_quality_summary": get_data_quality_summary(database_path),
    }


data = load_overview_data(str(db_path), tuple(selected_years))

df_metrics = data["metrics"]
df_encounters_by_year = data["encounters_by_year"]
df_encounters_by_month = data["encounters_by_month"]
df_top_encounter_types = data["top_encounter_types"]
df_top_conditions = data["top_conditions"]
df_data_quality_summary = data["data_quality_summary"]

if df_metrics.empty:
    st.warning("No overview data available.")
    st.stop()

metrics_row = df_metrics.iloc[0]

if selected_years:
    st.info(f"Year filter applied: {', '.join(selected_years)}")
else:
    st.info("Showing all available years.")

col1, col2, col3 = st.columns(3)
col4, col5, col6 = st.columns(3)

with col1:
    st.metric("Total Patients", f"{int(metrics_row['total_patients']):,}")

with col2:
    st.metric("Total Encounters", f"{int(metrics_row['total_encounters']):,}")

with col3:
    st.metric("Total Conditions", f"{int(metrics_row['total_conditions']):,}")

with col4:
    st.metric("Total Observations", f"{int(metrics_row['total_observations']):,}")

with col5:
    avg_encounters = metrics_row["avg_encounters_per_patient"]
    st.metric(
        "Avg Encounters / Patient",
        f"{avg_encounters:,.2f}" if avg_encounters is not None else "N/A",
    )

with col6:
    avg_duration = metrics_row["avg_encounter_duration_minutes"]
    st.metric(
        "Avg Encounter Duration (mins)",
        f"{avg_duration:,.2f}" if avg_duration is not None else "N/A",
    )

st.metric(
    "Total Data Quality Issues",
    f"{int(metrics_row['total_data_quality_issues']):,}",
)

st.divider()

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    # buffer = StringIO()
    # df_encounters_by_year.info(buf=buffer)
    # info_str = buffer.getvalue()
    # st.text(info_str)
    st.subheader("Encounters by Year")
    if not df_encounters_by_year.empty:
        df_encounters_by_year = df_encounters_by_year.copy()
        df_encounters_by_year["encounter_year"] = df_encounters_by_year[
            "encounter_year"
        ].astype(str)

        year_order = df_encounters_by_year["encounter_year"].tolist()

        fig_year = px.bar(
            df_encounters_by_year,
            x="encounter_year",
            y="encounter_count",
            category_orders={"encounter_year": year_order},
            title="Encounter Volume by Year",
        )
        fig_year.update_layout(
            xaxis_title="Year",
            yaxis_title="Encounter Count",
            xaxis={"type": "category"},
        )
        st.plotly_chart(fig_year, use_container_width=True)
    else:
        st.info("No yearly encounter data available for the selected filter.")

with chart_col2:
    st.subheader("Encounters by Month")
    if not df_encounters_by_month.empty:
        month_name_map = {
            "01": "Jan",
            "02": "Feb",
            "03": "Mar",
            "04": "Apr",
            "05": "May",
            "06": "Jun",
            "07": "Jul",
            "08": "Aug",
            "09": "Sep",
            "10": "Oct",
            "11": "Nov",
            "12": "Dec",
        }

        month_order = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]

        df_encounters_by_month = df_encounters_by_month.copy()
        df_encounters_by_month["month_label"] = (
            df_encounters_by_month["encounter_month"]
            .astype(str)
            .str.zfill(2)
            .map(month_name_map)
        )

        fig_month = px.bar(
            df_encounters_by_month,
            x="month_label",
            y="encounter_count",
            category_orders={"month_label": month_order},
            title="Encounter Volume by Month",
        )
        fig_month.update_layout(xaxis_title="Month", yaxis_title="Encounter Count")
        st.plotly_chart(fig_month, use_container_width=True)
    else:
        st.info("No monthly encounter data available for the selected filter.")

chart_col3, chart_col4 = st.columns(2)

with chart_col3:
    st.subheader("Top Encounter Types")
    if not df_top_encounter_types.empty:
        fig_encounter_types = px.bar(
            df_top_encounter_types,
            x="encounter_count",
            y="encounter_type",
            orientation="h",
            title="Top 10 Encounter Types",
        )
        fig_encounter_types.update_layout(
            xaxis_title="Encounter Count",
            yaxis_title="Encounter Type",
            yaxis={"categoryorder": "total ascending"},
        )
        st.plotly_chart(fig_encounter_types, use_container_width=True)
    else:
        st.info("No encounter type data available for the selected filter.")

with chart_col4:
    st.subheader("Top Conditions")
    if not df_top_conditions.empty:
        fig_conditions = px.bar(
            df_top_conditions,
            x="condition_count",
            y="condition_description",
            orientation="h",
            title="Top 10 Conditions",
        )
        fig_conditions.update_layout(
            xaxis_title="Condition Count",
            yaxis_title="Condition",
            yaxis={"categoryorder": "total ascending"},
        )
        st.plotly_chart(fig_conditions, use_container_width=True)
    else:
        st.info("No condition data available for the selected filter.")

st.divider()

st.subheader("Data Quality Summary")
if not df_data_quality_summary.empty:
    fig_dq = px.bar(
        df_data_quality_summary,
        x="issue_count",
        y="issue_type",
        color="source_table",
        orientation="h",
        title="Data Quality Issues by Type",
    )
    fig_dq.update_layout(
        xaxis_title="Issue Count",
        yaxis_title="Issue Type",
        yaxis={"categoryorder": "total ascending"},
    )
    st.plotly_chart(fig_dq, use_container_width=True)

    with st.expander("View data quality summary table"):
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
        """
    )
