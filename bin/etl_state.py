"""ETL state tracking for hybrid incremental loading."""

import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class StateTracker:
    """Tracks file processing state for incremental loading."""

    def __init__(self, db, force: bool = False):
        self.db = db
        self.force = force
        self.run_timestamp = datetime.now()

    def should_process_file(self, source: str, file_path: Path) -> bool:
        """
        Hybrid incremental strategy:
        - If --force: always True
        - If new file: True
        - If modified (mtime or size changed): True
        - Otherwise: False
        """
        if self.force:
            return True

        stat = file_path.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime)

        result = self.db.query_one(
            "SELECT mtime, size FROM etl_file_state WHERE file_path = ?",
            (str(file_path),),
        )

        if not result:
            return True  # New file

        prev_mtime = datetime.fromisoformat(result["mtime"])
        prev_size = result["size"]

        return mtime > prev_mtime or stat.st_size != prev_size

    def mark_processed(self, source: str, file_path: Path):
        """Mark file as processed."""
        stat = file_path.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime)

        with self.db.transaction():
            assert self.db.conn is not None
            self.db.conn.execute(
                """
                INSERT OR REPLACE INTO etl_file_state
                (file_path, source, mtime, size, last_processed)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    str(file_path),
                    source,
                    mtime.isoformat(),
                    stat.st_size,
                    self.run_timestamp.isoformat(),
                ),
            )

    def log_run(
        self,
        source: str,
        files: int,
        records: int,
        errors: int,
        duration: float,
        status: str,
    ):
        """Log ETL run statistics."""
        with self.db.transaction():
            assert self.db.conn is not None
            self.db.conn.execute(
                """
                INSERT INTO etl_runs
                (run_timestamp, source, files_processed, records_inserted,
                 errors_count, duration_seconds, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.run_timestamp.isoformat(),
                    source,
                    files,
                    records,
                    errors,
                    duration,
                    status,
                ),
            )
