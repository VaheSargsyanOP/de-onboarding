import requests
import json
import argparse
import uuid
import logging
import os

from google.cloud import storage

from datetime import date
from datetime import datetime
from datetime import timedelta
from datetime import timezone

from tenacity import retry
from tenacity import stop_after_attempt
from tenacity import wait_fixed

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "project-347a7b51-e6cd-40d3-9ac")
BUCKET_NAME = os.getenv("GCS_BUCKET", "us-central1-weather-project-7b4142b8-bucket")

CITY_COORDINATES = {
    "Yerevan": (40.1772, 44.5035),
    "Paris": (48.8566, 2.3522),
    "London": (51.5074, -0.1278)
}


def upload_to_gcs(
    bucket_name,
    source_file,
    destination_blob
):
    """
    Upload a local file to Google Cloud Storage.
    """

    client = storage.Client(project=PROJECT_ID)

    bucket = client.bucket(bucket_name)

    blob = bucket.blob(destination_blob)

    blob.upload_from_filename(source_file)

    logging.info(
        f"Uploaded to gs://{bucket_name}/{destination_blob}"
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(5),
    reraise=True
)
def fetch_weather(url, params):
    """
    Fetch weather data from Open-Meteo.
    Retry up to 3 times if request fails.
    """

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def weather_for_date(
    lat,
    lon,
    city_name,
    batch_id,
    target_date=None
):
    """
    Fetch weather data for a single date.
    """

    if target_date is None:
        target_date = date.today().isoformat()

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": target_date,
        "end_date": target_date,
        "hourly": "temperature_2m",
        "timezone": "auto"
    }

    try:

        data = fetch_weather(
            url=url,
            params=params
        )

        metadata = {
            "ingestion_time": datetime.now(
                timezone.utc
            ).isoformat(),
            "batch_id": batch_id,
            "source": "open-meteo",
            "city": city_name
        }

        final_payload = {
            "metadata": metadata,
            "weather_data": data
        }

        os.makedirs(
            "/tmp/weather",
            exist_ok=True
        )

        file_name = (
            f"/tmp/weather/weather_{city_name}_{target_date}.json"
        )

        with open(file_name, "w") as f:
            json.dump(
                final_payload,
                f,
                indent=4
            )

        year = target_date[:4]
        month = target_date[5:7]
        day = target_date[8:10]

        destination_blob = (
            f"raw/weather/"
            f"tenant={city_name}/"
            f"year={year}/"
            f"month={month}/"
            f"day={day}/"
            f"batch_{batch_id}.json"
        )

        upload_to_gcs(
            bucket_name=BUCKET_NAME,
            source_file=file_name,
            destination_blob=destination_blob
        )

        logging.info(
            f"Saved weather for {city_name} ({target_date})"
        )

    except requests.exceptions.HTTPError as e:

        logging.error(
            f"HTTP error for {city_name}: {e}"
        )

    except requests.exceptions.RequestException as e:

        logging.error(
            f"Network error for {city_name}: {e}"
        )

    except json.JSONDecodeError as e:

        logging.error(
            f"Invalid JSON returned for {city_name}: {e}"
        )

    except Exception as e:

        logging.error(
            f"Unexpected error for {city_name}: {e}"
        )


def weather_for_range(
    lat,
    lon,
    city_name,
    batch_id,
    start_date,
    end_date
):
    """
    Fetch weather data for every day
    in a date range (inclusive).
    """

    start = datetime.strptime(
        start_date,
        "%Y-%m-%d"
    )

    end = datetime.strptime(
        end_date,
        "%Y-%m-%d"
    )

    current = start

    while current <= end:

        target_date = current.strftime(
            "%Y-%m-%d"
        )

        weather_for_date(
            lat=lat,
            lon=lon,
            city_name=city_name,
            batch_id=batch_id,
            target_date=target_date
        )

        current += timedelta(days=1)


def get_city_coordinates(city_name):
    """
    Return coordinates
    for supported cities.
    """

    if city_name not in CITY_COORDINATES:

        raise ValueError(
            f"City '{city_name}' is not supported."
        )

    return CITY_COORDINATES[city_name]


def main():

    parser = argparse.ArgumentParser(
        description="Download weather data from Open-Meteo"
    )

    parser.add_argument(
        "--city",
        help="City name"
    )

    parser.add_argument(
        "--date",
        help="Single date (YYYY-MM-DD)"
    )

    parser.add_argument(
        "--date_from",
        help="Start date (YYYY-MM-DD)"
    )

    parser.add_argument(
        "--date_to",
        help="End date (YYYY-MM-DD)"
    )

    args = parser.parse_args()

    batch_id = str(uuid.uuid4())

    if args.city:
        cities_to_process = [args.city]
    else:
        cities_to_process = list(
            CITY_COORDINATES.keys()
        )

    logging.info(
        f"Starting ingestion batch {batch_id}"
    )

    for city_name in cities_to_process:

        lat, lon = get_city_coordinates(
            city_name
        )

        if args.date:

            weather_for_date(
                lat=lat,
                lon=lon,
                city_name=city_name,
                batch_id=batch_id,
                target_date=args.date
            )

        elif args.date_from and args.date_to:

            weather_for_range(
                lat=lat,
                lon=lon,
                city_name=city_name,
                batch_id=batch_id,
                start_date=args.date_from,
                end_date=args.date_to
            )

        else:

            weather_for_date(
                lat=lat,
                lon=lon,
                city_name=city_name,
                batch_id=batch_id
            )

    logging.info(
    f"Completed ingestion batch {batch_id}"
    )


if __name__ == "__main__":
    main()