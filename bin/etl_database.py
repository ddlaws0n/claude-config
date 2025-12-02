"""Database connection and operations."""

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite connection with remote-ready patterns."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self):
        """Establish database connection."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

        # WAL mode for better concurrency
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")

        logger.info(f"Connected to: {self.db_path}")

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    @contextmanager
    def transaction(self):
        """Transaction context manager."""
        try:
            yield self.conn
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def setup_schema(self):
        """Initialize schema (idempotent)."""
        schema_path = Path(__file__).parent / "schema.sql"

        with open(schema_path) as f:
            schema_sql = f.read()

        with self.transaction():
            self.conn.executescript(schema_sql)

        logger.info("Schema initialized")

    def execute_batch(
        self, sql: str, records: List[tuple], batch_size: int = 1000
    ) -> int:
        """Batch insert with chunking."""
        if not records:
            return 0

        total_inserted = 0

        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]

            with self.transaction():
                assert self.conn is not None
                cursor = self.conn.executemany(sql, batch)
                total_inserted += cursor.rowcount

        return total_inserted

    def query_one(self, sql: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Execute query, return single result."""
        assert self.conn is not None
        cursor = self.conn.execute(sql, params)
        return cursor.fetchone()  # type: ignore[no-any-return]
