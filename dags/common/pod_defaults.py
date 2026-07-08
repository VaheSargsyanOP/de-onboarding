"""Shared GKEStartPodOperator kwargs and pod naming for all weather DAGs.

Centralizes the settings every task needs so DAG files stay thin
orchestration. See docs/MIGRATION.md invariants: get_logs=False +
execution_timeout is a deliberate fix for a Composer 3 log-watch hang -
do not revert to get_logs=True.
"""
from datetime import timedelta

from config import settings

from common.k8s_helpers import build_env_vars, build_resources


def pod_name(prefix: str) -> str:
    """Build a Jinja-templated pod name, e.g. "weather-download-{{ ... }}".

    Deliberately NOT an f-string: embedding literal Jinja `{{ }}` braces
    inside an f-string requires quadruple-brace escaping (`{{{{ }}}}`),
    which is easy to get wrong. Plain concatenation avoids that entirely.
    """
    return prefix + "-{{ dag_run.logical_date.strftime('%Y%m%d%H%M%S') }}"


def common_pod_kwargs(pipeline_label: str) -> dict:
    """Return the GKEStartPodOperator kwargs shared by every task.

    `pipeline_label` is used only for the `pipeline` pod label
    (observability), e.g. "weather-pipeline" or "weather-yerevan".
    """
    return {
        "project_id": settings.PROJECT_ID,
        "location": settings.GKE_LOCATION,
        "cluster_name": settings.GKE_CLUSTER_NAME,
        "namespace": settings.GKE_NAMESPACE,
        "service_account_name": settings.WEATHER_POD_SERVICE_ACCOUNT,
        "image": settings.WEATHER_ETL_IMAGE,
        "get_logs": False,
        "is_delete_operator_pod": True,
        "image_pull_policy": "Always",
        "execution_timeout": timedelta(minutes=settings.POD_EXECUTION_TIMEOUT_MINUTES),
        "labels": {"app": "weather-etl", "pipeline": pipeline_label},
        "container_resources": build_resources(),
        "env_vars": build_env_vars(),
    }
