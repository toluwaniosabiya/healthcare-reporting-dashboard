DROP VIEW IF EXISTS vw_overview_metrics;
DROP VIEW IF EXISTS vw_encounters_by_month;
DROP VIEW IF EXISTS vw_encounters_by_year;
DROP VIEW IF EXISTS vw_encounters_by_year_month;
DROP VIEW IF EXISTS vw_top_encounter_types;
DROP VIEW IF EXISTS vw_top_conditions;
DROP VIEW IF EXISTS vw_top_observation_types;
DROP VIEW IF EXISTS vw_data_quality_summary;

CREATE VIEW vw_overview_metrics AS
SELECT
    (SELECT COUNT(*) FROM patients) AS total_patients,
    (SELECT COUNT(*) FROM encounters) AS total_encounters,
    (SELECT COUNT(*) FROM conditions) AS total_conditions,
    (SELECT COUNT(*) FROM observations) AS total_observations,
    (
        SELECT ROUND(
            CAST(COUNT(*) AS REAL) / NULLIF(COUNT(DISTINCT patient_id), 0),
            2
        )
        FROM encounters
    ) AS avg_encounters_per_patient,
    (
        SELECT ROUND(AVG(encounter_duration_minutes), 2)
        FROM encounters
        WHERE encounter_duration_minutes IS NOT NULL
    ) AS avg_encounter_duration_minutes,
    (
        SELECT ROUND(
            100.0 * SUM(
                CASE
                    WHEN encounter_start IS NOT NULL
                        AND encounter_end IS NOT NULL
                        AND encounter_duration_minutes IS NOT NULL
                    THEN 1 ELSE 0
                END
            ) / NULLIF(COUNT(*), 0),
            2
        )
        FROM encounters
    ) AS encounter_data_completeness_pct,
    (SELECT COUNT(*) FROM data_quality_audit) AS total_data_quality_issues;

CREATE VIEW vw_encounters_by_month AS
SELECT
    substr(encounter_start, 6, 2) AS encounter_month,
    COUNT(*) AS encounter_count
FROM encounters
WHERE encounter_start IS NOT NULL
GROUP BY substr(encounter_start, 6, 2)
ORDER BY encounter_month;

CREATE VIEW vw_encounters_by_year AS
SELECT
    substr(encounter_start, 1, 4) AS encounter_year,
    COUNT(*) AS encounter_count
FROM encounters
WHERE encounter_start IS NOT NULL
GROUP BY substr(encounter_start, 1, 4)
ORDER BY encounter_year;

CREATE VIEW vw_encounters_by_year_month AS
SELECT
    substr(encounter_start, 1, 7) AS encounter_year_month,
    COUNT(*) AS encounter_count
FROM encounters
WHERE encounter_start IS NOT NULL
GROUP BY substr(encounter_start, 1, 7)
ORDER BY encounter_month;

CREATE VIEW vw_top_encounter_types AS
SELECT
    COALESCE(encounter_type, 'Unknown') AS encounter_type,
    COUNT(*) AS encounter_count,
    ROUND(AVG(encounter_duration_minutes), 2) AS avg_duration_minutes
FROM encounters
GROUP BY COALESCE(encounter_type, 'Unknown')
ORDER BY encounter_count DESC;

CREATE VIEW vw_top_conditions AS
SELECT
    COALESCE(condition_description, 'Unknown') AS condition_description,
    COUNT(*) AS condition_count,
    COUNT(DISTINCT patient_id) AS patient_count
FROM conditions
GROUP BY COALESCE(condition_description, 'Unknown')
ORDER BY condition_count DESC;

CREATE VIEW vw_top_observation_types AS
SELECT
    COALESCE(observation_description, 'Unknown') AS observation_description,
    value_category,
    COUNT(*) AS observation_count
FROM observations
GROUP BY
    COALESCE(observation_description, 'Unknown'),
    value_category
ORDER BY observation_count DESC;

CREATE VIEW vw_data_quality_summary AS
SELECT
    source_table,
    issue_type,
    issue_severity,
    COUNT(*) AS issue_count
FROM data_quality_audit
GROUP BY source_table, issue_type, issue_severity
ORDER BY issue_count DESC;