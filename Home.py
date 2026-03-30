from __future__ import annotations

from pathlib import Path

import streamlit as st


st.set_page_config(
    page_title="Healthcare Reporting & EMR Insights Dashboard",
    page_icon="🏥",
    layout="wide",
)

project_root = Path(__file__).resolve().parent
db_path = project_root / "data" / "db" / "healthcare_reporting.db"

st.title("🏥 Healthcare Reporting & EMR Insights Dashboard")
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
