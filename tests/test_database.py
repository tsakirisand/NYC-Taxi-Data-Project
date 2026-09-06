"""Unit tests for Relational Database loading and SQL execution."""

from sqlalchemy import text
from src.database.load_postgres import DatabaseLoader


def test_database_schema_initialization(sqlite_test_engine):
    """Test SQL schema creation on test database."""
    loader = DatabaseLoader()
    loader._engine = sqlite_test_engine

    loader.initialize_schema()

    with sqlite_test_engine.connect() as conn:
        # Check tables created
        result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table';")
        )
        tables = [row[0] for row in result.fetchall()]

    assert "fact_trips" in tables
    assert "dim_taxi_zone" in tables
    assert "dim_date" in tables


def test_load_dim_date(sqlite_test_engine):
    """Test populating date dimension table."""
    loader = DatabaseLoader()
    loader._engine = sqlite_test_engine

    loader.initialize_schema()
    loader.load_dim_date(start_date="2025-01-01", end_date="2025-01-05")

    with sqlite_test_engine.connect() as conn:
        res = conn.execute(text("SELECT COUNT(*) FROM dim_date"))
        count = res.scalar()

    assert count == 5


def test_multi_month_database_query(sqlite_test_engine, sample_raw_df):
    """Test executing multi-month aggregation query against fact_trips."""
    import pandas as pd

    loader = DatabaseLoader()
    loader._engine = sqlite_test_engine
    loader.initialize_schema()

    df1 = sample_raw_df.copy()
    df1["tpep_pickup_datetime"] = pd.to_datetime("2025-01-15 10:00:00")
    df1["tpep_dropoff_datetime"] = pd.to_datetime("2025-01-15 10:15:00")

    df2 = sample_raw_df.copy()
    df2["tpep_pickup_datetime"] = pd.to_datetime("2025-02-15 10:00:00")
    df2["tpep_dropoff_datetime"] = pd.to_datetime("2025-02-15 10:15:00")

    multi_df = pd.concat([df1, df2], ignore_index=True)
    multi_df["pickup_year"] = pd.to_datetime(multi_df["tpep_pickup_datetime"]).dt.year
    multi_df["pickup_month"] = pd.to_datetime(multi_df["tpep_pickup_datetime"]).dt.month
    multi_df["pickup_hour"] = pd.to_datetime(multi_df["tpep_pickup_datetime"]).dt.hour
    multi_df["pickup_day_of_week"] = "Wed"
    multi_df["trip_duration_minutes"] = 15.0
    multi_df["avg_speed_mph"] = 12.0
    multi_df["tip_percentage"] = 15.0
    multi_df["is_peak_hour"] = False

    rename_map = {
        "PULocationID": "pulocation_id",
        "DOLocationID": "dolocation_id",
        "RatecodeID": "rate_code_id",
        "VendorID": "vendor_id",
    }
    multi_df.rename(columns=rename_map, inplace=True)
    multi_df.columns = [c.lower() for c in multi_df.columns]

    multi_df.to_sql(
        "fact_trips", con=sqlite_test_engine, if_exists="replace", index=False
    )

    with sqlite_test_engine.connect() as conn:
        res = conn.execute(
            text(
                "SELECT pickup_year, pickup_month, COUNT(*) AS trips "
                "FROM fact_trips GROUP BY 1, 2 ORDER BY 1, 2"
            )
        )
        rows = res.fetchall()

    assert len(rows) == 2
    assert rows[0][1] == 1  # Month 1
    assert rows[1][1] == 2  # Month 2
