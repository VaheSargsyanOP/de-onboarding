"""Thin wrappers around the BigQuery client + SQL templating helper."""
import logging
from typing import Any

from google.cloud import bigquery

logger = logging.getLogger(__name__)


def get_bigquery_client(project_id: str) -> bigquery.Client:
    return bigquery.Client(project=project_id)


def render_sql(sql_text: str, **params: str) -> str:
    """Substitute ``{name}``-style placeholders in a SQL template.

    Plain str.format() rather than Jinja: the SQL is read from disk and
    executed by a standalone script running inside a GKE pod, with no
    Airflow/Jinja rendering context available there (Jinja templating
    only applies to operator arguments at the Airflow-scheduler level).
    """
    return sql_text.format(**params)


def run_query(client: bigquery.Client, sql: str) -> bigquery.table.RowIterator:
    """Execute a query and block until it completes."""
    job = client.query(sql)
    return job.result()


def run_scalar_query(client: bigquery.Client, sql: str) -> Any:
    """Execute a query and return the first column of the first row."""
    result = run_query(client, sql)
    return list(result)[0][0]


def load_json_rows(
    client: bigquery.Client,
    rows: list[dict],
    table_id: str,
    write_disposition: str = bigquery.WriteDisposition.WRITE_TRUNCATE,
) -> int:
    """Load a list of JSON-serializable rows into a BigQuery table.

    Returns the number of rows loaded.
    """
    job_config = bigquery.LoadJobConfig(write_disposition=write_disposition)
    load_job = client.load_table_from_json(rows, table_id, job_config=job_config)
    load_job.result()
    return len(rows)
