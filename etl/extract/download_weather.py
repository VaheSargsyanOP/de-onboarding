"""Extract stage: fetch weather data from Open-Meteo and land it raw in GCS.

Run as: python -m etl.extract.download_weather --city Yerevan --date 2026-07-08
"""
import argparse
import json
import logging
import os
import uuid
from datetime import date, datetime, timedelta, timezone

import requests
from tenacity import retry, stop_after_attempt, wait_fixed

from config import settings
from utils.gcs import get_storage_client, upload_file
from utils.logging import configure_logging

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def blob_path_for(city_name: str, target_date: str, batch_id: str) -> str:
    """Build the Hive-style partitioned GCS destination path for a payload."""
    year, month, day = target_date[:4], target_date[5:7], target_date[8:10]
    return (
        f"raw/weather/"
        f"tenant={city_name}/"
        f"year={year}/"
        f"month={month}/"
        f"day={day}/"
        f"batch_{batch_id}.json"
    )


@retry(stop=stop_after_attempt(3), wait=wait_fixed(5), reraise=True)
def fetch_weather(url: str, params: dict) -> dict:
    """Fetch weather data from Open-Meteo. Retries up to 3 times on failure."""
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def weather_for_date(lat, lon, city_name, batch_id, target_date=None):
    """Fetch, save, and upload weather data for a single date."""
    if target_date is None:
        target_date = date.today().isoformat()

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": target_date,
        "end_date": target_date,
        "hourly": "temperature_2m",
        "timezone": "auto",
    }

    try:
        data = fetch_weather(url=OPEN_METEO_URL, params=params)

        metadata = {
            "ingestion_time": datetime.now(timezone.utc).isoformat(),
            "batch_id": batch_id,
            "source": "open-meteo",
            "city": city_name,
        }
        final_payload = {"metadata": metadata, "weather_data": data}

        os.makedirs("/tmp/weather", exist_ok=True)
        file_name = f"/tmp/weather/weather_{city_name}_{target_date}.json"
        with open(file_name, "w") as f:
            json.dump(final_payload, f, indent=4)

        destination_blob = blob_path_for(city_name, target_date, batch_id)
        client = get_storage_client(settings.PROJECT_ID)
        upload_file(client, settings.GCS_BUCKET, file_name, destination_blob)

        logger.info("Saved weather for %s (%s)", city_name, target_date)

    except requests.exceptions.HTTPError as e:
        logger.error("HTTP error for %s: %s", city_name, e)
    except requests.exceptions.RequestException as e:
        logger.error("Network error for %s: %s", city_name, e)
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON returned for %s: %s", city_name, e)
    except Exception as e:
        logger.error("Unexpected error for %s: %s", city_name, e)


def weather_for_range(lat, lon, city_name, batch_id, start_date, end_date):
    """Fetch weather data for every day in a date range (inclusive)."""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    current = start
    while current <= end:
        weather_for_date(
            lat=lat,
            lon=lon,
            city_name=city_name,
            batch_id=batch_id,
            target_date=current.strftime("%Y-%m-%d"),
        )
        current += timedelta(days=1)


def get_city_coordinates(city_name: str) -> tuple[float, float]:
    """Return (lat, lon) for a supported city."""
    if city_name not in settings.CITY_COORDINATES:
        raise ValueError(f"City '{city_name}' is not supported.")
    return settings.CITY_COORDINATES[city_name]


def main():
    configure_logging()

    parser = argparse.ArgumentParser(description="Download weather data from Open-Meteo")
    parser.add_argument("--city", help="City name")
    parser.add_argument("--date", help="Single date (YYYY-MM-DD)")
    parser.add_argument("--date_from", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--date_to", help="End date (YYYY-MM-DD)")
    args = parser.parse_args()

    batch_id = str(uuid.uuid4())
    cities_to_process = [args.city] if args.city else list(settings.CITY_COORDINATES.keys())

    logger.info("Starting ingestion batch %s", batch_id)

    for city_name in cities_to_process:
        lat, lon = get_city_coordinates(city_name)

        if args.date:
            weather_for_date(lat=lat, lon=lon, city_name=city_name, batch_id=batch_id, target_date=args.date)
        elif args.date_from and args.date_to:
            weather_for_range(
                lat=lat, lon=lon, city_name=city_name, batch_id=batch_id,
                start_date=args.date_from, end_date=args.date_to,
            )
        else:
            weather_for_date(lat=lat, lon=lon, city_name=city_name, batch_id=batch_id)

    logger.info("Completed ingestion batch %s", batch_id)


if __name__ == "__main__":
    main()
