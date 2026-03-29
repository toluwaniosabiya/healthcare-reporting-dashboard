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
    """
    return ", ".join(["?"] * len(values))


def get_overview_metrics(
    db_path: str | Path,
    selected_years: list[str] | None = None,
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
                SELECT ROUND(
                    100.0 * SUM(
                        CASE
                            WHEN encounter_start IS NOT NULL
                             AND encounter_end IS NOT NULL
                             AND encounter_duration_minutes IS NOT NULL
                            THEN 1 ELSE 0
                        END
                    ) / NULLIF(COUNT(*), 0),
                    2
                )
                FROM encounters
                WHERE substr(encounter_start, 1, 4) IN ({placeholders})
            ) AS encounter_data_completeness_pct,
            (
                SELECT COUNT(*)
                FROM data_quality_audit
            ) AS total_data_quality_issues
    """

    num_in_clauses = query.count("IN (")
    params = tuple(selected_years) * num_in_clauses
    return run_query(db_path, query, params=params)


def get_top_conditions(
    db_path: str | Path,
    selected_years: list[str] | None = None,
    limit: int = 10,
) -> pd.DataFrame:
    limit = max(1, int(limit))

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


def get_patient_utilization_pct(
    db_path: str | Path,
    threshold: int,
    selected_years: list[str] | None = None,
) -> pd.DataFrame:
    """
    Return the percentage of distinct patients who have at least `threshold`
    encounters within the selected year(s), or across all data if no years are selected.
    """
    threshold = max(0, int(threshold))

    if not selected_years:
        query = """
            SELECT
                ROUND(
                    100.0 * COUNT(*) / NULLIF(
                        (SELECT COUNT(DISTINCT patient_id) FROM encounters),
                        0
                    ),
                    2
                ) AS patient_utilization_pct
            FROM (
                SELECT patient_id
                FROM encounters
                GROUP BY patient_id
                HAVING COUNT(*) >= ?
            )
        """
        return run_query(db_path, query, params=(threshold,))

    placeholders = _build_in_clause_placeholders(selected_years)

    query = f"""
        SELECT
            ROUND(
                100.0 * COUNT(*) / NULLIF(
                    (
                        SELECT COUNT(DISTINCT patient_id)
                        FROM encounters
                        WHERE substr(encounter_start, 1, 4) IN ({placeholders})
                    ),
                    0
                ),
                2
            ) AS patient_utilization_pct
        FROM (
            SELECT patient_id
            FROM encounters
            WHERE substr(encounter_start, 1, 4) IN ({placeholders})
            GROUP BY patient_id
            HAVING COUNT(*) >= ?
        )
    """

    params = tuple(selected_years) + tuple(selected_years) + (threshold,)
    return run_query(db_path, query, params=params)


def get_top_observation_types(
    db_path: str | Path,
    selected_years: list[str] | None = None,
    limit: int = 10,
) -> pd.DataFrame:
    limit = max(1, int(limit))

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

    print("Overview metrics:")
    print(get_overview_metrics(db_path))
    print()

    print("Top conditions:")
    print(get_top_conditions(db_path).head())
    print()

    print("Top observation types:")
    print(get_top_observation_types(db_path).head())
    print()

    print("Data quality summary:")
    print(get_data_quality_summary(db_path).head())

    print("Patient utilization %:")
    print(get_patient_utilization_pct(db_path, threshold=5))
    print()
