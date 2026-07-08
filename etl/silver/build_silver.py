"""Silver stage: dedupe bronze rows into the clean Silver table.

Run as: python -m etl.silver.build_silver

This is the single place Silver gets built - previously
`load_weather_to_bigquery.py` (now etl.bronze.load_bronze) also ran this
same SQL itself, so Silver was built twice per pipeline run (once inside
the bronze-load pod, once again in the DAG's dedicated build_silver task).
"""
import logging
from pathlib import Path

from config import settings
from utils.bigquery import get_bigquery_client, render_sql, run_query
from utils.logging import configure_logging

logger = logging.getLogger(__name__)

# etl/silver/build_silver.py -> parents[2] is the app/repo root containing sql/.
SQL_FILE = Path(__file__).resolve().parents[2] / "sql" / "silver" / "build_silver.sql"


def main():
    configure_logging()

    client = get_bigquery_client(settings.PROJECT_ID)
    sql = render_sql(
        SQL_FILE.read_text(),
        project_id=settings.PROJECT_ID,
        bronze_dataset=settings.BIGQUERY_BRONZE_DATASET,
        bronze_table=settings.BIGQUERY_BRONZE_TABLE,
        silver_dataset=settings.BIGQUERY_SILVER_DATASET,
        silver_table=settings.BIGQUERY_SILVER_TABLE,
    )

    logger.info("Building Silver table...")
    run_query(client, sql)
    logger.info("Silver table built successfully.")


if __name__ == "__main__":
    main()
