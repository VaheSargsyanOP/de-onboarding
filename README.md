# Weather ETL on Cloud Composer 3 + GKE

This repository is structured for Cloud Composer 3 to orchestrate the Weather ETL entirely on GKE using GKEStartPodOperator. Nothing runs on the Composer worker itself - every ETL step (download, load, build silver, quality check, build gold) executes as its own pod on GKE.

## What changed
- The main pipeline DAG and the factory DAG both use GKEStartPodOperator exclusively (no BashOperator/KubernetesPodOperator/local execution).
- The container image includes only the ETL scripts and SQL assets required by the pods (Airflow itself is NOT installed in the image - it isn't needed there).
- The Dockerfile copies `dags/` as a single unit so every script's relative SQL path resolves consistently at `/app/dags/sql/...`.
- The repository uses the v5 Artifact Registry image consistently everywhere (DAGs, `weather-job.yaml`).
- `load_weather_to_bigquery.py` loads into `weather_raw_bronze`, matching the table `build_silver.sql` actually reads from (previously mismatched with `weather_raw_stage`, so Silver was building from an empty/nonexistent table).
- `download_weather.py` no longer shells out to re-run the BigQuery load itself - that step belongs solely to the DAG's `load_to_bigquery` task.
- `k8s/airflow-rbac.yaml` no longer grants the ETL pod's own ServiceAccount pod-create/secret-read permissions it never uses; it now only carries the Workload Identity annotation the pod needs to call BigQuery/GCS.

## Required IAM bindings (cannot be automated from this repo)
1. **GKE node pool / Artifact Registry access** - whichever service account backs your GKE node pool needs `roles/artifactregistry.reader` on the `weather` repository, or pulls will fail with `ImagePullBackOff`:
   ```
   gcloud artifacts repositories add-iam-policy-binding weather \
     --location=us-central1 \
     --member="serviceAccount:<NODE_POOL_SA>" \
     --role="roles/artifactregistry.reader"
   ```
2. **Composer -> GKE control plane** - the Composer environment's service account needs `roles/container.developer` on the project so GKEStartPodOperator can create/watch/delete pods on the target cluster.
3. **Workload Identity for the ETL pods** - create a Google Service Account, bind it to the `weather-etl` Kubernetes ServiceAccount, and grant it `roles/bigquery.dataEditor`, `roles/bigquery.jobUser`, and `roles/storage.objectAdmin` (scoped to the weather bucket). See comments in `k8s/airflow-rbac.yaml`.
4. Confirm the GKE cluster has Workload Identity Federation enabled (`--workload-pool=PROJECT_ID.svc.id.goog`).

## Deployment notes
- Build and push the image to Artifact Registry (see commands below).
- Apply `k8s/airflow-rbac.yaml`.
- Ensure the Composer environment can reach the GKE cluster and the GKE API (see IAM bindings above).
- Set the DAG environment variables in Composer.

## Required Composer environment variables
- WEATHER_ETL_IMAGE=us-central1-docker.pkg.dev/project-347a7b51-e6cd-40d3-9ac/weather/weather-etl:v5
- GOOGLE_CLOUD_PROJECT=project-347a7b51-e6cd-40d3-9ac
- GKE_LOCATION=us-central1
- GKE_CLUSTER_NAME=learning-cluster (verify this matches your actual cluster name)
- GKE_NAMESPACE=default
- WEATHER_POD_SERVICE_ACCOUNT=weather-etl
