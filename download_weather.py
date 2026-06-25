import requests
import json

from datetime import date
from datetime import datetime
from datetime import timedelta


def weather_for_date(lat, lon, city_name, target_date=None):


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

    file_name = f"data/weather_{city_name}_{target_date}.json"

    with open(file_name, "w") as f:
        json.dump(data, f, indent=4)

    print(f"Saved to {file_name}")

    return data


def weather_for_range(
    lat,
    lon,
    city_name,
    start_date,
    end_date
):
    """
    Fetch weather data for every day
    between start_date and end_date (inclusive).
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


if __name__ == "__main__":

    weather_for_range(
        lat=40.1772,
        lon=44.5035,
        city_name="Yerevan",
        start_date="2025-06-20",
        end_date="2025-06-24"
    )