from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


def get_connection(db_path: str | Path) -> sqlite3.Connection:
    """
    Return a SQLite connection for querying the reporting database.
    """
    db_path = Path(db_path)

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    conn = sqlite3.connect(db_path)
    return conn


def run_query(
    db_path: str | Path,
    query: str,
    params: tuple | None = None,
) -> pd.DataFrame:
    """
    Execute a SQL query and return the result as a pandas DataFrame.
    """
    conn = get_connection(db_path)

    try:
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()


def _build_in_clause_placeholders(values: list[str]) -> str:
    """
    Build a comma-separated placeholder string for SQL IN clauses.

    Example:
        ['2020', '2021'] -> '?, ?'
    """
    return ", ".join(["?"] * len(values))


def get_available_years(db_path: str | Path) -> list[str]:
    query = """
        SELECT DISTINCT substr(encounter_start, 1, 4) AS encounter_year
        FROM encounters
        WHERE encounter_start IS NOT NULL
        ORDER BY encounter_year
    """
    df = run_query(db_path, query)
    return df["encounter_year"].dropna().astype(str).tolist()


def get_overview_metrics(
    db_path: str | Path, selected_years: list[str] | None = None
) -> pd.DataFrame:
    """
    Return overview metrics.
    If selected_years is provided, metrics are filtered by year-aware event tables.
    """
    if not selected_years:
        query = """
            SELECT * FROM vw_overview_metrics
        """
        return run_query(db_path, query)

    placeholders = _build_in_clause_placeholders(selected_years)

    query = f"""
        SELECT
            (
                SELECT COUNT(DISTINCT patient_id)
                FROM encounters
                WHERE substr(encounter_start, 1, 4) IN ({placeholders})
            ) AS total_patients,
            (
                SELECT COUNT(*)
                FROM encounters
                WHERE substr(encounter_start, 1, 4) IN ({placeholders})
            ) AS total_encounters,
            (
                SELECT COUNT(*)
                FROM conditions
                WHERE substr(COALESCE(recorded_datetime, onset_datetime), 1, 4) IN ({placeholders})
            ) AS total_conditions,
            (
                SELECT COUNT(*)
                FROM observations
                WHERE substr(observation_datetime, 1, 4) IN ({placeholders})
            ) AS total_observations,
            (
                SELECT ROUND(
                    CAST(COUNT(*) AS REAL) / NULLIF(COUNT(DISTINCT patient_id), 0),
                    2
                )
                FROM encounters
                WHERE substr(encounter_start, 1, 4) IN ({placeholders})
            ) AS avg_encounters_per_patient,
            (
                SELECT ROUND(AVG(encounter_duration_minutes), 2)
                FROM encounters
                WHERE substr(encounter_start, 1, 4) IN ({placeholders})
                  AND encounter_duration_minutes IS NOT NULL
            ) AS avg_encounter_duration_minutes,
            (
                SELECT COUNT(*)
                FROM data_quality_audit
            ) AS total_data_quality_issues
    """

    num_in_clauses = query.count("IN (")
    params = tuple(selected_years) * num_in_clauses
    return run_query(db_path, query, params=params)


def get_encounters_by_year_month(
    db_path: str | Path,
    selected_years: list[str] | None = None,
) -> pd.DataFrame:
    if not selected_years:
        query = """
            SELECT * FROM vw_encounters_by_year_month
        """
        return run_query(db_path, query)

    placeholders = _build_in_clause_placeholders(selected_years)
    query = f"""
        SELECT
            substr(encounter_start, 1, 7) AS encounter_year_month,
            COUNT(*) AS encounter_count
        FROM encounters
        WHERE encounter_start IS NOT NULL
          AND substr(encounter_start, 1, 4) IN ({placeholders})
        GROUP BY substr(encounter_start, 1, 7)
        ORDER BY encounter_year_month
    """

    num_in_clauses = query.count("IN (")
    params = tuple(selected_years) * num_in_clauses
    return run_query(db_path, query, params=params)


def get_encounters_by_year(
    db_path: str | Path,
    selected_years: list[str] | None = None,
) -> pd.DataFrame:
    if not selected_years:
        query = """
            SELECT * FROM vw_encounters_by_year
        """
        return run_query(db_path, query)

    placeholders = _build_in_clause_placeholders(selected_years)
    query = f"""
        SELECT
            substr(encounter_start, 1, 4) AS encounter_year,
            COUNT(*) AS encounter_count
        FROM encounters
        WHERE encounter_start IS NOT NULL
          AND substr(encounter_start, 1, 4) IN ({placeholders})
        GROUP BY substr(encounter_start, 1, 4)
        ORDER BY encounter_year
    """

    num_in_clauses = query.count("IN (")
    params = tuple(selected_years) * num_in_clauses
    return run_query(db_path, query, params=params)


