from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


def get_connection(db_path: str | Path) -> sqlite3.Connection:
    """
    Create and return a SQLite connection.
    """
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def execute_sql_file(conn: sqlite3.Connection, sql_file_path: str | Path) -> None:
    """
    Execute a SQL script file against the provided SQLite connection.
    """
    sql_file_path = Path(sql_file_path)

    if not sql_file_path.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_file_path}")

    sql_script = sql_file_path.read_text(encoding="utf-8")
    conn.executescript(sql_script)
    conn.commit()


def load_dataframe(
    conn: sqlite3.Connection,
    df: pd.DataFrame,
    table_name: str,
    if_exists: str = "append",
) -> None:
    """
    Load a pandas DataFrame into a SQLite table.
    """
    df.to_sql(table_name, conn, if_exists=if_exists, index=False)


def build_database(
    db_path: str | Path,
    schema_path: str | Path,
    views_path: str | Path,
    df_patients: pd.DataFrame,
    df_encounters: pd.DataFrame,
    df_conditions: pd.DataFrame,
    df_observations: pd.DataFrame,
    df_data_quality_audit: pd.DataFrame,
) -> None:
    """
    Build the SQLite database from transformed DataFrames and reporting views.
    """
    conn = get_connection(db_path)

    try:
        execute_sql_file(conn, schema_path)

        load_dataframe(conn, df_patients, "patients")
        load_dataframe(conn, df_encounters, "encounters")
        load_dataframe(conn, df_conditions, "conditions")
        load_dataframe(conn, df_observations, "observations")
        load_dataframe(conn, df_data_quality_audit, "data_quality_audit")

        execute_sql_file(conn, views_path)

        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    from src.extract.read_ndjson import read_resource_group
    from src.transform.conditions import transform_conditions
    from src.transform.encounters import transform_encounters
    from src.transform.observations import transform_observations
    from src.transform.patients import transform_patients
    from src.transform.quality_checks import run_all_quality_checks

    project_root = Path(__file__).resolve().parents[2]

    raw_dir = project_root / "data" / "raw"
    db_path = project_root / "data" / "db" / "healthcare_reporting.db"
    schema_path = project_root / "sql" / "schema.sql"
    views_path = project_root / "sql" / "views.sql"

    patient_resources = read_resource_group(raw_dir, "Patient")
    encounter_resources = read_resource_group(raw_dir, "Encounter")
    condition_resources = read_resource_group(raw_dir, "Condition")
    observation_resources = read_resource_group(raw_dir, "Observation")

    df_patients = transform_patients(patient_resources)
    df_encounters = transform_encounters(encounter_resources)
    df_conditions = transform_conditions(condition_resources)
    df_observations = transform_observations(observation_resources)

    df_data_quality_audit = run_all_quality_checks(
        df_patients=df_patients,
        df_encounters=df_encounters,
        df_conditions=df_conditions,
        df_observations=df_observations,
    )

    build_database(
        db_path=db_path,
        schema_path=schema_path,
        views_path=views_path,
        df_patients=df_patients,
        df_encounters=df_encounters,
        df_conditions=df_conditions,
        df_observations=df_observations,
        df_data_quality_audit=df_data_quality_audit,
    )

    print(f"Database built successfully at: {db_path}")
    print(f"Patients: {len(df_patients):,}")
    print(f"Encounters: {len(df_encounters):,}")
    print(f"Conditions: {len(df_conditions):,}")
    print(f"Observations: {len(df_observations):,}")
    print(f"Data quality audit rows: {len(df_data_quality_audit):,}")
