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
