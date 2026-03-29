from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


def get_connection(db_path: str | Path) -> sqlite3.Connection:
    db_path = Path(db_path)

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    return sqlite3.connect(db_path)


def run_query(
    db_path: str | Path,
    query: str,
    params: tuple | None = None,
) -> pd.DataFrame:
    conn = get_connection(db_path)

    try:
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()


def _build_in_clause_placeholders(values: list[str]) -> str:
    return ", ".join(["?"] * len(values))


def get_clinical_kpis(
    db_path: str | Path,
    selected_years: list[str] | None = None,
) -> pd.DataFrame:
    if not selected_years:
        query = """
            SELECT
                ROUND(AVG(CASE 
                    WHEN observation_description = 'Pain severity - 0-10 verbal numeric rating [Score] - Reported'
                    THEN value_numeric END), 2) AS avg_pain_score,

                ROUND(AVG(CASE 
                    WHEN observation_description = 'Body mass index (BMI) [Ratio]'
                    THEN value_numeric END), 2) AS avg_bmi,

                ROUND(AVG(CASE 
                    WHEN observation_description = 'Body Weight'
                    THEN value_numeric END), 2) AS avg_weight,

                ROUND(AVG(CASE 
                    WHEN observation_description = 'Body Height'
                    THEN value_numeric END), 2) AS avg_height
            FROM observations
        """
        return run_query(db_path, query)

    placeholders = _build_in_clause_placeholders(selected_years)

    query = f"""
        SELECT
            ROUND(AVG(CASE 
                WHEN observation_description = 'Pain severity - 0-10 verbal numeric rating [Score] - Reported'
                THEN value_numeric END), 2) AS avg_pain_score,

            ROUND(AVG(CASE 
                WHEN observation_description = 'Body mass index (BMI) [Ratio]'
                THEN value_numeric END), 2) AS avg_bmi,

            ROUND(AVG(CASE 
                WHEN observation_description = 'Body Weight'
                THEN value_numeric END), 2) AS avg_weight,

            ROUND(AVG(CASE 
                WHEN observation_description = 'Body Height'
                THEN value_numeric END), 2) AS avg_height
        FROM observations
        WHERE substr(observation_datetime, 1, 4) IN ({placeholders})
    """

    return run_query(db_path, query, params=tuple(selected_years))


def get_top_conditions(
    db_path: str | Path,
    selected_years: list[str] | None = None,
    limit: int = 15,
) -> pd.DataFrame:
    limit = max(1, int(limit))

    if not selected_years:
        query = f"""
            SELECT
                COALESCE(condition_description, 'Unknown') AS condition_description,
                COUNT(*) AS condition_count,
                COUNT(DISTINCT patient_id) AS patient_count
            FROM conditions
            GROUP BY COALESCE(condition_description, 'Unknown')
            ORDER BY condition_count DESC
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
    return run_query(db_path, query, params=tuple(selected_years))


def get_top_observation_types(
    db_path: str | Path,
    selected_years: list[str] | None = None,
    limit: int = 20,
) -> pd.DataFrame:
    limit = max(1, int(limit))

    if not selected_years:
        query = f"""
            SELECT
                COALESCE(observation_description, 'Unknown') AS observation_description,
                value_category,
                COUNT(*) AS observation_count
            FROM observations
            GROUP BY
                COALESCE(observation_description, 'Unknown'),
                value_category
            ORDER BY observation_count DESC
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
    return run_query(db_path, query, params=tuple(selected_years))


def get_numeric_observation_type_summary(
    db_path: str | Path,
    selected_years: list[str] | None = None,
    limit: int = 15,
) -> pd.DataFrame:
    limit = max(1, int(limit))

    if not selected_years:
        query = f"""
            SELECT
                COALESCE(observation_description, 'Unknown') AS observation_description,
                COUNT(*) AS observation_count,
                ROUND(AVG(value_numeric), 2) AS avg_value,
                ROUND(MIN(value_numeric), 2) AS min_value,
                ROUND(MAX(value_numeric), 2) AS max_value
            FROM observations
            WHERE value_numeric IS NOT NULL
            GROUP BY COALESCE(observation_description, 'Unknown')
            ORDER BY observation_count DESC
            LIMIT {limit}
        """
        return run_query(db_path, query)

    placeholders = _build_in_clause_placeholders(selected_years)
    query = f"""
        SELECT
            COALESCE(observation_description, 'Unknown') AS observation_description,
            COUNT(*) AS observation_count,
            ROUND(AVG(value_numeric), 2) AS avg_value,
            ROUND(MIN(value_numeric), 2) AS min_value,
            ROUND(MAX(value_numeric), 2) AS max_value
        FROM observations
        WHERE value_numeric IS NOT NULL
          AND substr(observation_datetime, 1, 4) IN ({placeholders})
        GROUP BY COALESCE(observation_description, 'Unknown')
        ORDER BY observation_count DESC
        LIMIT {limit}
    """
    return run_query(db_path, query, params=tuple(selected_years))


def get_numeric_observation_boxplot_data(
    db_path: str | Path,
    selected_years: list[str] | None = None,
    top_n: int = 5,
) -> pd.DataFrame:
    top_n = max(1, int(top_n))

    if not selected_years:
        query = f"""
            WITH top_numeric_types AS (
                SELECT
                    COALESCE(observation_description, 'Unknown') AS observation_description
                FROM observations
                WHERE value_numeric IS NOT NULL
                GROUP BY COALESCE(observation_description, 'Unknown')
                ORDER BY COUNT(*) DESC
                LIMIT {top_n}
            )
            SELECT
                COALESCE(observation_description, 'Unknown') AS observation_description,
                value_numeric
            FROM observations
            WHERE value_numeric IS NOT NULL
              AND COALESCE(observation_description, 'Unknown') IN (
                  SELECT observation_description FROM top_numeric_types
              )
        """
        return run_query(db_path, query)

    placeholders = _build_in_clause_placeholders(selected_years)
    query = f"""
        WITH top_numeric_types AS (
            SELECT
                COALESCE(observation_description, 'Unknown') AS observation_description
            FROM observations
            WHERE value_numeric IS NOT NULL
              AND substr(observation_datetime, 1, 4) IN ({placeholders})
            GROUP BY COALESCE(observation_description, 'Unknown')
            ORDER BY COUNT(*) DESC
            LIMIT {top_n}
        )
        SELECT
            COALESCE(observation_description, 'Unknown') AS observation_description,
            value_numeric
        FROM observations
        WHERE value_numeric IS NOT NULL
          AND substr(observation_datetime, 1, 4) IN ({placeholders})
          AND COALESCE(observation_description, 'Unknown') IN (
              SELECT observation_description FROM top_numeric_types
          )
    """
    params = tuple(selected_years) + tuple(selected_years)
    return run_query(db_path, query, params=params)


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    db_path = project_root / "data" / "db" / "healthcare_reporting.db"

    print(get_top_conditions(db_path).head())
    print(get_top_observation_types(db_path).head())
    print(get_numeric_observation_type_summary(db_path).head())
    print(get_numeric_observation_boxplot_data(db_path).head())
