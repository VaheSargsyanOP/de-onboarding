"""Gold stage: aggregate Silver into daily business-ready summaries.

Run as: python -m etl.gold.build_gold
"""
import logging
from pathlib import Path

from config import settings
from utils.bigquery import get_bigquery_client, render_sql, run_query
from utils.logging import configure_logging

logger = logging.getLogger(__name__)

SQL_FILE = Path(__file__).resolve().parents[2] / "sql" / "gold" / "build_gold.sql"


def main():
    configure_logging()

    client = get_bigquery_client(settings.PROJECT_ID)
    sql = render_sql(
        SQL_FILE.read_text(),
        project_id=settings.PROJECT_ID,
        silver_dataset=settings.BIGQUERY_SILVER_DATASET,
        silver_table=settings.BIGQUERY_SILVER_TABLE,
        gold_dataset=settings.BIGQUERY_GOLD_DATASET,
        gold_table=settings.BIGQUERY_GOLD_TABLE,
    )

    logger.info("Building Gold table...")
    run_query(client, sql)
    logger.info("Gold table built successfully.")


if __name__ == "__main__":
    main()
