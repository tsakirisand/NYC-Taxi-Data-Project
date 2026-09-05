"""Storage Manager abstraction supporting Local File System and AWS S3."""

from pathlib import Path
from typing import Union
from src.utils.config import settings
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class StorageManager:
    """Storage manager to abstract file path resolution and cloud S3 access."""

    def __init__(
        self,
        storage_type: str = settings.STORAGE_TYPE,
        s3_bucket: str = settings.S3_BUCKET,
    ):
        self.storage_type = storage_type
        self.s3_bucket = s3_bucket

    def get_path(self, relative_path: str, stage: str = "raw") -> str:
        """Resolve a full storage path based on configured storage type.

        Args:
            relative_path: Filename or relative path (e.g., 'yellow_tripdata_2025-01.parquet')
            stage: Stage folder ('raw', 'validated', 'processed', 'reference')

        Returns:
            str: Resolved local file path or S3 URI (s3://bucket/stage/...)
        """
        if self.storage_type.lower() == "s3":
            return f"s3://{self.s3_bucket}/{stage}/{relative_path}"

        if stage == "raw":
            base = settings.RAW_DATA_DIR
        elif stage == "validated":
            base = settings.VALIDATED_DATA_DIR
        elif stage == "processed":
            base = settings.PROCESSED_DATA_DIR
        elif stage == "reference":
            base = settings.REFERENCE_DATA_DIR
        else:
            base = settings.BASE_DIR / stage

        full_path = base / relative_path
        return str(full_path)

    def file_exists(self, file_path: Union[str, Path]) -> bool:
        """Check if a file exists locally or on S3."""
        str_path = str(file_path)
        if str_path.startswith("s3://"):
            # Future AWS S3 check via boto3
            logger.info(f"S3 mode: Checking existence for {str_path}")
            return False
        return Path(str_path).exists() and Path(str_path).stat().st_size > 0
