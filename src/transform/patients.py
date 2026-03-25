from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd


def calculate_age(birth_date: str | None) -> int | None:
    """
    Calculate age in years from a YYYY-MM-DD birth date string.
    Returns None if birth_date is missing or invalid.
    """
    if not birth_date:
        return None

    try:
        dob = datetime.strptime(birth_date, "%Y-%m-%d")
        today = datetime.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age
    except ValueError:
        return None


def extract_patient_row(resource: dict[str, Any]) -> dict[str, Any]:
    """
    Flatten one FHIR Patient resource into a relational row.
    """
    patient_id = resource.get("id")

    name = resource.get("name", [{}])
    first_name = None
    last_name = None
    if name:
        first_name = name[0].get("given", [None])[0]
        last_name = name[0].get("family")

    gender = resource.get("gender")
    birth_date = resource.get("birthDate")
    age = calculate_age(birth_date)

    address = resource.get("address", [{}])
    city = None
    state = None
    postal_code = None
    country = None
    if address:
        city = address[0].get("city")
        state = address[0].get("state")
        postal_code = address[0].get("postalCode")
        country = address[0].get("country")

    marital_status = resource.get("maritalStatus", {}).get("text")

    deceased_date = resource.get("deceasedDateTime")
    is_deceased = 1 if deceased_date else 0

    return {
        "patient_id": patient_id,
        "first_name": first_name,
        "last_name": last_name,
        "gender": gender,
        "birth_date": birth_date,
        "age": age,
        "city": city,
        "state": state,
        "postal_code": postal_code,
        "country": country,
        "marital_status": marital_status,
        "is_deceased": is_deceased,
        "deceased_date": deceased_date,
    }


def transform_patients(resources: list[dict[str, Any]]) -> pd.DataFrame:
    """
    Transform a list of FHIR Patient resources into a pandas DataFrame.
    """
    rows = [extract_patient_row(resource) for resource in resources]
    return pd.DataFrame(rows)


if __name__ == "__main__":
    from pathlib import Path

    from src.extract.read_ndjson import read_resource_group

    raw_dir = Path("data/raw")
    patient_resources = read_resource_group(raw_dir, "Patient")

    df_patients = transform_patients(patient_resources)

    print(df_patients.head())
    print(df_patients.info())
