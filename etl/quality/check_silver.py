"""Quality stage: validate the Silver table before Gold is built.

Run as: python -m etl.quality.check_silver

Checks: row count, nulls in required columns, duplicate business keys
(city, observed_date, observed_hour), and temperature sanity bounds.
"""
import logging
from pathlib import Path

from config import settings
from utils.bigquery import get_bigquery_client, render_sql, run_scalar_query
from utils.logging import configure_logging

logger = logging.getLogger(__name__)

SQL_DIR = Path(__file__).resolve().parents[2] / "sql" / "quality"

MIN_VALID_TEMPERATURE_C = -50
MAX_VALID_TEMPERATURE_C = 60


def evaluate_quality(row_count: int, null_count: int, duplicate_count: int, invalid_temperature_count: int) -> None:
    """Raise RuntimeError on the first failing check; otherwise return None.

    Pure function - no BigQuery calls - so every pass/fail combination is
    directly unit-testable.
    """
    if row_count == 0:
        raise RuntimeError("Quality Check Failed: Silver table is empty.")

    if null_count > 0:
        raise RuntimeError(f"Quality Check Failed: {null_count} rows contain NULL values.")

    if duplicate_count > 0:
        raise RuntimeError(f"Quality Check Failed: {duplicate_count} duplicate business keys found.")

    if invalid_temperature_count > 0:
        raise RuntimeError(f"Quality Check Failed: {invalid_temperature_count} invalid temperatures found.")


def _render(filename: str) -> str:
    sql = (SQL_DIR / filename).read_text()
    return render_sql(
        sql,
        project_id=settings.PROJECT_ID,
        silver_dataset=settings.BIGQUERY_SILVER_DATASET,
        silver_table=settings.BIGQUERY_SILVER_TABLE,
    )


def main():
    configure_logging()
    client = get_bigquery_client(settings.PROJECT_ID)

    row_count = run_scalar_query(client, _render("row_count.sql"))
    logger.info("Row count: %d", row_count)

    null_count = run_scalar_query(client, _render("null_check.sql"))
    logger.info("Null rows: %d", null_count)

    duplicate_count = run_scalar_query(client, _render("duplicate_keys.sql"))
    logger.info("Duplicate keys: %d", duplicate_count)

    invalid_temperature_count = run_scalar_query(client, _render("temperature_range.sql"))
    logger.info("Invalid temperatures: %d", invalid_temperature_count)

    evaluate_quality(row_count, null_count, duplicate_count, invalid_temperature_count)

    logger.info("All Silver quality checks passed.")


if __name__ == "__main__":
    main()
