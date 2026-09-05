"""Unit tests for Data Quality & Validation module."""

import pyarrow as pa
import pyarrow.parquet as pq
from src.validation.validate_data import DataValidator


def test_validate_clean_data(temp_test_dir, sample_raw_parquet):
    """Test validation on clean dataset."""
    val_output = temp_test_dir / "clean_val.parquet"
    validator = DataValidator()

    success, metrics = validator.validate_file(sample_raw_parquet, val_output)

    assert success is True
    assert metrics["total_rows_initial"] == 50
    assert metrics["total_rows_clean"] == 50
    assert metrics["rejection_ratio"] == 0.0
    assert val_output.exists()


def test_validate_corrupt_records(temp_test_dir, sample_raw_df):
    """Test filtering of corrupt records (negative distance, negative fare, invalid zone)."""
    corrupt_df = sample_raw_df.copy()

    # Inject corrupt rows
    corrupt_df.loc[0, "trip_distance"] = -5.0  # Invalid distance
    corrupt_df.loc[1, "fare_amount"] = -20.0  # Invalid fare
    corrupt_df.loc[2, "PULocationID"] = 999  # Invalid zone

    raw_path = temp_test_dir / "corrupt_sample.parquet"
    val_path = temp_test_dir / "corrupt_val.parquet"

    pq.write_table(pa.Table.from_pandas(corrupt_df), raw_path)

    validator = DataValidator()
    success, metrics = validator.validate_file(raw_path, val_path)

    assert success is True
    assert metrics["total_rows_initial"] == 50
    assert metrics["total_rows_clean"] == 47
    assert metrics["failed_checks"]["negative_or_zero_distance"] >= 1
    assert metrics["failed_checks"]["negative_fares"] >= 1
    assert metrics["failed_checks"]["invalid_location_ids"] >= 1
