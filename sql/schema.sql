DROP TABLE IF EXISTS data_quality_audit;
DROP TABLE IF EXISTS observations;
DROP TABLE IF EXISTS conditions;
DROP TABLE IF EXISTS encounters;
DROP TABLE IF EXISTS patients;

CREATE TABLE patients (
    patient_id TEXT PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    gender TEXT,
    birth_date TEXT,
    age INTEGER,
    city TEXT,
    state TEXT,
    postal_code TEXT,
    country TEXT,
    marital_status TEXT,
    is_deceased INTEGER,
    deceased_date TEXT
);

CREATE TABLE encounters (
    encounter_id TEXT PRIMARY KEY,
    patient_id TEXT,
    encounter_status TEXT,
    encounter_class TEXT,
    encounter_type TEXT,
    encounter_start TEXT,
    encounter_end TEXT,
    encounter_duration_minutes REAL,
    provider_name TEXT,
    provider_reference TEXT,
    organization_name TEXT,
    organization_reference TEXT,
    location_name TEXT,
    location_reference TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);

CREATE TABLE conditions (
    condition_id TEXT PRIMARY KEY,
    patient_id TEXT,
    encounter_id TEXT,
    condition_code TEXT,
    condition_description TEXT,
    condition_system TEXT,
    clinical_status TEXT,
    verification_status TEXT,
    onset_datetime TEXT,
    recorded_datetime TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id)
);

CREATE TABLE observations (
    observation_id TEXT PRIMARY KEY,
    patient_id TEXT,
    encounter_id TEXT,
    observation_code TEXT,
    observation_description TEXT,
    observation_system TEXT,
    observation_datetime TEXT,
    value_numeric REAL,
    value_unit TEXT,
    value_text TEXT,
    value_category TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id)
);

CREATE TABLE data_quality_audit (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_table TEXT,
    record_id TEXT,
    issue_type TEXT,
    issue_severity TEXT,
    issue_description TEXT,
    detected_at TEXT
);