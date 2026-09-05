"""Data Validation Module.

Performs data quality validation checks using PyArrow / Pandas / PySpark on raw Parquet files.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd

from src.utils.config import settings
from src.utils.logging_config import get_logger
from src.utils.storage import StorageManager

logger = get_logger(__name__)


class DataValidator:
    """Validator class for NYC Taxi Trip Datasets."""

    def __init__(
        self,
        storage: Optional[StorageManager] = None,
        max_invalid_ratio: float = 0.5,
    ):
        self.storage = storage or StorageManager()
        self.max_invalid_ratio = max_invalid_ratio

    def validate_file(
        self, input_path: Path, output_path: Path
    ) -> Tuple[bool, Dict[str, Any]]:
        """Validate a single Parquet file and save the cleaned version.

        Args:
            input_path: Path to raw Parquet file
            output_path: Path where validated clean file should be saved

        Returns:
            Tuple[bool, Dict[str, Any]]: (success_flag, metrics_dict)
        """
        logger.info(f"Starting data validation for {input_path}...")

        try:
            table = pq.read_table(input_path)
            df = table.to_pandas()
        except Exception as e:
            logger.error(f"Failed to read Parquet file {input_path}: {e}")
            return False, {"error": str(e)}

        total_rows_initial = len(df)
        if total_rows_initial == 0:
            logger.error(f"File {input_path} contains 0 rows.")
            return False, {"error": "Empty dataset"}

        metrics: Dict[str, Any] = {
            "input_file": str(input_path),
            "output_file": str(output_path),
            "total_rows_initial": total_rows_initial,
            "failed_checks": {},
        }

        # Handle column name standardization
        pickup_col = "tpep_pickup_datetime"
        dropoff_col = "tpep_dropoff_datetime"

        if pickup_col not in df.columns or dropoff_col not in df.columns:
            logger.error(f"Missing required timestamp columns in {input_path}.")
            return False, {"error": "Missing timestamp columns"}

        # Convert timestamps to datetime
        df[pickup_col] = pd.to_datetime(df[pickup_col])
        df[dropoff_col] = pd.to_datetime(df[dropoff_col])

        # 1. Null pickup / dropoff timestamps
        null_ts_mask = df[pickup_col].isna() | df[dropoff_col].isna()
        metrics["failed_checks"]["null_timestamps"] = int(null_ts_mask.sum())

        # 2. Invalid timestamps (dropoff before pickup or unreasonable range)
        duration_minutes = (df[dropoff_col] - df[pickup_col]).dt.total_seconds() / 60.0
        invalid_ts_mask = (df[dropoff_col] <= df[pickup_col]) | (
            duration_minutes > 1440
        )  # > 24 hours
        metrics["failed_checks"]["invalid_timestamps"] = int(invalid_ts_mask.sum())

        # 3. Negative trip distances
        invalid_dist_mask = df["trip_distance"] <= 0
        metrics["failed_checks"]["negative_or_zero_distance"] = int(
            invalid_dist_mask.sum()
        )

        # 4. Negative fares & totals
        invalid_fare_mask = (df["fare_amount"] < 0) | (df["total_amount"] < 0)
        metrics["failed_checks"]["negative_fares"] = int(invalid_fare_mask.sum())

        # 5. Invalid passenger count (allow null or 1..9, flag <= 0 or > 9)
        invalid_passengers_mask = (df["passenger_count"] <= 0) | (
            df["passenger_count"] > 9
        )
        metrics["failed_checks"]["invalid_passenger_count"] = int(
            invalid_passengers_mask.fillna(False).sum()
        )

        # 6. Invalid taxi zones (outside 1..265)
        invalid_zone_mask = (
            (df["PULocationID"] < 1)
            | (df["PULocationID"] > 265)
            | (df["DOLocationID"] < 1)
            | (df["DOLocationID"] > 265)
        )
        metrics["failed_checks"]["invalid_location_ids"] = int(invalid_zone_mask.sum())

        # Combine invalid row mask
        invalid_rows_mask = (
            null_ts_mask
            | invalid_ts_mask
            | invalid_dist_mask
            | invalid_fare_mask
            | invalid_zone_mask
        )

        # 7. Deduplication
        cleaned_df = df[~invalid_rows_mask].copy()
        dedup_subset = [
            pickup_col,
            dropoff_col,
            "PULocationID",
            "DOLocationID",
            "fare_amount",
            "trip_distance",
        ]
        duplicates_count = int(cleaned_df.duplicated(subset=dedup_subset).sum())
        metrics["failed_checks"]["duplicates"] = duplicates_count
        cleaned_df.drop_duplicates(subset=dedup_subset, inplace=True)

        total_rows_clean = len(cleaned_df)
        total_rejected = total_rows_initial - total_rows_clean
        rejection_ratio = total_rejected / total_rows_initial

        metrics["total_rows_clean"] = total_rows_clean
        metrics["total_rows_rejected"] = total_rejected
        metrics["rejection_ratio"] = round(rejection_ratio, 4)

        logger.info(
            f"Validation results for {input_path.name}: Initial: {total_rows_initial:,} | "
            f"Clean: {total_rows_clean:,} | Rejected: {total_rejected:,} ({rejection_ratio:.2%})"
        )
        logger.info(
            f"Check details: Null Timestamps: {metrics['failed_checks']['null_timestamps']}, "
            f"Invalid Duration: {metrics['failed_checks']['invalid_timestamps']}, "
            f"Zero/Neg Distance: {metrics['failed_checks']['negative_or_zero_distance']}, "
            f"Neg Fares: {metrics['failed_checks']['negative_fares']}, "
            f"Duplicates: {metrics['failed_checks']['duplicates']}"
        )

        # Quality Threshold Assertion
        if rejection_ratio > self.max_invalid_ratio:
            logger.error(
                f"Validation failed for {input_path.name}! Rejection ratio {rejection_ratio:.2%} "
                f"exceeds maximum allowed threshold of {self.max_invalid_ratio:.2%}."
            )
            return False, metrics

        # Save clean dataset
        output_path.parent.mkdir(parents=True, exist_ok=True)
        clean_table = pa.Table.from_pandas(cleaned_df)
        pq.write_table(clean_table, output_path)

        logger.info(f"Successfully saved validated clean dataset to {output_path}")

        # Log metrics to JSON
        metrics_file = output_path.with_suffix(".json")
        with open(metrics_file, "w") as f:
            json.dump(metrics, f, indent=2)

        return True, metrics

    def validate_raw_directory(self, raw_dir: Path = settings.RAW_DATA_DIR) -> bool:
        """Validate all raw Parquet files in the raw directory."""
        parquet_files = sorted(raw_dir.glob("*.parquet"))
        if not parquet_files:
            logger.warning(f"No raw parquet files found in {raw_dir}")
            return False

        all_success = True
        for raw_file in parquet_files:
            val_file = settings.VALIDATED_DATA_DIR / raw_file.name
            success, _ = self.validate_file(raw_file, val_file)
            if not success:
                all_success = False

        return all_success


def main():
    parser = argparse.ArgumentParser(
        description="NYC Yellow Taxi Data Quality Validator"
    )
    parser.add_argument(
        "--file", type=str, help="Specific raw parquet file to validate"
    )
    args = parser.parse_args()

    validator = DataValidator()

    if args.file:
        raw_path = Path(args.file)
        val_path = settings.VALIDATED_DATA_DIR / raw_path.name
        success, metrics = validator.validate_file(raw_path, val_path)
        if not success:
            sys.exit(1)
    else:
        success = validator.validate_raw_directory()
        if not success:
            sys.exit(1)


if __name__ == "__main__":
    main()
