CREATE OR REPLACE TABLE
`project-347a7b51-e6cd-40d3-9ac.weather.weather_clean_silver`
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
        `project-347a7b51-e6cd-40d3-9ac.weather.weather_raw_bronze`
)

WHERE rn = 1;