"""Pytest configuration and shared test fixtures."""

import tempfile
from pathlib import Path
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from sqlalchemy import create_engine


@pytest.fixture(scope="session")
def temp_test_dir():
    """Create a temporary directory for test output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_raw_df():
    """Generate a clean synthetic sample DataFrame matching TLC yellow taxi schema."""
    dates = pd.date_range("2025-01-01 08:00:00", periods=50, freq="15min")
    df = pd.DataFrame(
        {
            "VendorID": [1] * 50,
            "tpep_pickup_datetime": dates,
            "tpep_dropoff_datetime": dates + pd.Timedelta(minutes=15),
            "passenger_count": [2] * 50,
            "trip_distance": [3.5] * 50,
            "RatecodeID": [1] * 50,
            "store_and_fwd_flag": ["N"] * 50,
            "PULocationID": [100] * 50,
            "DOLocationID": [140] * 50,
            "payment_type": [1] * 50,
            "fare_amount": [15.0] * 50,
            "extra": [1.0] * 50,
            "mta_tax": [0.5] * 50,
            "tip_amount": [3.0] * 50,
            "tolls_amount": [0.0] * 50,
            "improvement_surcharge": [0.3] * 50,
            "total_amount": [19.8] * 50,
            "congestion_surcharge": [2.5] * 50,
            "airport_fee": [0.0] * 50,
        }
    )
    return df


@pytest.fixture
def sample_raw_parquet(temp_test_dir, sample_raw_df):
    """Write sample DataFrame to a temporary raw Parquet file."""
    file_path = temp_test_dir / "yellow_tripdata_2025-01.parquet"
    table = pa.Table.from_pandas(sample_raw_df)
    pq.write_table(table, file_path)
    return file_path


@pytest.fixture
def sqlite_test_engine(temp_test_dir):
    """In-memory SQLite engine for testing database loader."""
    db_path = temp_test_dir / "test_nyc.db"
    engine = create_engine(f"sqlite:///{db_path}")
    return engine
