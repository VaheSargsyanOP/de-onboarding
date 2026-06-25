import requests
import json
import argparse
import uuid


from datetime import date
from datetime import datetime
from datetime import timedelta
from datetime import timezone


CITY_COORDINATES = {
    "Yerevan": (40.1772, 44.5035),
    "Paris": (48.8566, 2.3522),
    "London": (51.5074, -0.1278)
}


def weather_for_date(lat, lon, city_name, target_date=None):
    """
    Fetch weather data for a single date.
    If target_date is not provided, use today.
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

    response = requests.get(url, params=params)

    response.raise_for_status()

    data = response.json()

    metadata = {
        "ingestion_time": datetime.now(timezone.utc).isoformat(),
        "batch_id": str(uuid.uuid4()),
        "source": "open-meteo",
        "city": city_name
    }

    final_payload = {
        "metadata": metadata,
        "weather_data": data
    }

    file_name = f"data/weather_{city_name}_{target_date}.json"

    with open(file_name, "w") as f:
        json.dump(final_payload, f, indent=4)

    print(f"Saved to {file_name}")

def weather_for_range(
    lat,
    lon,
    city_name,
    start_date,
    end_date
):
    """
    Fetch weather for every day in the range.
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
            target_date=target_date
        )

        current += timedelta(days=1)


def get_city_coordinates(city_name):
    """
    Return coordinates for supported cities.
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
        required=True,
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

    city_name = args.city

    lat, lon = get_city_coordinates(city_name)

    # Case 1: Single date
    if args.date:

        weather_for_date(
            lat=lat,
            lon=lon,
            city_name=city_name,
            target_date=args.date
        )

    # Case 2: Date range
    elif args.date_from and args.date_to:

        weather_for_range(
            lat=lat,
            lon=lon,
            city_name=city_name,
            start_date=args.date_from,
            end_date=args.date_to
        )

    # Case 3: Today (default)
    else:

        weather_for_date(
            lat=lat,
            lon=lon,
            city_name=city_name
        )


if __name__ == "__main__":
    main()