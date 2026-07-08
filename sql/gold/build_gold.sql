CREATE OR REPLACE TABLE
`{project_id}.{gold_dataset}.{gold_table}`
PARTITION BY observed_date
CLUSTER BY city
AS

SELECT
    city,
    observed_date,

    MIN(temperature_c) AS min_temp,
    MAX(temperature_c) AS max_temp,
    AVG(temperature_c) AS avg_temp,
    COUNT(*) AS hourly_records

FROM
`{project_id}.{silver_dataset}.{silver_table}`

GROUP BY
    city,
    observed_date;
