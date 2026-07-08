# Weather ETL on Cloud Composer 3 + GKE

Weather ingestion, transformation, and quality-checking pipeline,
orchestrated entirely by Cloud Composer 3 (Airflow 2.11) using
`GKEStartPodOperator`. Every ETL step runs as its own pod on GKE —
nothing executes on the Composer worker except DAG orchestration itself.

## Architecture

```
Open-Meteo API --> extract (GCS raw) --> bronze (BigQuery) --> silver (dedup) --> quality gate --> gold (aggregates)
```

Each stage is a standalone, importable Python module with a `main()`
entrypoint — no stage has module-scope side effects, so every stage can
be unit-tested without touching BigQuery/GCS (see `tests/`) and safely
imported by anything (a linter, a test runner, or — critically — by
accident, which is exactly what caused a real incident this repo's
structure is designed to prevent; see "Why `dags/` only holds thin
orchestration" below).

## Project structure

```
dags/                  # Synced to Composer's DAGs GCS folder. Thin orchestration only.
├── weather_pipeline.py   # Yerevan-only, 5-task, manually triggered (schedule=None)
├── weather_factory.py    # 3 per-city download-only DAGs, daily @ 06:00 UTC
├── common/               # DAG-construction helpers (kubernetes client objects) - never shipped in the image
│   ├── pod_defaults.py     # shared GKEStartPodOperator kwargs
│   └── k8s_helpers.py      # V1EnvVar / V1ResourceRequirements builders
└── config/               # Shared settings - synced to Composer AND copied into the image
    ├── settings.py          # single source of truth: env vars, city coords, resource limits
    └── cities.yaml

etl/                   # Business logic. Container-image payload; NEVER synced to Composer.
├── extract/download_weather.py   # Open-Meteo -> GCS (raw JSON, Hive-partitioned path)
├── bronze/load_bronze.py         # GCS -> BigQuery bronze table (load only)
├── silver/build_silver.py        # bronze -> silver (dedup by city/date/hour, latest ingestion_time wins)
├── quality/check_silver.py       # row count / null / duplicate / temperature-range checks
└── gold/build_gold.py            # silver -> daily min/max/avg aggregates

utils/                 # GCP client wrappers shared by etl/* (bigquery.py, gcs.py, logging.py)
sql/                   # One transformation per file: silver/, gold/, quality/
tests/                 # pytest - pure-function unit tests, zero GCP credentials required
docs/MIGRATION.md       # BigQuery + Composer live-cutover runbook (not part of this repo's normal deploy path)
k8s/airflow-rbac.yaml   # weather-etl ServiceAccount + Workload Identity annotation
weather-job.yaml        # standalone kubectl-apply smoke-test Job (bypasses Airflow entirely)
scripts/build_and_push.sh
```

## Why `dags/` only holds thin orchestration

Composer's DAG file processor imports **every** `.py` file it finds in
the synced `dags/` GCS folder, looking for DAG objects. If a non-DAG
script with real module-scope side effects (a BigQuery `CREATE OR
REPLACE TABLE`, a GCS load job, ...) ends up in that folder, Airflow
silently re-executes it on every parse cycle (roughly every 30 seconds).

This happened for real on this project: raw ETL scripts were synced
directly into the DAGs folder and got imported/re-executed repeatedly.
The fix has two layers:

1. Every `etl/*` module has a real `main()` function behind
   `if __name__ == "__main__":` — nothing executes on import, so even if
   one of these files ended up in the DAGs folder again, it would be
   inert.
2. `etl/`, `utils/`, and `sql/` are never copied into `dags/` and never
   synced to Composer at all — only `dags/weather_pipeline.py`,
   `dags/weather_factory.py`, `dags/common/`, and `dags/config/` are.
   `dags/.airflowignore` additionally excludes `common/`/`config/` from
   DAG-file parsing as a second layer of defense.

## Known asymmetry (by design, not a bug)

`weather_pipeline` (Yerevan-only, full bronze→silver→quality→gold,
manually triggered) and `weather_factory` (Yerevan/Paris/London,
download-only, daily cron) are intentionally different in scope. Only
Yerevan gets the full downstream processing today; Paris/London data
lands in GCS/bronze but isn't carried through silver/gold on a schedule.
This is a pre-existing product decision, not something to silently
"fix" — extending full processing to all three cities is a real product
change that should be a deliberate, separate decision.

## Local development

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest tests/ -v
```

Tests run with zero GCP credentials — they exercise pure functions
(`parse_bronze_rows`, `evaluate_quality`, `blob_path_for`, `render_sql`)
and mock the GCS/BigQuery client boundaries.

`docker-compose.yaml` + `config/airflow.cfg` provide a local Airflow
stack for DAG-authoring convenience only — it is not used for
production deployment (Composer 3 manages that).

## Docker build

**Always build for `linux/amd64`**, regardless of your local machine's
architecture — GKE's node pools run amd64, and a plain `docker build` on
an arm64 dev machine (e.g. Apple Silicon) produces an image that pulls
fine locally but fails on GKE with `no match for platform in manifest`.

```bash
scripts/build_and_push.sh v6
```

## Required IAM bindings

1. **Artifact Registry read** — the GKE node pool's service account needs `roles/artifactregistry.reader` on the `weather` repo, or pod creation fails with `ImagePullBackOff`:
   ```bash
   gcloud artifacts repositories add-iam-policy-binding weather \
     --location=us-central1 --member="serviceAccount:<NODE_POOL_SA>" \
     --role="roles/artifactregistry.reader"
   ```
2. **Composer → GKE control plane** — Composer's service account needs `roles/container.developer` on the project so `GKEStartPodOperator` can create/watch/delete pods.
3. **Workload Identity for the ETL pods** — a GSA bound to the `weather-etl` KSA with `roles/bigquery.dataEditor`, `roles/bigquery.jobUser`, `roles/storage.objectAdmin`. See `k8s/airflow-rbac.yaml`.
4. Confirm the GKE cluster has Workload Identity Federation enabled (`--workload-pool=PROJECT_ID.svc.id.goog`).

## Required Composer environment variables

- `WEATHER_ETL_IMAGE` — e.g. `us-central1-docker.pkg.dev/<project>/weather/weather-etl:v6`
- `GOOGLE_CLOUD_PROJECT`
- `GKE_LOCATION` (default `us-central1`)
- `GKE_CLUSTER_NAME` (default `learning-cluster` — verify this matches your actual cluster)
- `GKE_NAMESPACE` (default `default`)
- `WEATHER_POD_SERVICE_ACCOUNT` (default `weather-etl`)
- `BIGQUERY_BRONZE_DATASET` / `BIGQUERY_SILVER_DATASET` / `BIGQUERY_GOLD_DATASET` (defaults: `weather_bronze`/`weather_silver`/`weather_gold`)
- `BIGQUERY_BRONZE_TABLE` / `BIGQUERY_SILVER_TABLE` / `BIGQUERY_GOLD_TABLE` (defaults: `weather_raw`/`weather_clean`/`weather_daily`)

All of the above have working defaults baked into `dags/config/settings.py`; env vars only need to be set in Composer to override a default.

## BigQuery layout

One dataset per medallion layer — `weather_bronze.weather_raw`,
`weather_silver.weather_clean`, `weather_gold.weather_daily` — all
partitioned `BY observed_date` (DAY) and clustered `BY city`. Migrated
from a single flat `weather` dataset on 2026-07-08; see
`docs/MIGRATION.md` for the executed runbook (the old dataset has since
been decommissioned).

## Deploying to Composer / GKE

See `docs/MIGRATION.md` for the full step-by-step runbook (BigQuery
dataset setup, image build/push, Composer DAGs-folder sync, verification,
rollback) and its executed history. Short version for a future change:

```bash
scripts/build_and_push.sh v6
kubectl apply -f k8s/airflow-rbac.yaml
gsutil -m rsync -r dags/ gs://<composer-bucket>/dags/
gcloud composer environments run <env> --location=<region> dags list-import-errors
```

## Troubleshooting

- **`ImagePullBackOff`** — almost always missing `roles/artifactregistry.reader` on the node pool SA, or an image built for the wrong CPU architecture. Check `kubectl describe pod <pod>` for the exact containerd error.
- **DAG parses but pods never get created** — check Composer's service account has `roles/container.developer`.
- **Task stuck in `running` for exactly ~5 minutes, no error logged, pod already shows `Completed` in `kubectl`** — this is a known Composer 3 log-watch hang when `get_logs=True` is combined with `is_delete_operator_pod=True`; this repo's DAGs already set `get_logs=False` + `execution_timeout=timedelta(minutes=10)` to avoid it. Do not revert that.
- **`AttributeError: 'dict' object has no attribute 'name'`** during pod construction — `env_vars` were passed as plain dicts instead of `kubernetes.client.models.V1EnvVar` objects; use `dags/common/k8s_helpers.build_env_vars()`.
- **Silver/Gold tables look stale or empty** — check `BIGQUERY_BRONZE_TABLE`/`BIGQUERY_SILVER_TABLE` in `dags/config/settings.py` actually match the tables your SQL reads from; a past bug had these silently pointing at different tables (`weather_raw_stage` vs `weather_raw_bronze`).
