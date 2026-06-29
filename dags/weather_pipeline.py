from datetime import datetime

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator


with DAG(
    dag_id="weather_pipeline",
    description="Weather ingestion pipeline",
    start_date=datetime(2026, 1, 1),
    schedule="0 6 * * *",
    catchup=False,
    max_active_runs=1,
    tags=["weather"],
) as dag:

    download_weather = BashOperator(
        task_id="download_weather",
        bash_command="""
        cd /opt/airflow/project

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
                --city Yerevan
                --date {{ ds }}

        fi
        """
)