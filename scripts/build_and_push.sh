#!/usr/bin/env bash
# Build and push the weather-etl image for GKE (amd64), regardless of the
# local machine's architecture.
#
# GKE's node pools ("learning-cluster") run linux/amd64. A plain
# `docker build` on an arm64 dev machine (e.g. Apple Silicon) produces an
# arm64-only image that pulls fine locally but fails on GKE with
# "no match for platform in manifest" - this bit the project once
# already. Always build through this script, not a bare `docker build`.
set -euo pipefail

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-project-347a7b51-e6cd-40d3-9ac}"
REPO="us-central1-docker.pkg.dev/${PROJECT_ID}/weather/weather-etl"
TAG="${1:?Usage: scripts/build_and_push.sh <tag>}"

cd "$(dirname "$0")/.."

docker buildx build \
  --platform linux/amd64 \
  -t "${REPO}:${TAG}" \
  --push \
  .

echo "Pushed ${REPO}:${TAG}"
docker buildx imagetools inspect "${REPO}:${TAG}"
