"""Weather ETL orchestrated entirely on GKE.

Thin orchestration only - all business logic lives in etl.* (executed
inside the pods this DAG launches), never here. Task chain:
download -> load bronze -> build silver -> quality check -> build gold.

Yerevan-only, manually triggered (schedule=None) - see weather_factory.py
for the separate daily per-city download-only DAGs. This asymmetry is a
pre-existing product decision, not something this DAG resolves.
"""
from datetime import datetime

from airflow import DAG
from airflow.providers.google.cloud.operators.kubernetes_engine import GKEStartPodOperator

from common.pod_defaults import common_pod_kwargs, pod_name

POD_KWARGS = common_pod_kwargs(pipeline_label="weather-pipeline")

with DAG(
    dag_id="weather_pipeline",
    description="Weather ETL orchestrated entirely on GKE",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    is_paused_upon_creation=False,
    tags=["weather", "gke", "composer3"],
) as dag:

    download_weather = GKEStartPodOperator(
        task_id="download_weather",
        name=pod_name("weather-download"),
        cmds=["python", "-m"],
        arguments=["etl.extract.download_weather", "--city", "Yerevan", "--date", "{{ ds }}"],
        **POD_KWARGS,
    )

    load_to_bigquery = GKEStartPodOperator(
        task_id="load_to_bigquery",
        name=pod_name("weather-load"),
        cmds=["python", "-m"],
        arguments=["etl.bronze.load_bronze"],
        **POD_KWARGS,
    )

    build_silver = GKEStartPodOperator(
        task_id="build_silver",
        name=pod_name("weather-silver"),
        cmds=["python", "-m"],
        arguments=["etl.silver.build_silver"],
        **POD_KWARGS,
    )

    quality_check = GKEStartPodOperator(
        task_id="quality_check",
        name=pod_name("weather-quality"),
        cmds=["python", "-m"],
        arguments=["etl.quality.check_silver"],
        **POD_KWARGS,
    )

    build_gold = GKEStartPodOperator(
        task_id="build_gold",
        name=pod_name("weather-gold"),
        cmds=["python", "-m"],
        arguments=["etl.gold.build_gold"],
        **POD_KWARGS,
    )

    download_weather >> load_to_bigquery >> build_silver >> quality_check >> build_gold
