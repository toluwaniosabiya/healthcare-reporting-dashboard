from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd


def build_audit_row(
    source_table: str,
    record_id: str | None,
    issue_type: str,
    issue_severity: str,
    issue_description: str,
) -> dict[str, Any]:
    """
    Create one standardized data quality audit record.
    """
    return {
        "source_table": source_table,
        "record_id": record_id,
        "issue_type": issue_type,
        "issue_severity": issue_severity,
        "issue_description": issue_description,
        "detected_at": datetime.now().isoformat(timespec="seconds"),
    }


def check_patients(df_patients: pd.DataFrame) -> pd.DataFrame:
    audit_rows: list[dict[str, Any]] = []

    for _, row in df_patients.iterrows():
        record_id = row.get("patient_id")

        if pd.isna(record_id):
            audit_rows.append(
                build_audit_row(
                    "patients",
                    None,
                    "missing_primary_key",
                    "high",
                    "Patient record is missing patient_id.",
                )
            )

        if pd.isna(row.get("birth_date")):
            audit_rows.append(
                build_audit_row(
                    "patients",
                    record_id,
                    "missing_birth_date",
                    "medium",
                    "Patient is missing birth_date.",
                )
            )

        if pd.isna(row.get("first_name")) or pd.isna(row.get("last_name")):
            audit_rows.append(
                build_audit_row(
                    "patients",
                    record_id,
                    "incomplete_name",
                    "low",
                    "Patient is missing first_name or last_name.",
                )
            )

        age = row.get("age")
        if pd.notna(age) and (age < 0 or age > 120):
            audit_rows.append(
                build_audit_row(
                    "patients",
                    record_id,
                    "invalid_age",
                    "medium",
                    f"Patient age {age} is outside expected range.",
                )
            )

    return pd.DataFrame(audit_rows)


def check_encounters(df_encounters: pd.DataFrame) -> pd.DataFrame:
    audit_rows: list[dict[str, Any]] = []

    for _, row in df_encounters.iterrows():
        record_id = row.get("encounter_id")

        if pd.isna(record_id):
            audit_rows.append(
                build_audit_row(
                    "encounters",
                    None,
                    "missing_primary_key",
                    "high",
                    "Encounter record is missing encounter_id.",
                )
            )

        if pd.isna(row.get("patient_id")):
            audit_rows.append(
                build_audit_row(
                    "encounters",
                    record_id,
                    "missing_patient_reference",
                    "high",
                    "Encounter is missing patient_id.",
                )
            )

        if pd.isna(row.get("encounter_start")):
            audit_rows.append(
                build_audit_row(
                    "encounters",
                    record_id,
                    "missing_encounter_start",
                    "medium",
                    "Encounter is missing encounter_start.",
                )
            )

        if pd.isna(row.get("encounter_type")):
            audit_rows.append(
                build_audit_row(
                    "encounters",
                    record_id,
                    "missing_encounter_type",
                    "low",
                    "Encounter is missing encounter_type.",
                )
            )

        duration = row.get("encounter_duration_minutes")
        if pd.notna(duration) and duration < 0:
            audit_rows.append(
                build_audit_row(
                    "encounters",
                    record_id,
                    "negative_duration",
                    "medium",
                    f"Encounter duration {duration} is negative.",
                )
            )

    return pd.DataFrame(audit_rows)


def check_conditions(df_conditions: pd.DataFrame) -> pd.DataFrame:
    audit_rows: list[dict[str, Any]] = []

    for _, row in df_conditions.iterrows():
        record_id = row.get("condition_id")

        if pd.isna(record_id):
            audit_rows.append(
                build_audit_row(
                    "conditions",
                    None,
                    "missing_primary_key",
                    "high",
                    "Condition record is missing condition_id.",
                )
            )

        if pd.isna(row.get("patient_id")):
            audit_rows.append(
                build_audit_row(
                    "conditions",
                    record_id,
                    "missing_patient_reference",
                    "high",
                    "Condition is missing patient_id.",
                )
            )

        if pd.isna(row.get("condition_code")):
            audit_rows.append(
                build_audit_row(
                    "conditions",
                    record_id,
                    "missing_condition_code",
                    "medium",
                    "Condition is missing condition_code.",
                )
            )

        if pd.isna(row.get("condition_description")):
            audit_rows.append(
                build_audit_row(
                    "conditions",
                    record_id,
                    "missing_condition_description",
                    "low",
                    "Condition is missing condition_description.",
                )
            )

    return pd.DataFrame(audit_rows)


