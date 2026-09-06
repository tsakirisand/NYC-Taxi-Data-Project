"""Apache Airflow Orchestration DAG for NYC Taxi Data Engineering Pipeline.

Runs ingestion, data validation, PySpark transformations, PostgreSQL loading, and verification.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Ensure src modules are resolvable by Airflow worker
DAG_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = DAG_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
except ImportError:
    # Graceful fallback mock for testing DAG syntax outside Airflow worker
    class DAG:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    class PythonOperator:
        def __init__(self, *args, **kwargs):
            pass


def task_download_data(**kwargs):
    """Task 1: Download raw NYC Yellow Taxi Parquet files."""
    from src.ingestion.download_taxi_data import TaxiDataDownloader
    from src.utils.logging_config import get_logger

    logger = get_logger("airflow.download")
    logger.info("Airflow Task 1: Starting data ingestion...")

    downloader = TaxiDataDownloader()
    # Download 2025 all 12 months by default
    downloaded = downloader.download_year(year=2025)
    logger.info(f"Airflow Task 1 Finished. Downloaded {len(downloaded)} files.")
    return [str(p) for p in downloaded]


def task_validate_data(**kwargs):
    """Task 2: Validate raw Parquet files and generate data quality metrics."""
    from src.validation.validate_data import DataValidator
    from src.utils.logging_config import get_logger

    logger = get_logger("airflow.validate")
    logger.info("Airflow Task 2: Validating data quality...")

    validator = DataValidator()
    success = validator.validate_raw_directory()
    if not success:
        raise ValueError("Data validation failed quality thresholds!")
    logger.info("Airflow Task 2 Finished successfully.")


def task_transform_data(**kwargs):
    """Task 3: Execute PySpark transformations and create aggregations."""
    from src.transformation.transform_taxi_data import TaxiDataTransformer
    from src.utils.logging_config import get_logger

    logger = get_logger("airflow.transform")
    logger.info("Airflow Task 3: Starting PySpark transformations...")

    transformer = TaxiDataTransformer()
    success = transformer.process_validated_directory()
    if not success:
        raise RuntimeError("PySpark transformation failed!")
    logger.info("Airflow Task 3 Finished successfully.")


def task_load_postgres(**kwargs):
    """Task 4: Load transformed Parquet files into PostgreSQL / SQLite database."""
    from src.database.load_postgres import DatabaseLoader
    from src.utils.logging_config import get_logger

    logger = get_logger("airflow.load")
    logger.info("Airflow Task 4: Loading data into relational database...")

    loader = DatabaseLoader()
    loader.run_full_pipeline()
    logger.info("Airflow Task 4 Finished successfully.")


def task_run_analytics(**kwargs):
    """Task 5: Execute analytical SQL queries."""
    from src.database.load_postgres import DatabaseLoader
    from src.utils.logging_config import get_logger

    logger = get_logger("airflow.analytics")
    logger.info("Airflow Task 5: Running analytical SQL queries...")

    loader = DatabaseLoader()
    loader.run_analytics_queries()
    logger.info("Airflow Task 5 Finished successfully.")


def task_verify_pipeline(**kwargs):
    """Task 6: Pipeline end-to-end verification check."""
    from src.database.load_postgres import DatabaseLoader
    from src.utils.logging_config import get_logger
    from sqlalchemy import text

    logger = get_logger("airflow.verify")
    logger.info("Airflow Task 6: Verifying pipeline end-to-end integrity...")

    loader = DatabaseLoader()
    with loader.engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM fact_trips"))
        count = result.scalar()

    logger.info(f"Verification Check: fact_trips contains {count:,} total records.")
    if count == 0:
        raise ValueError("Pipeline verification failed: fact_trips is empty!")
    logger.info("Pipeline verification check PASSED!")


default_args = {
    "owner": "data_engineering_team",
    "depends_on_past": False,
    "start_date": datetime(2025, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="nyc_taxi_etl_pipeline",
    default_args=default_args,
    description="End-to-end NYC Yellow Taxi ETL pipeline orchestrator",
    schedule_interval="@monthly",
    catchup=False,
    max_active_runs=1,
    tags=["nyc_taxi", "pyspark", "postgres", "data_engineering"],
) as dag:

    t1_download = PythonOperator(
        task_id="download_nyc_taxi_data",
        python_callable=task_download_data,
    )

    t2_validate = PythonOperator(
        task_id="validate_data_quality",
        python_callable=task_validate_data,
    )

    t3_transform = PythonOperator(
        task_id="transform_with_pyspark",
        python_callable=task_transform_data,
    )

    t4_load = PythonOperator(
        task_id="load_into_postgres",
        python_callable=task_load_postgres,
    )

    t5_analytics = PythonOperator(
        task_id="run_analytical_sql",
        python_callable=task_run_analytics,
    )

    t6_verify = PythonOperator(
        task_id="verify_pipeline_integrity",
        python_callable=task_verify_pipeline,
    )

    # Define Directed Acyclic Graph (DAG) Task Dependencies
    t1_download >> t2_validate >> t3_transform >> t4_load >> t5_analytics >> t6_verify
