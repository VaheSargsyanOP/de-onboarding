import requests_mock

from etl.extract.download_weather import blob_path_for, fetch_weather


def test_blob_path_for_builds_hive_style_partition_path():
    path = blob_path_for("Yerevan", "2026-07-08", "abc-123")
    assert path == (
        "raw/weather/tenant=Yerevan/year=2026/month=07/day=08/batch_abc-123.json"
    )


def test_fetch_weather_returns_parsed_json():
    url = "https://api.open-meteo.com/v1/forecast"
    payload = {"hourly": {"time": ["2026-07-08T00:00"], "temperature_2m": [18.4]}}

    with requests_mock.Mocker() as m:
        m.get(url, json=payload)
        result = fetch_weather(url, params={"latitude": 40.17, "longitude": 44.5})

    assert result == payload


def test_fetch_weather_retries_on_server_error_then_succeeds(monkeypatch):
    # fetch_weather is wrapped with tenacity's wait_fixed(5) - patch out
    # the real sleep so this test exercises the retry loop without
    # actually waiting 10 real seconds.
    monkeypatch.setattr("time.sleep", lambda seconds: None)

    url = "https://api.open-meteo.com/v1/forecast"
    payload = {"hourly": {"time": [], "temperature_2m": []}}

    with requests_mock.Mocker() as m:
        m.get(
            url,
            [
                {"status_code": 500},
                {"status_code": 500},
                {"json": payload, "status_code": 200},
            ],
        )
        result = fetch_weather(url, params={})

    assert result == payload
    assert m.call_count == 3
