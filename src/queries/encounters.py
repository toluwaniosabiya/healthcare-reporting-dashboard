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

    return sqlite3.connect(db_path)


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


def get_encounters_by_year(
    db_path: str | Path,
    selected_years: list[str] | None = None,
) -> pd.DataFrame:
    if not selected_years:
        query = """
            SELECT
                substr(encounter_start, 1, 4) AS encounter_year,
                COUNT(*) AS encounter_count
            FROM encounters
            WHERE encounter_start IS NOT NULL
            GROUP BY substr(encounter_start, 1, 4)
            ORDER BY encounter_year
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
    return run_query(db_path, query, params=tuple(selected_years))


def get_encounters_by_month(
    db_path: str | Path,
    selected_years: list[str] | None = None,
) -> pd.DataFrame:
    if not selected_years:
        query = """
            SELECT
                substr(encounter_start, 6, 2) AS encounter_month,
                COUNT(*) AS encounter_count
            FROM encounters
            WHERE encounter_start IS NOT NULL
            GROUP BY substr(encounter_start, 6, 2)
            ORDER BY encounter_month
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
    return run_query(db_path, query, params=tuple(selected_years))


def get_encounter_year_month_trend(
    db_path: str | Path,
    selected_years: list[str] | None = None,
) -> pd.DataFrame:
    if not selected_years:
        query = """
            SELECT
                substr(encounter_start, 1, 7) AS encounter_year_month,
                COUNT(*) AS encounter_count
            FROM encounters
            WHERE encounter_start IS NOT NULL
            GROUP BY substr(encounter_start, 1, 7)
            ORDER BY encounter_year_month
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
    return run_query(db_path, query, params=tuple(selected_years))


def get_top_encounter_types(
    db_path: str | Path,
    selected_years: list[str] | None = None,
    limit: int = 10,
) -> pd.DataFrame:
    limit = max(1, int(limit))

    if not selected_years:
        query = f"""
            SELECT
                COALESCE(encounter_type, 'Unknown') AS encounter_type,
                COUNT(*) AS encounter_count,
                ROUND(AVG(encounter_duration_minutes), 2) AS avg_duration_minutes
            FROM encounters
            GROUP BY COALESCE(encounter_type, 'Unknown')
            ORDER BY encounter_count DESC
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
    return run_query(db_path, query, params=tuple(selected_years))


def get_encounter_class_summary(
    db_path: str | Path,
    selected_years: list[str] | None = None,
    # limit: int = 15,
) -> pd.DataFrame:
    # limit = max(1, int(limit))

    if not selected_years:
        query = """
            SELECT
                CASE encounter_class
                    WHEN 'AMB' THEN 'Ambulatory'
                    WHEN 'IMP' THEN 'Inpatient'
                    WHEN 'EMER' THEN 'Emergency'
                    WHEN 'HH' THEN 'Home Health'
                    WHEN 'VR' THEN 'Virtual'
                    ELSE 'Other'
                END AS encounter_class,
                COUNT(*) AS encounter_count
            FROM encounters
            GROUP BY 1
            ORDER BY encounter_count DESC
        """
        return run_query(db_path, query)

    placeholders = _build_in_clause_placeholders(selected_years)
    query = f"""
        SELECT
            CASE encounter_class
                WHEN 'AMB' THEN 'Ambulatory'
                WHEN 'IMP' THEN 'Inpatient'
                WHEN 'EMER' THEN 'Emergency'
                WHEN 'HH' THEN 'Home Health'
                WHEN 'VR' THEN 'Virtual'
                ELSE 'Other'
            END AS encounter_class,
            COUNT(*) AS encounter_count
        FROM encounters
        WHERE encounter_start IS NOT NULL
          AND substr(encounter_start, 1, 4) IN ({placeholders})
        GROUP BY 1
        ORDER BY encounter_count DESC
    """
    return run_query(db_path, query, params=tuple(selected_years))


def get_encounter_duration_by_type(
    db_path: str | Path,
    selected_years: list[str] | None = None,
    limit: int = 15,
) -> pd.DataFrame:
    limit = max(1, int(limit))

    if not selected_years:
        query = f"""
            SELECT
                COALESCE(encounter_type, 'Unknown') AS encounter_type,
                COUNT(*) AS encounter_count,
                ROUND(AVG(encounter_duration_minutes), 2) AS avg_duration_minutes
            FROM encounters
            WHERE encounter_duration_minutes IS NOT NULL
            GROUP BY COALESCE(encounter_type, 'Unknown')
            ORDER BY avg_duration_minutes DESC
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
        WHERE encounter_duration_minutes IS NOT NULL
          AND encounter_start IS NOT NULL
          AND substr(encounter_start, 1, 4) IN ({placeholders})
        GROUP BY COALESCE(encounter_type, 'Unknown')
        ORDER BY avg_duration_minutes DESC
        LIMIT {limit}
    """
    return run_query(db_path, query, params=tuple(selected_years))


def get_encounter_duration_distribution(
    db_path: str | Path,
    selected_years: list[str] | None = None,
) -> pd.DataFrame:
    if not selected_years:
        query = """
            SELECT
                encounter_duration_minutes
            FROM encounters
            WHERE encounter_duration_minutes IS NOT NULL
        """
        return run_query(db_path, query)

    placeholders = _build_in_clause_placeholders(selected_years)
    query = f"""
        SELECT
            encounter_duration_minutes
        FROM encounters
        WHERE encounter_duration_minutes IS NOT NULL
          AND encounter_start IS NOT NULL
          AND substr(encounter_start, 1, 4) IN ({placeholders})
    """
    return run_query(db_path, query, params=tuple(selected_years))


def get_top_organizations(
    db_path: str | Path,
    selected_years: list[str] | None = None,
    limit: int = 10,
) -> pd.DataFrame:
    limit = max(1, int(limit))

    if not selected_years:
        query = f"""
            SELECT
                COALESCE(organization_name, 'Unknown') AS organization_name,
                COUNT(*) AS encounter_count
            FROM encounters
            GROUP BY COALESCE(organization_name, 'Unknown')
            ORDER BY encounter_count DESC
            LIMIT {limit}
        """
        return run_query(db_path, query)

    placeholders = _build_in_clause_placeholders(selected_years)
    query = f"""
        SELECT
            COALESCE(organization_name, 'Unknown') AS organization_name,
            COUNT(*) AS encounter_count
        FROM encounters
        WHERE encounter_start IS NOT NULL
          AND substr(encounter_start, 1, 4) IN ({placeholders})
        GROUP BY COALESCE(organization_name, 'Unknown')
        ORDER BY encounter_count DESC
        LIMIT {limit}
    """
    return run_query(db_path, query, params=tuple(selected_years))


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    db_path = project_root / "data" / "db" / "healthcare_reporting.db"

    years = get_available_years(db_path)
    sample_years = years[-3:] if len(years) >= 3 else years

    print("Available years:")
    print(sample_years)
    print()

    print("Encounters by year:")
    print(get_encounters_by_year(db_path, selected_years=sample_years).head())
    print()

    print("Encounters by month:")
    print(get_encounters_by_month(db_path, selected_years=sample_years).head())
    print()

    print("Year-month trend:")
    print(get_encounter_year_month_trend(db_path, selected_years=sample_years).head())
    print()

    print("Encounter class summary:")
    print(get_encounter_class_summary(db_path, selected_years=sample_years).head())
    print()

    print("Duration by type:")
    print(get_encounter_duration_by_type(db_path, selected_years=sample_years).head())
    print()

    print("Top organizations:")
    print(get_top_organizations(db_path, selected_years=sample_years).head())
