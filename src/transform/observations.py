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


def extract_observation_row(resource: dict[str, Any]) -> dict[str, Any]:
    """
    Flatten one FHIR Observation resource into a relational row.
    Supports numeric and text-like value fields.
    """
    observation_id = resource.get("id")

    patient_id = parse_reference(resource.get("subject", {}).get("reference"))
    encounter_id = parse_reference(resource.get("encounter", {}).get("reference"))

    coding = resource.get("code", {}).get("coding", [])
    observation_code = None
    observation_description = None
    observation_system = None
    if coding:
        observation_code = coding[0].get("code")
        observation_description = coding[0].get("display")
        observation_system = coding[0].get("system")

    observation_datetime = resource.get("effectiveDateTime")

    value_numeric = None
    value_unit = None
    value_text = None

    value_quantity = resource.get("valueQuantity")
    value_codeable_concept = resource.get("valueCodeableConcept")
    value_string = resource.get("valueString")

    if value_quantity:
        value_numeric = value_quantity.get("value")
        value_unit = value_quantity.get("unit")
    elif value_codeable_concept:
        value_text = value_codeable_concept.get("text")
        if not value_text:
            codings = value_codeable_concept.get("coding", [])
            if codings:
                value_text = codings[0].get("display")
    elif value_string:
        value_text = value_string

    if value_numeric is not None:
        value_category = "numeric"
    elif value_text:
        value_category = "text"
    else:
        value_category = "unknown"

    return {
        "observation_id": observation_id,
        "patient_id": patient_id,
        "encounter_id": encounter_id,
        "observation_code": observation_code,
        "observation_description": observation_description,
        "observation_system": observation_system,
        "observation_datetime": observation_datetime,
        "value_numeric": value_numeric,
        "value_unit": value_unit,
        "value_text": value_text,
        "value_category": value_category,
    }


def transform_observations(resources: list[dict[str, Any]]) -> pd.DataFrame:
    """
    Transform a list of FHIR Observation resources into a pandas DataFrame.
    """
    rows = [extract_observation_row(resource) for resource in resources]
    return pd.DataFrame(rows)


if __name__ == "__main__":
    from pathlib import Path

    from src.extract.read_ndjson import read_resource_group

    raw_dir = Path("data/raw")
    observation_resources = read_resource_group(raw_dir, "Observation")

    df_observations = transform_observations(observation_resources)

    print(df_observations.head())
    print(df_observations.info())
    # print(
    #     df_observations[
    #         [
    #             "observation_description",
    #             "value_numeric",
    #             "value_unit",
    #             "value_text",
    #             "value_category",
    #         ]
    #     ].head()
    # )
