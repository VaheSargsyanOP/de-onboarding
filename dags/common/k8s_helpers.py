"""Kubernetes object builders for GKEStartPodOperator kwargs.

DAG-construction-only code: requires the ``kubernetes`` client library,
which is available in the Composer/Airflow environment but deliberately
NOT installed in the weather-etl image (see Dockerfile/requirements.txt).
Do not import this module from anything under etl/ or utils/.
"""
from kubernetes.client import models as k8s

from config import settings


def build_env_vars(**extra: str) -> list[k8s.V1EnvVar]:
    """Build the standard pod env vars as real V1EnvVar objects.

    Composer 3's pod-mutation hook crashes with
    ``AttributeError: 'dict' object has no attribute 'name'`` if env_vars
    are passed as plain dicts instead of V1EnvVar instances - do not
    "simplify" this back to dicts.
    """
    env = {
        "GOOGLE_CLOUD_PROJECT": settings.PROJECT_ID,
        "PYTHONUNBUFFERED": "1",
        **extra,
    }
    return [k8s.V1EnvVar(name=k, value=v) for k, v in env.items()]


def build_resources() -> k8s.V1ResourceRequirements:
    return k8s.V1ResourceRequirements(
        requests=settings.POD_RESOURCE_REQUESTS,
        limits=settings.POD_RESOURCE_LIMITS,
    )
