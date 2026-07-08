"""Per-city daily weather download DAGs.

Thin orchestration only. Download-only (no load/silver/gold/quality) -
that asymmetry with weather_pipeline.py is a pre-existing product
decision, not something this factory resolves.
"""
from datetime import datetime

from airflow import DAG
from airflow.providers.google.cloud.operators.kubernetes_engine import GKEStartPodOperator

from common.pod_defaults import common_pod_kwargs, pod_name

TENANTS = ["Yerevan", "Paris", "London"]


def build_dag(city: str) -> DAG:
    with DAG(
        dag_id=f"weather_{city.lower()}",
        description=f"Weather ingestion pipeline for {city}",
        start_date=datetime(2026, 1, 1),
        schedule="0 6 * * *",
        catchup=False,
        max_active_runs=1,
        is_paused_upon_creation=False,
        tags=["weather", "gke", "composer3"],
    ) as dag:

        GKEStartPodOperator(
            task_id="download_weather",
            name=pod_name(f"weather-download-{city.lower()}"),
            cmds=["python", "-m"],
            arguments=["etl.extract.download_weather", "--city", city, "--date", "{{ ds }}"],
            **common_pod_kwargs(pipeline_label=f"weather-{city.lower()}"),
        )

    return dag


for tenant in TENANTS:
    globals()[f"weather_{tenant.lower()}"] = build_dag(tenant)
