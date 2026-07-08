"""Single source of truth for environment-driven configuration.

Imported both by the DAG files (parsed by Composer's scheduler/DAG
processor) and, via the same file baked into the image at
``/app/config/settings.py`` (see Dockerfile), by the ``etl.*`` runtime
scripts inside GKE pods. Keep this module free of any GCP/Kubernetes
client calls — it must be safe to import with zero credentials.
"""
import os
from pathlib import Path

import yaml

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "project-347a7b51-e6cd-40d3-9ac")
GCS_BUCKET = os.getenv("GCS_BUCKET", "us-central1-weather-project-7b4142b8-bucket")

# GKE / Composer orchestration
GKE_LOCATION = os.getenv("GKE_LOCATION", "us-central1")
GKE_CLUSTER_NAME = os.getenv("GKE_CLUSTER_NAME", "learning-cluster")
GKE_NAMESPACE = os.getenv("GKE_NAMESPACE", "default")
WEATHER_ETL_IMAGE = os.getenv(
    "WEATHER_ETL_IMAGE",
    "us-central1-docker.pkg.dev/project-347a7b51-e6cd-40d3-9ac/weather/weather-etl:v6",
)
WEATHER_POD_SERVICE_ACCOUNT = os.getenv("WEATHER_POD_SERVICE_ACCOUNT", "weather-etl")
POD_EXECUTION_TIMEOUT_MINUTES = int(os.getenv("WEATHER_POD_TIMEOUT_MINUTES", "10"))
POD_RESOURCE_REQUESTS = {"cpu": "250m", "memory": "512Mi"}
POD_RESOURCE_LIMITS = {"cpu": "1", "memory": "1Gi"}

# BigQuery — one dataset per medallion layer (migrated from a single flat
# "weather" dataset; see docs/MIGRATION.md). Table names no longer repeat
# the layer name since the dataset itself encodes it.
BIGQUERY_BRONZE_DATASET = os.getenv("BIGQUERY_BRONZE_DATASET", "weather_bronze")
BIGQUERY_BRONZE_TABLE = os.getenv("BIGQUERY_BRONZE_TABLE", "weather_raw")
BIGQUERY_SILVER_DATASET = os.getenv("BIGQUERY_SILVER_DATASET", "weather_silver")
BIGQUERY_SILVER_TABLE = os.getenv("BIGQUERY_SILVER_TABLE", "weather_clean")
BIGQUERY_GOLD_DATASET = os.getenv("BIGQUERY_GOLD_DATASET", "weather_gold")
BIGQUERY_GOLD_TABLE = os.getenv("BIGQUERY_GOLD_TABLE", "weather_daily")


def _load_cities() -> dict[str, tuple[float, float]]:
    cities_file = Path(__file__).parent / "cities.yaml"
    with open(cities_file) as f:
        raw = yaml.safe_load(f)
    return {name: (coords["lat"], coords["lon"]) for name, coords in raw.items()}


CITY_COORDINATES = _load_cities()
