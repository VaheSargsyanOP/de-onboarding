import requests
import json
from datetime import date


def todays_weather(lat, lon, city_name):
    url = "https://api.open-meteo.com/v1/forecast"

    today = date.today().isoformat()

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": today,
        "end_date": today,
        "hourly": "temperature_2m",
        "timezone": "auto",
    }

    response = requests.get(url, params=params)

    response.raise_for_status()

    data = response.json()

    file_name = f"data/today_weather_{city_name}_{today}.json"

    with open(file_name, "w") as f:
        json.dump(data, f, indent=4)

    print(f"Saved to {file_name}")

    return data


if __name__ == "__main__":
    todays_weather(
        lat=40.1772,
        lon=44.5035,
        city_name="Yerevan"
    )