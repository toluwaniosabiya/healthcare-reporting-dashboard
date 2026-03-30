from __future__ import annotations

from pathlib import Path

import streamlit as st

from components.headers import render_title_header


st.set_page_config(
    page_title="Healthcare Reporting & EMR Insights Dashboard",
    page_icon="🏥",
    layout="wide",
)

project_root = Path(__file__).resolve().parent
db_path = project_root / "data" / "db" / "healthcare_reporting.db"

# st.title("🏥 Healthcare Reporting & EMR Insights Dashboard")
render_title_header("🏥 Healthcare Reporting & EMR Insights Dashboard")
st.markdown(
    """
    This dashboard demonstrates how FHIR-based clinical data can be transformed into a
    relational reporting model for operational, clinical, and data quality analysis.

    Use the pages in the left sidebar to explore:
    - **Executive Overview**
    - **Encounter Activity**
    - **Clinical Insights**
    - **Data Quality**
    """
)

if db_path.exists():
    st.success(f"Connected to database: `{db_path.name}`")
else:
    st.error("Database not found.")
    st.info(
        "Run the pipeline first to build the SQLite reporting database:\n\n"
        "`python -m scripts.run_pipeline`"
    )
    st.stop()

st.markdown("---")

st.markdown(
    """
    ## FHIR-to-Reporting Operating Model

    This dashboard is built on a structured 7-layer operating model that transforms raw FHIR data into
    trusted, decision-ready insights.
    """
)

# # Center the image
# col1, col2, col3 = st.columns([1, 6, 1])

# with col2:
st.image("assets/images/operating-model.png", use_container_width=True)

st.markdown("---")

# st.markdown(
#     """
#     ### What this demonstrates
#     - End-to-end health data transformation (FHIR → SQL → Dashboard)
#     - Data quality as a first-class reporting component
#     - Stakeholder-focused analytics design
#     - Governed, explainable reporting layer
#     """
# )

col1, col2 = st.columns(2)

with col1:
    st.subheader("What this project shows")
    st.markdown(
        """
        - Ingestion of raw FHIR NDJSON resources
        - Transformation into relational tables
        - SQL-backed reporting views
        - Data quality auditing
        - Product-style dashboarding for healthcare reporting
        """
    )

with col2:
    st.subheader("Core data model")
    st.markdown(
        """
        - **patients**
        - **encounters**
        - **conditions**
        - **observations**
        - **data_quality_audit**
        """
    )

st.divider()

st.subheader("How to navigate")
st.markdown(
    """
    Start with **Executive Overview** for the KPI snapshot, then move into:
    - **Encounter Activity** for operational reporting
    - **Clinical Insights** for conditions and observations
    - **Data Quality** for audit visibility
    """
)
