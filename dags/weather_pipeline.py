import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.google.cloud.operators.kubernetes_engine import (
    GKEStartPodOperator,
)
from kubernetes.client import models as k8s

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "project-347a7b51-e6cd-40d3-9ac")
LOCATION = os.getenv("GKE_LOCATION", "us-central1")
CLUSTER_NAME = os.getenv("GKE_CLUSTER_NAME", "learning-cluster")
IMAGE = os.getenv(
    "WEATHER_ETL_IMAGE",
    "us-central1-docker.pkg.dev/project-347a7b51-e6cd-40d3-9ac/weather/weather-etl:v5",
)
NAMESPACE = os.getenv("GKE_NAMESPACE", "default")
SERVICE_ACCOUNT = os.getenv("WEATHER_POD_SERVICE_ACCOUNT", "weather-etl")

COMMON_POD_KWARGS = {
    "project_id": PROJECT_ID,
    "location": LOCATION,
    "cluster_name": CLUSTER_NAME,
    "namespace": NAMESPACE,
    "service_account_name": SERVICE_ACCOUNT,
    "image": IMAGE,
    "get_logs": False,
    "is_delete_operator_pod": True,
    "image_pull_policy": "Always",
    "execution_timeout": timedelta(minutes=10),
    "labels": {"app": "weather-etl", "pipeline": "weather-pipeline"},
    "container_resources": k8s.V1ResourceRequirements(
        requests={"cpu": "250m", "memory": "512Mi"},
        limits={"cpu": "1", "memory": "1Gi"},
    ),
    "env_vars": [
        k8s.V1EnvVar(name="GOOGLE_CLOUD_PROJECT", value=PROJECT_ID),
        k8s.V1EnvVar(name="PYTHONUNBUFFERED", value="1"),
    ],
}

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
        name="weather-download-{{ dag_run.logical_date.strftime('%Y%m%d%H%M%S') }}",
        cmds=["bash", "-c"],
        arguments=[
            """
python /app/download_weather.py \
    --city Yerevan \
    --date "{{ ds }}"
"""
        ],
        **COMMON_POD_KWARGS,
    )

    load_to_bigquery = GKEStartPodOperator(
        task_id="load_to_bigquery",
        name="weather-load-{{ dag_run.logical_date.strftime('%Y%m%d%H%M%S') }}",
        cmds=["python"],
        arguments=["/app/load_weather_to_bigquery.py"],
        **COMMON_POD_KWARGS,
    )

    build_silver = GKEStartPodOperator(
        task_id="build_silver",
        name="weather-silver-{{ dag_run.logical_date.strftime('%Y%m%d%H%M%S') }}",
        cmds=["bash", "-c"],
        arguments=[
            """
python - <<'PY'
from pathlib import Path
from google.cloud import bigquery

sql = Path('/app/dags/sql/build_silver.sql').read_text()
client = bigquery.Client()
client.query(sql).result()
print('Silver table built.')
PY
"""
        ],
        **COMMON_POD_KWARGS,
    )

    quality_check = GKEStartPodOperator(
        task_id="quality_check",
        name="weather-quality-{{ dag_run.logical_date.strftime('%Y%m%d%H%M%S') }}",
        cmds=["python"],
        arguments=["/app/dags/check_silver.py"],
        **COMMON_POD_KWARGS,
    )

    build_gold = GKEStartPodOperator(
        task_id="build_gold",
        name="weather-gold-{{ dag_run.logical_date.strftime('%Y%m%d%H%M%S') }}",
        cmds=["python"],
        arguments=["/app/dags/build_gold.py"],
        **COMMON_POD_KWARGS,
    )

    (
        download_weather
        >> load_to_bigquery
        >> build_silver
        >> quality_check
        >> build_gold
    )