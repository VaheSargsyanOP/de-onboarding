CREATE OR REPLACE TABLE
`project-347a7b51-e6cd-40d3-9ac.weather.weather_daily_gold`
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
`project-347a7b51-e6cd-40d3-9ac.weather.weather_clean_silver`

GROUP BY
    city,
    observed_date;