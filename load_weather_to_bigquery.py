import json

from pathlib import Path
from datetime import datetime

from google.cloud import storage
from google.cloud import bigquery


PROJECT_ID = "project-347a7b51-e6cd-40d3-9ac"

DATASET = "weather"

STAGE_TABLE = "weather_raw_stage"

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


# -------------------------------------------------------
# Execute build_silver.sql
# -------------------------------------------------------

sql_file = Path(__file__).parent / "dags" / "sql" / "build_silver.sql"

with open(sql_file, "r") as f:
    sql = f.read()

print("Building Silver table...")

query_job = client_bq.query(sql)

query_job.result()

print("Silver table built successfully.")