FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Image payload: etl/ (business logic), utils/ (GCP client helpers),
# sql/ (queries), config/ (shared settings - sourced from dags/config so
# Composer and the image read the exact same constants). Deliberately NOT
# copying dags/ itself - DAG-construction code (common/, the DAG files)
# has no place in this image and must never be importable from it.
COPY etl/ ./etl
COPY utils/ ./utils
COPY sql/ ./sql
COPY dags/config ./config

ENTRYPOINT ["python", "-m"]
CMD ["etl.extract.download_weather"]