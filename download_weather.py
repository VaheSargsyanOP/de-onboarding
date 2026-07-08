import requests
import json
from datetime import date


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

    file_name = (
        f"weather_{city_name}_{target_date}.json"
    )

    with open(file_name, "w") as f:
        json.dump(data, f, indent=4)

    print(f"Saved to {file_name}")

    return data


if __name__ == "__main__":

    weather_for_date(
        lat=40,
        lon=44,
        city_name="Yerevan",
        target_date="2026-02-24"
    )