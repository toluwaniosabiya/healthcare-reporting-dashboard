from __future__ import annotations

from typing import Any

import pandas as pd


def parse_reference(reference: str | None) -> str | None:
    """
    Extract the resource ID from a FHIR reference string.

    Example:
        'Patient/123' -> '123'
    """
    if not reference:
        return None
    return reference.split("/")[-1]


def extract_conditions_row(resource: dict[str, Any]) -> dict[str, Any]:
    """
    Flatten one FHIR Condition resource into a relational row.
    """
    condition_id = resource.get("id")

    patient_id = parse_reference(resource.get("subject", {}).get("reference"))
    encounter_id = parse_reference(resource.get("encounter", {}).get("reference"))

    coding = resource.get("code", {}).get("coding", [])
    condition_code = None
    condition_description = None
    condition_system = None
    if coding:
        condition_code = coding[0].get("code")
        condition_description = coding[0].get("display")
        condition_system = coding[0].get("system")

    clinical_status = None
    clinical_status_coding = resource.get("clinicalStatus", {}).get("coding", [])
    if clinical_status_coding:
        clinical_status = clinical_status_coding[0].get("code")

    verification_status = None
    verification_status_coding = resource.get("verificationStatus", {}).get(
        "coding", []
    )
    if verification_status_coding:
        verification_status = verification_status_coding[0].get("code")

    onset_datetime = resource.get("onsetDateTime")
    recorded_datetime = resource.get("recordedDate")

    return {
        "condition_id": condition_id,
        "patient_id": patient_id,
        "encounter_id": encounter_id,
        "condition_code": condition_code,
        "condition_description": condition_description,
        "condition_system": condition_system,
        "clinical_status": clinical_status,
        "verification_status": verification_status,
        "onset_datetime": onset_datetime,
        "recorded_datetime": recorded_datetime,
    }


def transform_conditions(resources: list[dict[str, Any]]) -> pd.DataFrame:
    """
    Transform a list of FHIR Condition resources into a pandas DataFrame.
    """
    rows = [extract_conditions_row(resource) for resource in resources]
    return pd.DataFrame(rows)


if __name__ == "__main__":
    from pathlib import Path

    from src.extract.read_ndjson import read_resource_group

    raw_dir = Path("data/raw")
    condition_resources = read_resource_group(raw_dir, "Condition")

    df_conditions = transform_conditions(condition_resources)

    print(df_conditions.head())
    print(df_conditions.info())
