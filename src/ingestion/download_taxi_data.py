"""Data Ingestion Module.

Downloads official NYC Yellow Taxi trip record Parquet files from NYC TLC.
"""

import argparse
import sys
import time
from pathlib import Path
from typing import List, Optional

import requests

from src.utils.config import settings
from src.utils.logging_config import get_logger
from src.utils.storage import StorageManager

logger = get_logger(__name__)


class TaxiDataDownloader:
    """Downloader for NYC TLC Yellow Taxi dataset."""

    def __init__(
        self,
        base_url: str = settings.NYC_TLC_BASE_URL,
        storage: Optional[StorageManager] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.storage = storage or StorageManager()

    def download_month(
        self, year: int, month: int, force: bool = False
    ) -> Optional[Path]:
        """Download a single month's yellow taxi parquet file.

        Args:
            year: Four-digit year (e.g. 2025)
            month: One-based month (1..12)
            force: If True, redownload file even if it exists.

        Returns:
            Optional[Path]: Path to local downloaded file, or None if download failed.
        """
        filename = f"yellow_tripdata_{year:04d}-{month:02d}.parquet"
        target_path_str = self.storage.get_path(filename, stage="raw")
        target_path = Path(target_path_str)

        if not force and self.storage.file_exists(target_path):
            logger.info(
                f"File {filename} already exists at {target_path} "
                f"(size: {target_path.stat().st_size / 1024 / 1024:.2f} MB). Skipping download."
            )
            return target_path

        url = f"{self.base_url}/{filename}"
        logger.info(f"Downloading {url} -> {target_path}...")

        start_time = time.time()
        try:
            response = requests.get(url, stream=True, timeout=120)
            if response.status_code == 200:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                downloaded_bytes = 0
                with open(target_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
                            downloaded_bytes += len(chunk)

                elapsed = time.time() - start_time
                mb = downloaded_bytes / (1024 * 1024)
                logger.info(
                    f"Successfully downloaded {filename}: {mb:.2f} MB in {elapsed:.2f}s ({mb/elapsed:.2f} MB/s)."
                )
                return target_path

            elif response.status_code == 404:
                logger.warning(f"Data file not found on TLC server (404): {url}")
                return None
            else:
                logger.error(f"HTTP error {response.status_code} when requesting {url}")
                return None

        except Exception as e:
            logger.error(f"Error downloading {url}: {e}", exc_info=True)
            return None

    def download_taxi_zone_lookup(self, force: bool = False) -> Optional[Path]:
        """Download Taxi Zone Lookup CSV file into reference directory."""
        filename = "taxi_zone_lookup.csv"
        target_path_str = self.storage.get_path(filename, stage="reference")
        target_path = Path(target_path_str)

        if not force and self.storage.file_exists(target_path):
            logger.info(f"Taxi Zone Lookup CSV already exists at {target_path}.")
            return target_path

        url = settings.TAXI_ZONE_LOOKUP_URL
        logger.info(f"Downloading Taxi Zone Lookup from {url}...")
        try:
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with open(target_path, "wb") as f:
                    f.write(resp.content)
                logger.info(
                    f"Successfully downloaded Taxi Zone Lookup to {target_path}."
                )
                return target_path
            else:
                logger.error(
                    f"Failed to download zone lookup: Status {resp.status_code}"
                )
                return None
        except Exception as e:
            logger.error(
                f"Exception downloading taxi zone lookup CSV: {e}",
                exc_info=True,
            )
            return None

    def download_year(
        self,
        year: int = settings.DEFAULT_YEAR,
        months: Optional[List[int]] = None,
        force: bool = False,
    ) -> List[Path]:
        """Download taxi trip data for multiple months of a year.

        Args:
            year: Year integer
            months: List of month numbers (1-12)
            force: Whether to overwrite existing files

        Returns:
            List[Path]: Paths of successfully downloaded files
        """
        months_to_download = months or settings.DEFAULT_MONTHS
        logger.info(
            f"Starting dataset download for Year {year}, Months: {months_to_download}"
        )

        # Download zone lookup reference first
        self.download_taxi_zone_lookup(force=force)

        downloaded_files = []
        for m in months_to_download:
            res = self.download_month(year=year, month=m, force=force)
            if res:
                downloaded_files.append(res)

        logger.info(
            f"Download completed. Downloaded/verified {len(downloaded_files)} files."
        )
        return downloaded_files


def main():
    parser = argparse.ArgumentParser(description="NYC TLC Yellow Taxi Data Downloader")
    parser.add_argument(
        "--year",
        type=int,
        default=settings.DEFAULT_YEAR,
        help="Year to download (default: 2025)",
    )
    parser.add_argument(
        "--months",
        type=str,
        default="1,2,3,4,5,6,7,8,9,10,11,12",
        help="Comma-separated months to download, e.g. '1,2,3' or 'all' (default: all 12 months)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-downloading files even if present locally",
    )

    args = parser.parse_args()

    if args.months.lower() in ("all", "12"):
        months = list(range(1, 13))
    else:
        months = [int(m.strip()) for m in args.months.split(",") if m.strip()]

    downloader = TaxiDataDownloader()
    results = downloader.download_year(year=args.year, months=months, force=args.force)

    if not results:
        logger.warning(f"No files downloaded for Year {args.year}, Months {months}.")
        sys.exit(0)
    else:
        logger.info(f"Successfully processed {len(results)} files.")


if __name__ == "__main__":
    main()