def get_encounters_by_month(
    db_path: str | Path,
    selected_years: list[str] | None = None,
) -> pd.DataFrame:
    if not selected_years:
        query = """
            SELECT * FROM vw_encounters_by_month
        """
        return run_query(db_path, query)

    placeholders = _build_in_clause_placeholders(selected_years)
    query = f"""
        SELECT
            substr(encounter_start, 6, 2) AS encounter_month,
            COUNT(*) AS encounter_count
        FROM encounters
        WHERE encounter_start IS NOT NULL
          AND substr(encounter_start, 1, 4) IN ({placeholders})
        GROUP BY substr(encounter_start, 6, 2)
        ORDER BY encounter_month
    """

    num_in_clauses = query.count("IN (")
    params = tuple(selected_years) * num_in_clauses
    return run_query(db_path, query, params=params)


def get_top_encounter_types(
    db_path: str | Path,
    selected_years: list[str] | None = None,
    limit: int = 10,
) -> pd.DataFrame:
    limit = int(limit)

    if not selected_years:
        query = f"""
            SELECT *
            FROM vw_top_encounter_types
            LIMIT {limit}
        """
        return run_query(db_path, query)

    placeholders = _build_in_clause_placeholders(selected_years)
    query = f"""
        SELECT
            COALESCE(encounter_type, 'Unknown') AS encounter_type,
            COUNT(*) AS encounter_count,
            ROUND(AVG(encounter_duration_minutes), 2) AS avg_duration_minutes
        FROM encounters
        WHERE encounter_start IS NOT NULL
          AND substr(encounter_start, 1, 4) IN ({placeholders})
        GROUP BY COALESCE(encounter_type, 'Unknown')
        ORDER BY encounter_count DESC
        LIMIT {limit}
    """

    num_in_clauses = query.count("IN (")
    params = tuple(selected_years) * num_in_clauses
    return run_query(db_path, query, params=params)


def get_top_conditions(
    db_path: str | Path,
    selected_years: list[str] | None = None,
    limit: int = 10,
) -> pd.DataFrame:
    limit = int(limit)

    if not selected_years:
        query = f"""
            SELECT *
            FROM vw_top_conditions
            LIMIT {limit}
        """
        return run_query(db_path, query)

    placeholders = _build_in_clause_placeholders(selected_years)
    query = f"""
        SELECT
            COALESCE(condition_description, 'Unknown') AS condition_description,
            COUNT(*) AS condition_count,
            COUNT(DISTINCT patient_id) AS patient_count
        FROM conditions
        WHERE substr(COALESCE(recorded_datetime, onset_datetime), 1, 4) IN ({placeholders})
        GROUP BY COALESCE(condition_description, 'Unknown')
        ORDER BY condition_count DESC
        LIMIT {limit}
    """

    num_in_clauses = query.count("IN (")
    params = tuple(selected_years) * num_in_clauses
    return run_query(db_path, query, params=params)


def get_top_observation_types(
    db_path: str | Path,
    selected_years: list[str] | None = None,
    limit: int = 10,
) -> pd.DataFrame:
    limit = int(limit)

    if not selected_years:
        query = f"""
            SELECT *
            FROM vw_top_observation_types
            LIMIT {limit}
        """
        return run_query(db_path, query)

    placeholders = _build_in_clause_placeholders(selected_years)
    query = f"""
        SELECT
            COALESCE(observation_description, 'Unknown') AS observation_description,
            value_category,
            COUNT(*) AS observation_count
        FROM observations
        WHERE substr(observation_datetime, 1, 4) IN ({placeholders})
        GROUP BY
            COALESCE(observation_description, 'Unknown'),
            value_category
        ORDER BY observation_count DESC
        LIMIT {limit}
    """

    num_in_clauses = query.count("IN (")
    params = tuple(selected_years) * num_in_clauses
    return run_query(db_path, query, params=params)


def get_data_quality_summary(db_path: str | Path) -> pd.DataFrame:
    query = """
        SELECT * FROM vw_data_quality_summary
    """
    return run_query(db_path, query)


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    db_path = project_root / "data" / "db" / "healthcare_reporting.db"

    years = get_available_years(db_path)
    sample_years = years[-3:] if len(years) >= 3 else years

    print("Available years:")
    print(years[:10], "..." if len(years) > 10 else "")
    print()

    print("Overview metrics:")
    print(get_overview_metrics(db_path, selected_years=sample_years))
    print()

    print("Encounters by year:")
    print(get_encounters_by_year(db_path, selected_years=sample_years).head())
    print()

    print("Encounters by month:")
    print(get_encounters_by_month(db_path, selected_years=sample_years).head())
    print()

    print("Top encounter types:")
    print(get_top_encounter_types(db_path, selected_years=sample_years).head())
    print()

    print("Top conditions:")
    print(get_top_conditions(db_path, selected_years=sample_years).head())
    print()

    print("Data quality summary:")
    print(get_data_quality_summary(db_path).head())
