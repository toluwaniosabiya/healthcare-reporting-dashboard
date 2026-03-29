from __future__ import annotations

from pathlib import Path

import plotly.express as px
import streamlit as st

from src.queries.encounters import (
    get_available_years,
    get_encounter_class_summary,
    get_encounter_duration_by_type,
    get_encounter_duration_distribution,
    get_encounter_year_month_trend,
    get_encounters_by_month,
    get_encounters_by_year,
    get_top_encounter_types,
    get_top_organizations,
)

st.set_page_config(page_title="Encounter Activity", page_icon="📅", layout="wide")

project_root = Path(__file__).resolve().parents[1]
db_path = project_root / "data" / "db" / "healthcare_reporting.db"

st.title("📅 Encounter Activity")
st.markdown(
    """
    Operational reporting view focused on encounter volume, service mix, encounter class,
    duration patterns, and organizational activity.
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
def load_encounter_activity_data(
    database_path: str, selected_years: tuple[str, ...]
) -> dict:
    years = list(selected_years)
    return {
        "encounters_by_year": get_encounters_by_year(
            database_path, selected_years=years
        ),
        "encounters_by_month": get_encounters_by_month(
            database_path, selected_years=years
        ),
        "encounter_year_month_trend": get_encounter_year_month_trend(
            database_path, selected_years=years
        ),
        "top_encounter_types": get_top_encounter_types(
            database_path, selected_years=years, limit=15
        ),
        "encounter_class_summary": get_encounter_class_summary(
            database_path, selected_years=years, limit=15
        ),
        "encounter_duration_by_type": get_encounter_duration_by_type(
            database_path, selected_years=years, limit=15
        ),
        "encounter_duration_distribution": get_encounter_duration_distribution(
            database_path, selected_years=years
        ),
        "top_organizations": get_top_organizations(
            database_path, selected_years=years, limit=10
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


data = load_encounter_activity_data(str(db_path), tuple(selected_years))

df_encounters_by_year = data["encounters_by_year"]
df_encounters_by_month = data["encounters_by_month"]
df_year_month_trend = data["encounter_year_month_trend"]
df_top_encounter_types = data["top_encounter_types"]
df_encounter_class_summary = data["encounter_class_summary"]
df_duration_by_type = data["encounter_duration_by_type"]
df_duration_distribution = data["encounter_duration_distribution"]
df_top_organizations = data["top_organizations"]

if selected_years:
    st.info(f"Year filter applied: {', '.join(selected_years)}")
else:
    st.info("Showing all available years.")

row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.subheader("Encounter Volume by Year")
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

with row1_col2:
    st.subheader("Encounter Year-Month Trend")
    if not df_year_month_trend.empty:
        fig_trend = px.line(
            df_year_month_trend,
            x="encounter_year_month",
            y="encounter_count",
            markers=True,
            title="Encounter Trend by Year-Month",
        )
        fig_trend.update_layout(
            xaxis_title="Year-Month",
            yaxis_title="Encounter Count",
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("No year-month trend data available for the selected filter.")

row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.subheader("Encounter Volume by Month")
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
            title="Seasonality: Encounter Volume by Month",
        )
        fig_month.update_layout(
            xaxis_title="Month",
            yaxis_title="Encounter Count",
            xaxis={"type": "category"},
        )
        st.plotly_chart(fig_month, use_container_width=True)
    else:
        st.info("No monthly encounter data available for the selected filter.")

with row2_col2:
    st.subheader("Encounter Class Distribution")
    if not df_encounter_class_summary.empty:
        fig_class = px.bar(
            df_encounter_class_summary,
            x="encounter_count",
            y="encounter_class",
            orientation="h",
            title="Encounter Count by Class",
        )
        fig_class.update_layout(
            xaxis_title="Encounter Count",
            yaxis_title="Encounter Class",
            yaxis={"categoryorder": "total ascending"},
        )
        st.plotly_chart(fig_class, use_container_width=True)
    else:
        st.info("No encounter class data available for the selected filter.")

row3_col1, row3_col2 = st.columns(2)

with row3_col1:
    st.subheader("Top Encounter Types")
    if not df_top_encounter_types.empty:
        fig_types = px.bar(
            df_top_encounter_types,
            x="encounter_count",
            y="encounter_type",
            orientation="h",
            title="Top Encounter Types",
        )
        fig_types.update_layout(
            xaxis_title="Encounter Count",
            yaxis_title="Encounter Type",
            yaxis={"categoryorder": "total ascending"},
        )
        st.plotly_chart(fig_types, use_container_width=True)
    else:
        st.info("No encounter type data available for the selected filter.")

with row3_col2:
    st.subheader("Average Duration by Encounter Type")
    if not df_duration_by_type.empty:
        fig_duration_type = px.bar(
            df_duration_by_type,
            x="avg_duration_minutes",
            y="encounter_type",
            orientation="h",
            title="Average Encounter Duration by Type",
        )
        fig_duration_type.update_layout(
            xaxis_title="Average Duration (mins)",
            yaxis_title="Encounter Type",
            yaxis={"categoryorder": "total ascending"},
        )
        st.plotly_chart(fig_duration_type, use_container_width=True)
    else:
        st.info("No encounter duration-by-type data available for the selected filter.")

row4_col1, row4_col2 = st.columns(2)

with row4_col1:
    st.subheader("Encounter Duration Distribution")
    if not df_duration_distribution.empty:
        fig_duration_dist = px.histogram(
            df_duration_distribution,
            x="encounter_duration_minutes",
            nbins=30,
            title="Distribution of Encounter Durations",
        )
        fig_duration_dist.update_layout(
            xaxis_title="Encounter Duration (mins)",
            yaxis_title="Frequency",
        )
        st.plotly_chart(fig_duration_dist, use_container_width=True)
    else:
        st.info("No encounter duration data available for the selected filter.")

with row4_col2:
    st.subheader("Top Organizations by Encounter Volume")
    if not df_top_organizations.empty:
        fig_orgs = px.bar(
            df_top_organizations,
            x="encounter_count",
            y="organization_name",
            orientation="h",
            title="Top Organizations by Encounter Count",
        )
        fig_orgs.update_layout(
            xaxis_title="Encounter Count",
            yaxis_title="Organization",
            yaxis={"categoryorder": "total ascending"},
        )
        st.plotly_chart(fig_orgs, use_container_width=True)
    else:
        st.info("No organization data available for the selected filter.")

with st.expander("View encounter activity tables"):
    st.markdown("**Encounter class summary**")
    st.dataframe(df_encounter_class_summary, use_container_width=True)

    st.markdown("**Top encounter types**")
    st.dataframe(df_top_encounter_types, use_container_width=True)

    st.markdown("**Average duration by encounter type**")
    st.dataframe(df_duration_by_type, use_container_width=True)

    st.markdown("**Top organizations**")
    st.dataframe(df_top_organizations, use_container_width=True)
