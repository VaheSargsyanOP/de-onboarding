import os

from google.cloud import bigquery


client = bigquery.Client()

sql_file = os.path.join(
    os.path.dirname(__file__),
    "sql",
    "build_gold.sql"
)

with open(sql_file) as f:
    query = f.read()

print("Building Gold table...")

job = client.query(query)

job.result()

print("Gold table built successfully.")