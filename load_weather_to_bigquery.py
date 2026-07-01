import json

from datetime import datetime

from google.cloud import storage
from google.cloud import bigquery


PROJECT_ID = "project-347a7b51-e6cd-40d3-9ac"

DATASET = "weather"

STAGE_TABLE = "weather_raw_stage"
BRONZE_TABLE = "weather_raw_bronze"

BUCKET = "us-central1-weather-project-7b4142b8-bucket"


client_storage = storage.Client()
client_bq = bigquery.Client()

bucket = client_storage.bucket(BUCKET)

blobs = bucket.list_blobs(prefix="raw/weather/")


rows = []


for blob in blobs:

    if not blob.name.endswith(".json"):
        continue

    print(f"Reading {blob.name}")

    data = json.loads(blob.download_as_text())

    metadata = data["metadata"]

    hourly = data["weather_data"]["hourly"]

    for time_str, temp in zip(
        hourly["time"],
        hourly["temperature_2m"]
    ):

        dt = datetime.fromisoformat(time_str)

        rows.append(
            {
                "city": metadata["city"],
                "observed_date": dt.date().isoformat(),
                "observed_hour": dt.hour,
                "temperature_c": temp,
                "ingestion_time": metadata["ingestion_time"],
                "batch_id": metadata["batch_id"],
                "source": metadata["source"],
            }
        )


if not rows:
    raise RuntimeError("No weather records found in GCS.")


stage_table_id = (
    f"{PROJECT_ID}.{DATASET}.{STAGE_TABLE}"
)

bronze_table_id = (
    f"{PROJECT_ID}.{DATASET}.{BRONZE_TABLE}"
)


print("Loading data into staging table...")

job_config = bigquery.LoadJobConfig(
    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
)

load_job = client_bq.load_table_from_json(
    rows,
    stage_table_id,
    job_config=job_config,
)

load_job.result()

print(f"Loaded {len(rows)} rows into staging.")


merge_query = f"""
MERGE `{bronze_table_id}` T

USING (

SELECT
    city,
    observed_date,
    observed_hour,
    ANY_VALUE(temperature_c) AS temperature_c,
    MAX(ingestion_time) AS ingestion_time,
    ANY_VALUE(batch_id) AS batch_id,
    ANY_VALUE(source) AS source

FROM `{stage_table_id}`

GROUP BY
    city,
    observed_date,
    observed_hour

) S

ON
    T.city = S.city
    AND T.observed_date = S.observed_date
    AND T.observed_hour = S.observed_hour

WHEN MATCHED THEN
UPDATE SET
    temperature_c = S.temperature_c,
    ingestion_time = S.ingestion_time,
    batch_id = S.batch_id,
    source = S.source

WHEN NOT MATCHED THEN
INSERT (
    city,
    observed_date,
    observed_hour,
    temperature_c,
    ingestion_time,
    batch_id,
    source
)

VALUES (
    S.city,
    S.observed_date,
    S.observed_hour,
    S.temperature_c,
    S.ingestion_time,
    S.batch_id,
    S.source
)
"""


print("Running MERGE...")

merge_job = client_bq.query(merge_query)

merge_job.result()

print("Merge completed successfully.")