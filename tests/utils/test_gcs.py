from unittest.mock import MagicMock

from utils.gcs import iter_json_blobs


def _make_blob(name: str, content: str):
    blob = MagicMock()
    blob.name = name
    blob.download_as_text.return_value = content
    return blob


def test_iter_json_blobs_skips_non_json_and_parses_json():
    blobs = [
        _make_blob("raw/weather/tenant=Yerevan/readme.txt", "not json"),
        _make_blob("raw/weather/tenant=Yerevan/batch_1.json", '{"city": "Yerevan"}'),
        _make_blob("raw/weather/tenant=Paris/batch_2.json", '{"city": "Paris"}'),
    ]

    client = MagicMock()
    client.bucket.return_value.list_blobs.return_value = blobs

    results = list(iter_json_blobs(client, "some-bucket", "raw/weather/"))

    assert results == [{"city": "Yerevan"}, {"city": "Paris"}]
    client.bucket.assert_called_once_with("some-bucket")
    client.bucket.return_value.list_blobs.assert_called_once_with(prefix="raw/weather/")
