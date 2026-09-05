"""Unit tests for PySpark Data Transformations module."""

import pytest

pyspark = pytest.importorskip("pyspark")
from src.transformation.transform_taxi_data import (  # noqa: E402
    TaxiDataTransformer,
    get_spark_session,
)


@pytest.fixture(scope="module")
def spark_session():
    """Create PySpark local session for tests."""
    spark = get_spark_session("UnitTestPySpark")
    yield spark


def test_pyspark_transformations(spark_session, sample_raw_df):
    """Test feature calculation functions (duration, speed, tip %, dates)."""
    spark_df = spark_session.createDataFrame(sample_raw_df)
    transformer = TaxiDataTransformer(spark=spark_session)

    transformed_df = transformer.transform_trips(spark_df)
    cols = transformed_df.columns

    assert "trip_duration_minutes" in cols
    assert "avg_speed_mph" in cols
    assert "tip_percentage" in cols
    assert "pickup_hour" in cols
    assert "is_peak_hour" in cols

    row = transformed_df.first()
    # 15 mins duration check
    assert row["trip_duration_minutes"] == 15.0
    # Speed check: 3.5 miles in 15 mins = 14 mph
    assert row["avg_speed_mph"] == 14.0
    # Tip % check: 3.0 tip on 15.0 fare = 20%
    assert row["tip_percentage"] == 20.0


def test_pyspark_aggregations(spark_session, sample_raw_df):
    """Test aggregated summary DataFrames computation."""
    spark_df = spark_session.createDataFrame(sample_raw_df)
    transformer = TaxiDataTransformer(spark=spark_session)

    transformed_df = transformer.transform_trips(spark_df)
    aggs = transformer.compute_aggregations(transformed_df)

    assert "hourly" in aggs
    assert "daily" in aggs
    assert "monthly" in aggs
    assert "zone" in aggs

    hourly_df = aggs["hourly"]
    assert hourly_df.count() > 0
