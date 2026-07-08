SELECT COUNT(*)
FROM `{project_id}.{silver_dataset}.{silver_table}`
WHERE city IS NULL
   OR observed_date IS NULL
   OR observed_hour IS NULL
   OR temperature_c IS NULL
