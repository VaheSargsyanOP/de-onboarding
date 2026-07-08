SELECT COUNT(*)
FROM `{project_id}.{silver_dataset}.{silver_table}`
WHERE temperature_c < -50
   OR temperature_c > 60
