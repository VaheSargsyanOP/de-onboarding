from datetime import datetime

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator


def build_dag(city):

    with DAG(
        dag_id=f"weather_{city.lower()}",
        description=f"Weather ingestion pipeline for {city}",
        start_date=datetime(2026, 1, 1),
        schedule="0 6 * * *",
        catchup=False,
        max_active_runs=1,
        tags=["weather"],
    ) as dag:

        BashOperator(
            task_id="download_weather",
            params={
                "city": city,
            },
            bash_command="""
            cd /opt/airflow/project

            echo "City: {{ params.city }}"
            echo "Logical date: {{ ds }}"
            echo "Run ID: {{ run_id }}"
            echo "Dag Run Config: {{ dag_run.conf }}"
            echo "--------------------------------"

            if [ -n "{{ dag_run.conf.get('date_from', '') }}" ] && \
               [ -n "{{ dag_run.conf.get('date_to', '') }}" ]; then

                python download_weather.py \
                    --city {{ params.city }} \
                    --date_from {{ dag_run.conf.get('date_from') }} \
                    --date_to {{ dag_run.conf.get('date_to') }}

            elif [ -n "{{ dag_run.conf.get('date', '') }}" ]; then

                python download_weather.py \
                    --city {{ params.city }} \
                    --date {{ dag_run.conf.get('date') }}

            else

                python download_weather.py \
                    --city {{ params.city }} \
                    --date {{ ds }}

            fi
            """,
        )

    return dag


TENANTS = [
    "Yerevan",
    "Paris",
    "London",
]

for tenant in TENANTS:
    globals()[f"weather_{tenant.lower()}"] = build_dag(tenant)