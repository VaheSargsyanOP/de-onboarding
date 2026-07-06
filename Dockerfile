FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY download_weather.py .
COPY load_weather_to_bigquery.py .
COPY dags/sql ./dags/sql

ENTRYPOINT ["python", "download_weather.py"]