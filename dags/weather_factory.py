import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.google.cloud.operators.kubernetes_engine import (
    GKEStartPodOperator,
)
from kubernetes.client import models as k8s


IMAGE = os.getenv(
    "WEATHER_ETL_IMAGE",
    "us-central1-docker.pkg.dev/project-347a7b51-e6cd-40d3-9ac/weather/weather-etl:v5",
)
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "project-347a7b51-e6cd-40d3-9ac")
LOCATION = os.getenv("GKE_LOCATION", "us-central1")
CLUSTER_NAME = os.getenv("GKE_CLUSTER_NAME", "learning-cluster")
NAMESPACE = os.getenv("GKE_NAMESPACE", "default")
SERVICE_ACCOUNT = os.getenv("WEATHER_POD_SERVICE_ACCOUNT", "weather-etl")


def build_dag(city):

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
            name=f"weather-download-{city.lower()}-{{{{ dag_run.logical_date.strftime('%Y%m%d%H%M%S') }}}}",
            project_id=PROJECT_ID,
            location=LOCATION,
            cluster_name=CLUSTER_NAME,
            namespace=NAMESPACE,
            service_account_name=SERVICE_ACCOUNT,
            image=IMAGE,
            cmds=["bash", "-c"],
            arguments=[f"""
python /app/download_weather.py --city {city} --date "{{{{ ds }}}}"
"""],
            env_vars=[
                k8s.V1EnvVar(name="GOOGLE_CLOUD_PROJECT", value=PROJECT_ID),
                k8s.V1EnvVar(name="PYTHONUNBUFFERED", value="1"),
            ],
            labels={"app": "weather-etl", "pipeline": f"weather-{city.lower()}"},
            container_resources=k8s.V1ResourceRequirements(
                requests={"cpu": "250m", "memory": "512Mi"},
                limits={"cpu": "1", "memory": "1Gi"},
            ),
            is_delete_operator_pod=True,
            get_logs=False,
            execution_timeout=timedelta(minutes=10),
            image_pull_policy="Always",
        )

    return dag


TENANTS = [
    "Yerevan",
    "Paris",
    "London",
]

for tenant in TENANTS:
    globals()[f"weather_{tenant.lower()}"] = build_dag(tenant)