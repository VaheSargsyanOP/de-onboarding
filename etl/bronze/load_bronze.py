"""Bronze stage: load raw GCS weather payloads into the bronze BigQuery table.

Run as: python -m etl.bronze.load_bronze

Loads only - does NOT build Silver. (Previously this script also re-ran
build_silver.sql itself, duplicating the DAG's separate build_silver task;
etl.silver.build_silver is now the single place Silver gets built.)
"""
import logging
from datetime import datetime

from config import settings
from utils.bigquery import get_bigquery_client, load_json_rows
from utils.gcs import get_storage_client, iter_json_blobs
from utils.logging import configure_logging

logger = logging.getLogger(__name__)

RAW_PREFIX = "raw/weather/"


def parse_bronze_rows(payload: dict) -> list[dict]:
    """Flatten one raw weather JSON payload into bronze table rows."""
    metadata = payload["metadata"]
    hourly = payload["weather_data"]["hourly"]

    rows = []
    for time_str, temp in zip(hourly["time"], hourly["temperature_2m"]):
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
    return rows


def main():
    configure_logging()

    storage_client = get_storage_client(settings.PROJECT_ID)
    bq_client = get_bigquery_client(settings.PROJECT_ID)

    rows = []
    for payload in iter_json_blobs(storage_client, settings.GCS_BUCKET, RAW_PREFIX):
        rows.extend(parse_bronze_rows(payload))

    if not rows:
        raise RuntimeError("No weather records found in GCS.")

    bronze_table_id = f"{settings.PROJECT_ID}.{settings.BIGQUERY_BRONZE_DATASET}.{settings.BIGQUERY_BRONZE_TABLE}"
    logger.info("Loading data into bronze table %s...", bronze_table_id)
    loaded = load_json_rows(bq_client, rows, bronze_table_id)
    logger.info("Loaded %d rows into bronze.", loaded)


if __name__ == "__main__":
    main()
