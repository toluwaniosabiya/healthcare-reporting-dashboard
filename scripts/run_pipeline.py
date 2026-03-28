from __future__ import annotations

from pathlib import Path

from src.extract.read_ndjson import read_resource_group
from src.load.sqlite_loader import build_database
from src.transform.conditions import transform_conditions
from src.transform.encounters import transform_encounters
from src.transform.observations import transform_observations
from src.transform.patients import transform_patients
from src.transform.quality_checks import run_all_quality_checks


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]

    raw_dir = project_root / "data" / "raw"
    interim_dir = project_root / "data" / "interim"
    db_path = project_root / "data" / "db" / "healthcare_reporting.db"
    schema_path = project_root / "sql" / "schema.sql"
    views_path = project_root / "sql" / "views.sql"

    interim_dir.mkdir(parents=True, exist_ok=True)

    print("Reading raw FHIR resources...")
    patient_resources = read_resource_group(raw_dir, "Patient")
    encounter_resources = read_resource_group(raw_dir, "Encounter")
    condition_resources = read_resource_group(raw_dir, "Condition")
    observation_resources = read_resource_group(raw_dir, "Observation")

    print("Transforming resources into relational tables...")
    df_patients = transform_patients(patient_resources)
    df_encounters = transform_encounters(encounter_resources)
    df_conditions = transform_conditions(condition_resources)
    df_observations = transform_observations(observation_resources)

    print("Running data quality checks...")
    df_data_quality_audit = run_all_quality_checks(
        df_patients=df_patients,
        df_encounters=df_encounters,
        df_conditions=df_conditions,
        df_observations=df_observations,
    )

    print("Saving interim CSV files...")
    df_patients.to_csv(interim_dir / "patients.csv", index=False)
    df_encounters.to_csv(interim_dir / "encounters.csv", index=False)
    df_conditions.to_csv(interim_dir / "conditions.csv", index=False)
    df_observations.to_csv(interim_dir / "observations.csv", index=False)
    df_data_quality_audit.to_csv(interim_dir / "data_quality_audit.csv", index=False)

    print("Building SQLite database...")
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

    print("\nPipeline completed successfully.")
    print(f"Database: {db_path}")
    print(f"Patients: {len(df_patients):,}")
    print(f"Encounters: {len(df_encounters):,}")
    print(f"Conditions: {len(df_conditions):,}")
    print(f"Observations: {len(df_observations):,}")
    print(f"Data quality audit rows: {len(df_data_quality_audit):,}")


if __name__ == "__main__":
    main()
