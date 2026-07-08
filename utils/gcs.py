"""Thin wrappers around the GCS client used by extract/bronze stages."""
import json
import logging
from typing import Iterator

from google.cloud import storage

logger = logging.getLogger(__name__)


def get_storage_client(project_id: str) -> storage.Client:
    return storage.Client(project=project_id)


def upload_file(client: storage.Client, bucket_name: str, source_file: str, destination_blob: str) -> None:
    """Upload a local file to Google Cloud Storage."""
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob)
    blob.upload_from_filename(source_file)
    logger.info("Uploaded to gs://%s/%s", bucket_name, destination_blob)


def iter_json_blobs(client: storage.Client, bucket_name: str, prefix: str) -> Iterator[dict]:
    """Yield parsed JSON payloads for every ``.json`` blob under ``prefix``."""
    bucket = client.bucket(bucket_name)
    for blob in bucket.list_blobs(prefix=prefix):
        if not blob.name.endswith(".json"):
            continue
        logger.info("Reading %s", blob.name)
        yield json.loads(blob.download_as_text())
