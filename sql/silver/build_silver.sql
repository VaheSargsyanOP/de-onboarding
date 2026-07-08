CREATE OR REPLACE TABLE
`{project_id}.{silver_dataset}.{silver_table}`
PARTITION BY observed_date
CLUSTER BY city
AS

SELECT
    city,
    observed_date,
    observed_hour,
    temperature_c,
    ingestion_time,
    batch_id,
    source
FROM
(
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY
                city,
                observed_date,
                observed_hour
            ORDER BY
                ingestion_time DESC
        ) AS rn
    FROM
        `{project_id}.{bronze_dataset}.{bronze_table}`
)

WHERE rn = 1;
