from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def get_matching_files(data_dir: str | Path, prefix: str) -> list[Path]:
    """
    Return all NDJSON files in a directory that start with the given prefix,
    sorted alphabetically.

    Example:
        prefix='Encounter' -> [Encounter.000.ndjson, Encounter.001.ndjson, ...]
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_path}")

    files = sorted(data_path.glob(f"{prefix}*.ndjson"))
    if not files:
        raise FileNotFoundError(
            f"No NDJSON files found in {data_path} with prefix '{prefix}'"
        )

    return files


def read_ndjson_file(file_path: str | Path) -> list[dict[str, Any]]:
    """
    Read one NDJSON file and return a list of JSON records.
    Skips blank lines.
    """
    file_path = Path(file_path)
    records: list[dict[str, Any]] = []

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with file_path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Invalid JSON in file {file_path} at line {line_number}: {e}"
                ) from e

    return records


def read_resource_group(data_dir: str | Path, prefix: str) -> list[dict[str, Any]]:
    """
    Read all NDJSON files for a FHIR resource group and combine them.

    Example:
        read_resource_group('data/raw', 'Observation')
    """
    files = get_matching_files(data_dir, prefix)

    all_records: list[dict[str, Any]] = []
    for file_path in files:
        records = read_ndjson_file(file_path)
        all_records.extend(records)

    return all_records


if __name__ == "__main__":
    raw_dir = Path("data/raw")

    for resource_prefix in ["Patient", "Encounter", "Condition", "Observation"]:
        try:
            records = read_resource_group(raw_dir, resource_prefix)
            print(f"{resource_prefix}: {len(records)} records loaded")
        except FileNotFoundError as e:
            print(f"{resource_prefix}: {e}")
