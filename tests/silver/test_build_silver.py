from etl.silver.build_silver import SQL_FILE
from utils.bigquery import render_sql


def test_sql_file_exists_and_is_readable():
    assert SQL_FILE.exists(), f"expected {SQL_FILE} to exist"


def test_sql_renders_with_configured_table_names():
    sql = render_sql(
        SQL_FILE.read_text(),
        project_id="test-project",
        bronze_dataset="test_bronze",
        bronze_table="bronze_t",
        silver_dataset="test_silver",
        silver_table="silver_t",
    )
    assert "test-project.test_silver.silver_t" in sql
    assert "test-project.test_bronze.bronze_t" in sql
    assert "{" not in sql and "}" not in sql