def check_observations(df_observations: pd.DataFrame) -> pd.DataFrame:
    audit_rows: list[dict[str, Any]] = []

    for _, row in df_observations.iterrows():
        record_id = row.get("observation_id")

        if pd.isna(record_id):
            audit_rows.append(
                build_audit_row(
                    "observations",
                    None,
                    "missing_primary_key",
                    "high",
                    "Observation record is missing observation_id.",
                )
            )

        if pd.isna(row.get("patient_id")):
            audit_rows.append(
                build_audit_row(
                    "observations",
                    record_id,
                    "missing_patient_reference",
                    "high",
                    "Observation is missing patient_id.",
                )
            )

        if pd.isna(row.get("observation_code")):
            audit_rows.append(
                build_audit_row(
                    "observations",
                    record_id,
                    "missing_observation_code",
                    "medium",
                    "Observation is missing observation_code.",
                )
            )

        if pd.isna(row.get("observation_datetime")):
            audit_rows.append(
                build_audit_row(
                    "observations",
                    record_id,
                    "missing_observation_datetime",
                    "low",
                    "Observation is missing observation_datetime.",
                )
            )

        value_numeric = row.get("value_numeric")
        value_text = row.get("value_text")
        if pd.isna(value_numeric) and pd.isna(value_text):
            audit_rows.append(
                build_audit_row(
                    "observations",
                    record_id,
                    "missing_observation_value",
                    "medium",
                    "Observation is missing both numeric and text values.",
                )
            )

    return pd.DataFrame(audit_rows)


def run_all_quality_checks(
    df_patients: pd.DataFrame,
    df_encounters: pd.DataFrame,
    df_conditions: pd.DataFrame,
    df_observations: pd.DataFrame,
) -> pd.DataFrame:
    """
    Run all table-level quality checks and return one combined audit DataFrame.
    """
    audit_frames = [
        check_patients(df_patients),
        check_encounters(df_encounters),
        check_conditions(df_conditions),
        check_observations(df_observations),
    ]

    non_empty_frames = [df for df in audit_frames if not df.empty]

    if not non_empty_frames:
        return pd.DataFrame(
            columns=[
                "source_table",
                "record_id",
                "issue_type",
                "issue_severity",
                "issue_description",
                "detected_at",
            ]
        )

    return pd.concat(non_empty_frames, ignore_index=True)


if __name__ == "__main__":
    from pathlib import Path

    from src.extract.read_ndjson import read_resource_group
    from src.transform.conditions import transform_conditions
    from src.transform.encounters import transform_encounters
    from src.transform.observations import transform_observations
    from src.transform.patients import transform_patients

    raw_dir = Path("data/raw")

    patient_resources = read_resource_group(raw_dir, "Patient")
    encounter_resources = read_resource_group(raw_dir, "Encounter")
    condition_resources = read_resource_group(raw_dir, "Condition")
    observation_resources = read_resource_group(raw_dir, "Observation")

    df_patients = transform_patients(patient_resources)
    df_encounters = transform_encounters(encounter_resources)
    df_conditions = transform_conditions(condition_resources)
    df_observations = transform_observations(observation_resources)

    df_audit = run_all_quality_checks(
        df_patients=df_patients,
        df_encounters=df_encounters,
        df_conditions=df_conditions,
        df_observations=df_observations,
    )

    print(df_audit.head())
    print(df_audit.info())
    # print(
    #     df_audit[df_audit["source_table"] == "patients"]
    #     .head()
    #     .drop(columns=["record_id", "detected_at"])
    # )
    # print(
    #     df_audit[df_audit["source_table"] == "conditions"]
    #     .head()
    #     .drop(columns=["record_id", "detected_at"])
    # )
    # print(
    #     df_audit[df_audit["source_table"] == "encounters"]
    #     .head()
    #     .drop(columns=["record_id", "detected_at"])
    # )
    # print(
    #     df_audit[df_audit["source_table"] == "observations"]
    #     .head()
    #     .drop(columns=["record_id", "detected_at"])
    # )

    # print(df_audit["source_table"].value_counts())
