import requests
import json
import argparse
import uuid
import logging

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


CITY_COORDINATES = {
    "Yerevan": (40.1772, 44.5035),
    "Paris": (48.8566, 2.3522),
    "London": (51.5074, -0.1278)
}


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

        file_name = (
            f"data/weather_{city_name}_{target_date}.json"
        )

        with open(file_name, "w") as f:
            json.dump(
                final_payload,
                f,
                indent=4
            )

        logging.info(
            f"Saved to {file_name}"
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