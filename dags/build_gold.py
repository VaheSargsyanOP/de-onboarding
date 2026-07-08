import os

from google.cloud import bigquery

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "project-347a7b51-e6cd-40d3-9ac")

client = bigquery.Client(project=PROJECT_ID)

sql_file = os.path.join(
    os.path.dirname(__file__),
    "sql",
    "build_gold.sql",
)

with open(sql_file) as f:
    query = f.read()

print("Building Gold table...")

job = client.query(query)

job.result()

print("Gold table built successfully.")