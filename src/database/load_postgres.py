"""Database Loader Module.

Batch loads transformed Parquet datasets into PostgreSQL or SQLite.
"""

import argparse
import hashlib
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from src.utils.config import settings
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class DatabaseLoader:
    """Loader class to manage relational database operations."""

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or settings.db_url
        self._engine: Optional[Engine] = None

    @property
    def engine(self) -> Engine:
        """Lazy engine instantiation with fallback to SQLite if PostgreSQL fails."""
        if self._engine is None:
            try:
                self._engine = create_engine(self.db_url, echo=False)
                # Test connection
                with self._engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                logger.info(f"Connected to database at {self.db_url}")
            except Exception as e:
                logger.warning(f"Could not connect to database at {self.db_url}: {e}")
                if "postgresql" in self.db_url:
                    fallback_url = settings.sqlite_sqlalchemy_url
                    logger.info(
                        f"Falling back to local SQLite database: {fallback_url}"
                    )
                    self.db_url = fallback_url
                    self._engine = create_engine(fallback_url, echo=False)
                else:
                    raise e
        return self._engine

    def execute_sql_file(self, sql_file_path: Path) -> None:
        """Read and execute SQL statements from a file."""
        if not sql_file_path.exists():
            logger.error(f"SQL file not found: {sql_file_path}")
            return

        logger.info(f"Executing SQL script: {sql_file_path}...")
        with open(sql_file_path, "r") as f:
            sql_content = f.read()

        statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]
        with self.engine.connect() as conn:
            for stmt in statements:
                try:
                    conn.execute(text(stmt))
                except Exception as e:
                    logger.warning(f"Statement warning/error during execution: {e}")
            conn.commit()
        logger.info(f"Executed {len(statements)} SQL statements.")

    def initialize_schema(self) -> None:
        """Create tables and indexes from DDL files."""
        schema_file = settings.BASE_DIR / "sql" / "schema.sql"
        indexes_file = settings.BASE_DIR / "sql" / "indexes.sql"
        self.execute_sql_file(schema_file)
        self.execute_sql_file(indexes_file)

    def load_dim_taxi_zone(
        self, csv_path: Path = settings.REFERENCE_DATA_DIR / "taxi_zone_lookup.csv"
    ) -> None:
        """Populate dim_taxi_zone table from CSV lookup file."""
        if not csv_path.exists():
            logger.warning(f"Taxi zone lookup file not found at {csv_path}. Skipping.")
            return

        logger.info(f"Loading dim_taxi_zone from {csv_path}...")
        df = pd.read_csv(csv_path)

        df.rename(
            columns={
                "LocationID": "location_id",
                "Borough": "borough",
                "Zone": "zone",
                "service_zone": "service_zone",
            },
            inplace=True,
        )

        df.to_sql(
            "dim_taxi_zone",
            con=self.engine,
            if_exists="replace",
            index=False,
            chunksize=500,
        )
        logger.info(f"Successfully loaded {len(df)} records into dim_taxi_zone.")

    def load_dim_date(
        self, start_date: str = "2025-01-01", end_date: str = "2025-12-31"
    ) -> None:
        """Populate dim_date dimension table."""
        logger.info(f"Generating dim_date dimension from {start_date} to {end_date}...")
        date_range = pd.date_range(start=start_date, end=end_date, freq="D")

        dim_date_df = pd.DataFrame(
            {
                "date_key": date_range.date,
                "year": date_range.year,
                "month": date_range.month,
                "month_name": date_range.strftime("%B"),
                "day": date_range.day,
                "day_of_week": date_range.dayofweek + 1,
                "day_name": date_range.strftime("%A"),
                "is_weekend": date_range.dayofweek >= 5,
                "quarter": date_range.quarter,
            }
        )

        dim_date_df.to_sql(
            "dim_date",
            con=self.engine,
            if_exists="replace",
            index=False,
        )
        logger.info(f"Loaded {len(dim_date_df)} date records into dim_date.")

    def load_fact_trips(
        self, parquet_path: Path = settings.PROCESSED_DATA_DIR / "fact_trips.parquet"
    ) -> None:
        """Load transformed fact_trips dataset into database."""
        if parquet_path.exists():
            logger.info(f"Loading fact_trips from processed path: {parquet_path}...")
            df = pd.read_parquet(parquet_path)
        else:
            val_files = sorted(settings.VALIDATED_DATA_DIR.glob("*.parquet"))
            if not val_files:
                logger.error("No processed or validated parquet files found!")
                return
            logger.info(f"Loading fact_trips from {len(val_files)} validated parquet file(s)...")
            df = pd.concat([pd.read_parquet(f) for f in val_files], ignore_index=True)

            # Compute features if loading directly from validated parquet
            if "trip_duration_minutes" not in df.columns:
                p_col, d_col = "tpep_pickup_datetime", "tpep_dropoff_datetime"
                df[p_col] = pd.to_datetime(df[p_col])
                df[d_col] = pd.to_datetime(df[d_col])
                df["trip_duration_minutes"] = (
                    (df[d_col] - df[p_col]).dt.total_seconds() / 60.0
                ).round(2)
                df["avg_speed_mph"] = (
                    (df["trip_distance"] / (df["trip_duration_minutes"] / 60.0))
                    .replace([float("inf"), -float("inf")], 0.0)
                    .fillna(0.0)
                    .round(2)
                )
                df["tip_percentage"] = (
                    (df["tip_amount"] / df["fare_amount"].replace(0, pd.NA) * 100.0)
                    .fillna(0.0)
                    .round(2)
                )
                df["pickup_date"] = df[p_col].dt.date
                df["pickup_year"] = df[p_col].dt.year
                df["pickup_month"] = df[p_col].dt.month
                df["pickup_hour"] = df[p_col].dt.hour
                df["pickup_day_of_week"] = df[p_col].dt.strftime("%a")
                dow_num = df[p_col].dt.dayofweek + 2  # 1=Sun, 7=Sat format
                df["is_peak_hour"] = (dow_num.between(2, 6)) & (
                    df["pickup_hour"].between(7, 9) | df["pickup_hour"].between(16, 19)
                )

        # Generate deterministic synthetic trip_id if not present
        if "trip_id" not in df.columns:
            logger.info("Generating synthetic trip_id hashes for facts table...")
            df["trip_id"] = [
                hashlib.md5(f"{p_dt}_{pu}_{do}_{idx}".encode()).hexdigest()
                for idx, (p_dt, pu, do) in enumerate(
                    zip(
                        df["tpep_pickup_datetime"],
                        df["PULocationID"],
                        df["DOLocationID"],
                    )
                )
            ]

        # Rename columns to match DB schema
        column_mapping = {
            "PULocationID": "pulocation_id",
            "DOLocationID": "dolocation_id",
            "RatecodeID": "rate_code_id",
            "VendorID": "vendor_id",
        }
        df.rename(columns=column_mapping, inplace=True)

        # Lowercase all remaining columns
        df.columns = [c.lower() for c in df.columns]

        logger.info(f"Inserting {len(df):,} rows into fact_trips...")
        df.to_sql(
            "fact_trips",
            con=self.engine,
            if_exists="replace",
            index=False,
            chunksize=5000,
        )
        logger.info("Successfully loaded fact_trips.")

    def load_aggregate_tables(
        self, processed_dir: Path = settings.PROCESSED_DATA_DIR
    ) -> None:
        """Load aggregated summary tables into DB."""
        agg_files = {
            "agg_hourly.parquet": "agg_hourly_trips",
            "agg_daily.parquet": "agg_daily_trips",
            "agg_monthly.parquet": "agg_monthly_summary",
            "agg_zone.parquet": "agg_zone_metrics",
        }

        for file_name, table_name in agg_files.items():
            file_path = processed_dir / file_name
            if file_path.exists():
                logger.info(
                    f"Loading aggregate table '{table_name}' from {file_path}..."
                )
                df = pd.read_parquet(file_path)
                df.columns = [c.lower() for c in df.columns]
                if "pulocationid" in df.columns:
                    df.rename(columns={"pulocationid": "location_id"}, inplace=True)
                df.to_sql(
                    table_name,
                    con=self.engine,
                    if_exists="replace",
                    index=False,
                )
                logger.info(f"Successfully loaded {len(df)} rows into {table_name}.")

    def run_analytics_queries(self) -> None:
        """Run all analytical queries from sql/analytics.sql and print results."""
        analytics_file = settings.BASE_DIR / "sql" / "analytics.sql"
        if not analytics_file.exists():
            logger.error(f"Analytics file missing: {analytics_file}")
            return

        with open(analytics_file, "r") as f:
            content = f.read()

        queries = [q.strip() for q in content.split(";") if q.strip()]
        logger.info(f"Running {len(queries)} analytical queries against database...")

        with self.engine.connect() as conn:
            for idx, q in enumerate(queries, 1):
                try:
                    result = conn.execute(text(q))
                    if result.returns_rows:
                        rows = result.fetchall()
                        logger.info(
                            f"--- Query {idx} Result Sample ({len(rows)} rows) ---"
                        )
                        for r in rows[:3]:
                            logger.info(f"  {r}")
                except Exception as e:
                    logger.warning(f"Query {idx} execution failed: {e}")

    def run_full_pipeline(self) -> None:
        """Execute full database loading pipeline."""
        self.initialize_schema()
        self.load_dim_taxi_zone()
        self.load_dim_date()
        self.load_fact_trips()
        self.load_aggregate_tables()
        logger.info("Database loading pipeline completed successfully.")


def main():
    parser = argparse.ArgumentParser(description="PostgreSQL / SQLite Database Loader")
    parser.add_argument(
        "--run-analytics",
        action="store_true",
        help="Run analytical queries after loading database",
    )
    args = parser.parse_args()

    loader = DatabaseLoader()
    loader.run_full_pipeline()

    if args.run_analytics:
        loader.run_analytics_queries()


if __name__ == "__main__":
    main()
