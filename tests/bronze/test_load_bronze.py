import json
from pathlib import Path

from etl.bronze.load_bronze import parse_bronze_rows

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "sample_weather_payload.json"


def _load_fixture() -> dict:
    with open(FIXTURE) as f:
        return json.load(f)


def test_parse_bronze_rows_shape_and_count():
    payload = _load_fixture()
    rows = parse_bronze_rows(payload)

    assert len(rows) == 3
    assert {row["city"] for row in rows} == {"Yerevan"}
    assert {row["batch_id"] for row in rows} == {"test-batch-0001"}
    assert {row["source"] for row in rows} == {"open-meteo"}


def test_parse_bronze_rows_extracts_date_hour_temp_correctly():
    payload = _load_fixture()
    rows = parse_bronze_rows(payload)

    first = rows[0]
    assert first["observed_date"] == "2026-07-08"
    assert first["observed_hour"] == 0
    assert first["temperature_c"] == 18.4

    last = rows[-1]
    assert last["observed_hour"] == 2
    assert last["temperature_c"] == 17.5


def test_parse_bronze_rows_empty_hourly_returns_no_rows():
    payload = {
        "metadata": {
            "ingestion_time": "2026-07-08T06:00:00+00:00",
            "batch_id": "empty-batch",
            "source": "open-meteo",
            "city": "Paris",
        },
        "weather_data": {"hourly": {"time": [], "temperature_2m": []}},
    }
    assert parse_bronze_rows(payload) == []
