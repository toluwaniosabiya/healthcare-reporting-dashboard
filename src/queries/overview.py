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


def run_query(db_path: str | Path, query: str) -> pd.DataFrame:
    """
    Execute a SQL query and return the result as a pandas DataFrame.
    """
    conn = get_connection(db_path)

    try:
        return pd.read_sql_query(query, conn)
    finally:
        conn.close()


def get_overview_metrics(db_path: str | Path) -> pd.DataFrame:
    query = """
        SELECT * FROM vw_overview_metrics
    """
    return run_query(db_path, query)


def get_encounters_by_year_month(db_path: str | Path) -> pd.DataFrame:
    query = """
        SELECT * FROM vw_encounters_by_year_month
    """
    return run_query(db_path, query)


def get_encounters_by_year(db_path: str | Path) -> pd.DataFrame:
    query = """
        SELECT * FROM vw_encounters_by_year
    """
    return run_query(db_path, query)


def get_encounters_by_month(db_path: str | Path) -> pd.DataFrame:
    query = """
        SELECT * FROM vw_encounters_by_month
    """
    return run_query(db_path, query)


def get_top_encounter_types(db_path: str | Path, limit: int = 10) -> pd.DataFrame:
    query = f"""
        SELECT *
        FROM vw_top_encounter_types
        LIMIT {limit}
    """
    return run_query(db_path, query)


def get_top_conditions(db_path: str | Path, limit: int = 10) -> pd.DataFrame:
    query = f"""
        SELECT *
        FROM vw_top_conditions
        LIMIT {limit}
    """
    return run_query(db_path, query)


def get_top_observation_types(db_path: str | Path, limit: int = 10) -> pd.DataFrame:
    query = f"""
        SELECT *
        FROM vw_top_observation_types
        LIMIT {limit}
    """
    return run_query(db_path, query)


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

    print("Encounters by year:")
    print(get_encounters_by_year(db_path).head())
    print()

    print("Encounters by month:")
    print(get_encounters_by_month(db_path).head())
    print()

    print("Top encounter types:")
    print(get_top_encounter_types(db_path).head())
    print()

    print("Top conditions:")
    print(get_top_conditions(db_path).head())
    print()

    print("Data quality summary:")
    print(get_data_quality_summary(db_path).head())
