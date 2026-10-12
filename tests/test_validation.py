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


def test_validate_invalid_timestamps_and_duration(temp_test_dir, sample_raw_df):
    """Test rejection of dropoff before pickup, excess duration, and invalid year."""
    import pandas as pd

    corrupt_df = sample_raw_df.copy()
    # 1. Dropoff before pickup
    corrupt_df.loc[0, "tpep_dropoff_datetime"] = corrupt_df.loc[
        0, "tpep_pickup_datetime"
    ] - pd.Timedelta(minutes=5)
    # 2. Duration > 24 hours
    corrupt_df.loc[1, "tpep_dropoff_datetime"] = corrupt_df.loc[
        1, "tpep_pickup_datetime"
    ] + pd.Timedelta(hours=25)
    # 3. Out of bounds year (e.g. 2024 trip in 2025 file)
    corrupt_df.loc[2, "tpep_pickup_datetime"] = pd.to_datetime("2024-12-31 23:59:00")
    corrupt_df.loc[2, "tpep_dropoff_datetime"] = pd.to_datetime("2025-01-01 00:15:00")

    raw_path = temp_test_dir / "invalid_ts_sample.parquet"
    val_path = temp_test_dir / "invalid_ts_val.parquet"
    pq.write_table(pa.Table.from_pandas(corrupt_df), raw_path)

    validator = DataValidator()
    success, metrics = validator.validate_file(raw_path, val_path)

    assert success is True
    assert metrics["total_rows_clean"] == 47
    assert metrics["failed_checks"]["invalid_timestamps"] == 3


def test_validate_null_timestamps(temp_test_dir, sample_raw_df):
    """Test rejection of records with null pickup or dropoff timestamps."""
    corrupt_df = sample_raw_df.copy()
    corrupt_df.loc[0, "tpep_pickup_datetime"] = None
    corrupt_df.loc[1, "tpep_dropoff_datetime"] = None

    raw_path = temp_test_dir / "null_ts_sample.parquet"
    val_path = temp_test_dir / "null_ts_val.parquet"
    pq.write_table(pa.Table.from_pandas(corrupt_df), raw_path)

    validator = DataValidator()
    success, metrics = validator.validate_file(raw_path, val_path)

    assert success is True
    assert metrics["total_rows_clean"] == 48
    assert metrics["failed_checks"]["null_timestamps"] == 2


def test_validate_exact_duplicates(temp_test_dir, sample_raw_df):
    """Test deduplication drops exact duplicate trips."""
    import pandas as pd

    dup_df = pd.concat([sample_raw_df, sample_raw_df.iloc[[0], :]], ignore_index=True)
    raw_path = temp_test_dir / "dup_sample.parquet"
    val_path = temp_test_dir / "dup_val.parquet"
    pq.write_table(pa.Table.from_pandas(dup_df), raw_path)

    validator = DataValidator()
    success, metrics = validator.validate_file(raw_path, val_path)

    assert success is True
    assert metrics["total_rows_initial"] == 51
    assert metrics["total_rows_clean"] == 50
    assert metrics["failed_checks"]["duplicates"] == 1


def test_validate_max_invalid_ratio_threshold(temp_test_dir, sample_raw_df):
    """Test validation failure when corruption ratio exceeds threshold (50%)."""
    corrupt_df = sample_raw_df.copy()
    # Corrupt 30 out of 50 rows (60% rejection ratio)
    corrupt_df.loc[:29, "trip_distance"] = -1.0

    raw_path = temp_test_dir / "severe_corrupt.parquet"
    val_path = temp_test_dir / "severe_val.parquet"
    pq.write_table(pa.Table.from_pandas(corrupt_df), raw_path)

    validator = DataValidator(max_invalid_ratio=0.5)
    success, metrics = validator.validate_file(raw_path, val_path)

    assert success is False
    assert metrics["rejection_ratio"] >= 0.5
    assert not val_path.exists()
