from datetime import datetime

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator


with DAG(
    dag_id="weather_pipeline",
    description="Weather ingestion pipeline",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    tags=["weather"],
) as dag:

    download_weather = BashOperator(
        task_id="download_weather",
        cwd="{{ dag.folder }}",
        bash_command="""
        echo "Logical date: {{ ds }}"
        echo "Run ID: {{ run_id }}"
        echo "Dag Run Config: {{ dag_run.conf }}"
        echo "--------------------------------"

        if [ -n "{{ dag_run.conf.get('date_from', '') }}" ] && \
           [ -n "{{ dag_run.conf.get('date_to', '') }}" ]; then

            python download_weather.py \
                --city Yerevan \
                --date_from {{ dag_run.conf.get('date_from') }} \
                --date_to {{ dag_run.conf.get('date_to') }}

        elif [ -n "{{ dag_run.conf.get('date', '') }}" ]; then

            python download_weather.py \
                --city Yerevan \
                --date {{ dag_run.conf.get('date') }}

        else

            python download_weather.py \
                --city Yerevan \
                --date {{ ds }}

        fi
        """,
    )

    load_to_bigquery = BashOperator(
        task_id="load_to_bigquery",
        cwd="{{ dag.folder }}",
        bash_command="""
        echo "Loading weather into BigQuery..."
        python load_weather_to_bigquery.py
        """,
    )

    build_silver = BashOperator(
    task_id="build_silver",
    cwd="{{ dag.folder }}",
    bash_command="""
    bq query \
        --use_legacy_sql=false \
        < sql/build_silver.sql
    """,
    )
    
    quality_check = BashOperator(
    task_id="quality_check",
    cwd="{{ dag.folder }}",
    bash_command="""
    echo "Running Silver quality checks..."
    python check_silver.py
    """,
    )
    
    build_gold = BashOperator(
    task_id="build_gold",
    cwd="{{ dag.folder }}",
    bash_command="""
    echo "Building Gold table..."
    python build_gold.py
    """,
    )   

    download_weather >> load_to_bigquery >> build_silver >> quality_check >> build_gold