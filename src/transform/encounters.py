from __future__ import annotations

from datetime import datetime
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


def calculate_duration_minutes(
    encounter_start: str | None, encounter_end: str | None
) -> float | None:
    """
    Calculate encounter duration in minutes from ISO datetime strings.
    Returns None if either value is missing or invalid.
    """
    if not encounter_start or not encounter_end:
        return None

    try:
        start_dt = datetime.fromisoformat(encounter_start.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(encounter_end.replace("Z", "+00:00"))
        return round((end_dt - start_dt).total_seconds() / 60, 1)
    except ValueError:
        return None


def extract_encounter_row(resource: dict[str, Any]) -> dict[str, Any]:
    """
    Flatten one FHIR Encounter resource into a relational row.
    """
    encounter_id = resource.get("id")
    encounter_status = resource.get("status")
    encounter_class = resource.get("class", {}).get("code")

    encounter_type = None
    encounter_types = resource.get("type", [])
    if encounter_types:
        encounter_type = encounter_types[0].get("text")

    patient_id = parse_reference(resource.get("subject", {}).get("reference"))

    period = resource.get("period", {})
    encounter_start = period.get("start")
    encounter_end = period.get("end")
    encounter_duration_minutes = calculate_duration_minutes(
        encounter_start, encounter_end
    )

    provider_name = None
    provider_reference = None
    participants = resource.get("participant", [])
    if participants:
        individual = participants[0].get("individual", {})
        provider_name = individual.get("display")
        provider_reference = individual.get("reference")

    organization_name = None
    organization_reference = None
    service_provider = resource.get("serviceProvider", {})
    if service_provider:
        organization_name = service_provider.get("display")
        organization_reference = service_provider.get("reference")

    location_name = None
    location_reference = None
    locations = resource.get("location", [])
    if locations:
        loc = locations[0].get("location", {})
        location_name = loc.get("display")
        location_reference = loc.get("reference")

    return {
        "encounter_id": encounter_id,
        "patient_id": patient_id,
        "encounter_status": encounter_status,
        "encounter_class": encounter_class,
        "encounter_type": encounter_type,
        "encounter_start": encounter_start,
        "encounter_end": encounter_end,
        "encounter_duration_minutes": encounter_duration_minutes,
        "provider_name": provider_name,
        "provider_reference": provider_reference,
        "organization_name": organization_name,
        "organization_reference": organization_reference,
        "location_name": location_name,
        "location_reference": location_reference,
    }


def transform_encounters(resources: list[dict[str, Any]]) -> pd.DataFrame:
    """
    Transform a list of FHIR Encounter resources into a pandas DataFrame.
    """
    rows = [extract_encounter_row(resource) for resource in resources]
    return pd.DataFrame(rows)


if __name__ == "__main__":
    from pathlib import Path

    from src.extract.read_ndjson import read_resource_group

    raw_dir = Path("data/raw")
    encounter_resources = read_resource_group(raw_dir, "Encounter")

    df_encounters = transform_encounters(encounter_resources)

    print(df_encounters.head())
    print(df_encounters.info())
