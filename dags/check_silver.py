import os

from google.cloud import bigquery

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "project-347a7b51-e6cd-40d3-9ac")
DATASET = os.getenv("BIGQUERY_DATASET", "weather")
TABLE = os.getenv("BIGQUERY_SILVER_TABLE", "weather_clean_silver")

client = bigquery.Client(project=PROJECT_ID)

table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"


def run_scalar_query(query):
    result = client.query(query).result()
    return list(result)[0][0]


# -------------------------------------------------
# 1. Row count check
# -------------------------------------------------

row_count = run_scalar_query(f"""
SELECT COUNT(*)
FROM `{table_id}`
""")

print(f"Row count: {row_count}")

if row_count == 0:
    raise RuntimeError("Quality Check Failed: Silver table is empty.")

print("✓ Row count check passed")


# -------------------------------------------------
# 2. Null check
# -------------------------------------------------

null_count = run_scalar_query(f"""
SELECT COUNT(*)
FROM `{table_id}`
WHERE city IS NULL
   OR observed_date IS NULL
   OR observed_hour IS NULL
   OR temperature_c IS NULL
""")

print(f"Null rows: {null_count}")

if null_count > 0:
    raise RuntimeError(
        f"Quality Check Failed: {null_count} rows contain NULL values."
    )

print("✓ Null check passed")


# -------------------------------------------------
# 3. Duplicate business key check
# -------------------------------------------------

duplicate_count = run_scalar_query(f"""
SELECT COUNT(*)
FROM (
    SELECT
        city,
        observed_date,
        observed_hour,
        COUNT(*) AS cnt
    FROM `{table_id}`
    GROUP BY
        city,
        observed_date,
        observed_hour
    HAVING cnt > 1
)
""")

print(f"Duplicate keys: {duplicate_count}")

if duplicate_count > 0:
    raise RuntimeError(
        f"Quality Check Failed: {duplicate_count} duplicate business keys found."
    )

print("✓ Duplicate check passed")


# -------------------------------------------------
# 4. Temperature sanity check
# -------------------------------------------------

invalid_temperature_count = run_scalar_query(f"""
SELECT COUNT(*)
FROM `{table_id}`
WHERE temperature_c < -50
   OR temperature_c > 60
""")

print(f"Invalid temperatures: {invalid_temperature_count}")

if invalid_temperature_count > 0:
    raise RuntimeError(
        f"Quality Check Failed: {invalid_temperature_count} invalid temperatures found."
    )

print("✓ Temperature range check passed")


print("---------------------------------------")
print("All Silver quality checks passed.")
print("---------------------------------------")