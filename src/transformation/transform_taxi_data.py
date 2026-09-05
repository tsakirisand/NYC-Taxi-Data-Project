"""PySpark Transformation Module.

Distributed Spark transformations for NYC Yellow Taxi trip records.
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Optional

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F

from src.utils.config import settings
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def get_spark_session(app_name: str = "NYCTaxiTransformation") -> SparkSession:
    """Initialize and return a PySpark Session."""
    return (
        SparkSession.builder.appName(app_name)
        .config("spark.driver.memory", "2g")
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )


class TaxiDataTransformer:
    """PySpark Transformer for NYC Yellow Taxi Data."""

    def __init__(self, spark: Optional[SparkSession] = None):
        self.spark = spark or get_spark_session()

    def transform_trips(self, df: DataFrame) -> DataFrame:
        """Apply feature engineering transformations to trip records.

        Calculates:
        - trip_duration_minutes
        - avg_speed_mph
        - total_fare
        - tip_percentage
        - pickup_date, pickup_year, pickup_month, pickup_hour, pickup_day_of_week
        - is_peak_hour
        """
        logger.info("Applying PySpark feature transformations...")

        transformed = (
            df.withColumn(
                "trip_duration_minutes",
                F.round(
                    (
                        F.col("tpep_dropoff_datetime").cast("long")
                        - F.col("tpep_pickup_datetime").cast("long")
                    )
                    / 60.0,
                    2,
                ),
            )
            .withColumn(
                "avg_speed_mph",
                F.when(
                    F.col("trip_duration_minutes") > 0,
                    F.round(
                        F.col("trip_distance")
                        / (F.col("trip_duration_minutes") / 60.0),
                        2,
                    ),
                ).otherwise(0.0),
            )
            .withColumn("total_fare", F.col("total_amount"))
            .withColumn(
                "tip_percentage",
                F.when(
                    F.col("fare_amount") > 0,
                    F.round((F.col("tip_amount") / F.col("fare_amount")) * 100.0, 2),
                ).otherwise(0.0),
            )
            .withColumn("pickup_date", F.to_date(F.col("tpep_pickup_datetime")))
            .withColumn("pickup_year", F.year(F.col("tpep_pickup_datetime")))
            .withColumn("pickup_month", F.month(F.col("tpep_pickup_datetime")))
            .withColumn("pickup_hour", F.hour(F.col("tpep_pickup_datetime")))
            .withColumn(
                "pickup_day_of_week",
                F.date_format(F.col("tpep_pickup_datetime"), "E"),
            )
            .withColumn(
                "day_of_week_num",
                F.dayofweek(F.col("tpep_pickup_datetime")),  # 1=Sun, 7=Sat
            )
            .withColumn(
                "is_peak_hour",
                F.when(
                    (F.col("day_of_week_num").between(2, 6))
                    & (
                        (F.col("pickup_hour").between(7, 9))
                        | (F.col("pickup_hour").between(16, 19))
                    ),
                    True,
                ).otherwise(False),
            )
        )

        return transformed

    def compute_aggregations(self, df: DataFrame) -> Dict[str, DataFrame]:
        """Compute analytical aggregated DataFrames using Spark.

        Returns:
            Dict containing:
            - 'hourly': trips & revenue by hour
            - 'daily': trips & revenue by date
            - 'monthly': trips & revenue by month
            - 'zone': trips, avg fare & distance by pickup zone
        """
        logger.info("Computing PySpark distributed aggregations...")

        # 1. Hourly Aggregations
        hourly_agg = (
            df.groupBy("pickup_hour")
            .agg(
                F.count("*").alias("total_trips"),
                F.round(F.sum("total_amount"), 2).alias("total_revenue"),
                F.round(F.avg("fare_amount"), 2).alias("avg_fare"),
                F.round(F.avg("trip_distance"), 2).alias("avg_distance"),
                F.round(F.avg("trip_duration_minutes"), 2).alias("avg_duration"),
                F.round(F.avg("tip_percentage"), 2).alias("avg_tip_percentage"),
            )
            .orderBy("pickup_hour")
        )

        # 2. Daily Aggregations
        daily_agg = (
            df.groupBy("pickup_date", "pickup_day_of_week")
            .agg(
                F.count("*").alias("total_trips"),
                F.round(F.sum("total_amount"), 2).alias("total_revenue"),
                F.round(F.avg("fare_amount"), 2).alias("avg_fare"),
                F.round(F.avg("trip_distance"), 2).alias("avg_distance"),
            )
            .orderBy("pickup_date")
        )

        # 3. Monthly Aggregations
        monthly_agg = (
            df.groupBy("pickup_year", "pickup_month")
            .agg(
                F.count("*").alias("total_trips"),
                F.round(F.sum("total_amount"), 2).alias("total_revenue"),
                F.round(F.avg("fare_amount"), 2).alias("avg_fare"),
                F.round(F.avg("trip_distance"), 2).alias("avg_distance"),
                F.round(F.avg("trip_duration_minutes"), 2).alias("avg_duration"),
            )
            .orderBy("pickup_year", "pickup_month")
        )

        # 4. Zone Aggregations
        zone_agg = (
            df.groupBy("PULocationID")
            .agg(
                F.count("*").alias("total_pickups"),
                F.round(F.sum("total_amount"), 2).alias("total_revenue"),
                F.round(F.avg("fare_amount"), 2).alias("avg_fare"),
                F.round(F.avg("trip_distance"), 2).alias("avg_distance"),
                F.round(F.avg("trip_duration_minutes"), 2).alias("avg_duration"),
            )
            .orderBy(F.desc("total_pickups"))
        )

        return {
            "hourly": hourly_agg,
            "daily": daily_agg,
            "monthly": monthly_agg,
            "zone": zone_agg,
        }

    def process_validated_directory(
        self,
        validated_dir: Path = settings.VALIDATED_DATA_DIR,
        processed_dir: Path = settings.PROCESSED_DATA_DIR,
    ) -> bool:
        """Read all validated parquet files, apply transformations and save outputs."""
        parquet_files = sorted(validated_dir.glob("*.parquet"))
        if not parquet_files:
            logger.warning(f"No validated parquet files found in {validated_dir}")
            return False

        logger.info(
            f"Found {len(parquet_files)} validated Parquet files for PySpark transformation."
        )

        input_paths = [str(p) for p in parquet_files]
        raw_df = self.spark.read.parquet(*input_paths)

        transformed_df = self.transform_trips(raw_df)

        processed_dir.mkdir(parents=True, exist_ok=True)
        facts_output_path = str(processed_dir / "fact_trips.parquet")

        logger.info(f"Writing processed fact_trips dataset to {facts_output_path}...")
        transformed_df.write.mode("overwrite").parquet(facts_output_path)

        aggs = self.compute_aggregations(transformed_df)
        for name, agg_df in aggs.items():
            agg_path = str(processed_dir / f"agg_{name}.parquet")
            logger.info(f"Writing aggregation dataset '{name}' to {agg_path}...")
            agg_df.write.mode("overwrite").parquet(agg_path)

        logger.info("PySpark transformation pipeline finished successfully.")
        return True


def main():
    parser = argparse.ArgumentParser(description="PySpark NYC Taxi Data Transformer")
    parser.parse_args()

    transformer = TaxiDataTransformer()
    success = transformer.process_validated_directory()
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
