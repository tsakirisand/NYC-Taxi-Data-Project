"""Unit tests for Data Ingestion module."""

from unittest.mock import MagicMock, patch
from src.ingestion.download_taxi_data import TaxiDataDownloader
from src.utils.storage import StorageManager


def test_download_month_existing_file(temp_test_dir):
    """Test that existing files are skipped when force=False."""
    raw_dir = temp_test_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    existing_file = raw_dir / "yellow_tripdata_2025-01.parquet"
    existing_file.write_bytes(b"dummy_parquet_data")

    storage = StorageManager(storage_type="local")
    downloader = TaxiDataDownloader(storage=storage)

    with patch.object(storage, "get_path", return_value=str(existing_file)):
        res = downloader.download_month(2025, 1, force=False)
        assert res == existing_file


@patch("requests.get")
def test_download_month_http_success(mock_get, temp_test_dir):
    """Test successful HTTP stream download."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.iter_content.return_value = [b"chunk1", b"chunk2"]
    mock_get.return_value = mock_response

    target_file = temp_test_dir / "yellow_tripdata_2025-02.parquet"
    storage = StorageManager(storage_type="local")
    downloader = TaxiDataDownloader(storage=storage)

    with patch.object(storage, "get_path", return_value=str(target_file)):
        res = downloader.download_month(2025, 2, force=True)
        assert res == target_file
        assert target_file.exists()
        assert target_file.read_bytes() == b"chunk1chunk2"


@patch("requests.get")
def test_download_month_404_not_found(mock_get, temp_test_dir):
    """Test handling of 404 response."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    storage = StorageManager(storage_type="local")
    downloader = TaxiDataDownloader(storage=storage)

    res = downloader.download_month(2025, 12, force=True)
    assert res is None
