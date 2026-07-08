SELECT COUNT(*)
FROM (
    SELECT
        city,
        observed_date,
        observed_hour,
        COUNT(*) AS cnt
    FROM `{project_id}.{silver_dataset}.{silver_table}`
    GROUP BY
        city,
        observed_date,
        observed_hour
    HAVING cnt > 1
)
