"""Configuration management using Pydantic Settings."""

import json
from pathlib import Path
from typing import Any, List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration class for the pipeline."""

    # Project Root
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    # Data Storage Paths
    RAW_DATA_DIR: Path = BASE_DIR / "data" / "raw"
    VALIDATED_DATA_DIR: Path = BASE_DIR / "data" / "validated"
    PROCESSED_DATA_DIR: Path = BASE_DIR / "data" / "processed"
    REFERENCE_DATA_DIR: Path = BASE_DIR / "data" / "reference"

    # Ingestion Defaults
    NYC_TLC_BASE_URL: str = "https://d37ci6vzurychx.cloudfront.net/trip-data"
    TAXI_ZONE_LOOKUP_URL: str = (
        "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"
    )
    DEFAULT_YEAR: int = 2025
    DEFAULT_MONTHS: List[int] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

    @field_validator("DEFAULT_MONTHS", mode="before")
    @classmethod
    def parse_default_months(cls, v: Any) -> List[int]:
        """Parse DEFAULT_MONTHS safely from comma-separated string, JSON array, or list."""
        if isinstance(v, str):
            v_str = v.strip()
            if v_str.startswith("[") and v_str.endswith("]"):
                try:
                    return [int(x) for x in json.loads(v_str)]
                except Exception:
                    pass
            return [int(m.strip()) for m in v_str.split(",") if m.strip()]
        elif isinstance(v, (list, tuple)):
            return [int(x) for x in v]
        return [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

    # Database Configuration
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "nyc_taxi_db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    DB_ENGINE_TYPE: str = "postgresql"  # 'postgresql' or 'sqlite'
    SQLITE_DB_PATH: Path = BASE_DIR / "data" / "nyc_taxi.db"

    # Cloud / AWS S3 Extensibility
    STORAGE_TYPE: str = "local"  # 'local' or 's3'
    S3_BUCKET: Optional[str] = "nyc-taxi-data-lake"
    AWS_REGION: str = "us-east-1"

    # Logging & Runtime
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Path = BASE_DIR / "pipeline.log"

    @property
    def postgres_sqlalchemy_url(self) -> str:
        """Return SQLAlchemy database connection string for PostgreSQL."""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def sqlite_sqlalchemy_url(self) -> str:
        """Return SQLAlchemy database connection string for SQLite fallback."""
        return f"sqlite:///{self.SQLITE_DB_PATH}"

    @property
    def db_url(self) -> str:
        """Return database connection URL depending on DB_ENGINE_TYPE."""
        if self.DB_ENGINE_TYPE.lower() == "sqlite":
            return self.sqlite_sqlalchemy_url
        return self.postgres_sqlalchemy_url

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()

# Ensure directories exist
for path in [
    settings.RAW_DATA_DIR,
    settings.VALIDATED_DATA_DIR,
    settings.PROCESSED_DATA_DIR,
    settings.REFERENCE_DATA_DIR,
]:
    path.mkdir(parents=True, exist_ok=True)
