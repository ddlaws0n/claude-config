"""Database connection and operations with backend abstraction."""

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import List, Optional, Dict, Any

from database_backends import DatabaseBackend, LocalSQLiteBackend, RemoteD1Backend

logger = logging.getLogger(__name__)

# Default paths and settings
DEFAULT_DB = Path.home() / ".local/share/claude/conversations.db"


class DatabaseManager:
    """Factory class that selects appropriate database backend."""

    def __init__(
        self,
        db_path: Optional[Path] = None,
        remote: bool = False,
        fallback_to_local: bool = True,
    ):
        """Initialize database manager with appropriate backend.

        Args:
            db_path: Path to local SQLite database (used for local mode)
            remote: If True, attempt to use remote D1 database
            fallback_to_local: If True, fallback to local on remote connection failure
        """
        self.backend: DatabaseBackend
        self.remote = remote
        self.fallback_to_local = fallback_to_local

        if remote:
            try:
                self.backend = RemoteD1Backend()
                logger.info("Initializing remote D1 backend")
            except Exception as e:
                if fallback_to_local:
                    logger.warning(f"Remote D1 unavailable, falling back to local: {e}")
                    self.backend = LocalSQLiteBackend(db_path or DEFAULT_DB)
                    self.remote = False
                else:
                    raise RuntimeError(f"Failed to initialize remote D1 backend: {e}")
        else:
            self.backend = LocalSQLiteBackend(db_path or DEFAULT_DB)
            logger.info("Initializing local SQLite backend")

    def connect(self) -> None:
        """Establish database connection."""
        try:
            self.backend.connect()
        except Exception as e:
            if self.remote and self.fallback_to_local:
                logger.warning(f"Remote connection failed, falling back to local: {e}")
                self.backend = LocalSQLiteBackend(DEFAULT_DB)
                self.remote = False
                self.backend.connect()
            else:
                raise

    def close(self) -> None:
        """Close database connection."""
        self.backend.close()

    @contextmanager
    def transaction(self):
        """Transaction context manager."""
        with self.backend.transaction() as conn:
            yield conn

    def setup_schema(self) -> None:
        """Initialize database schema."""
        self.backend.setup_schema()

    def execute_batch(
        self, sql: str, records: List[tuple], batch_size: int = 1000
    ) -> int:
        """Execute batch insert/update operations."""
        return self.backend.execute_batch(sql, records, batch_size)

    def query_one(self, sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Execute query and return single result."""
        return self.backend.query_one(sql, params)

    @property
    def is_remote(self) -> bool:
        """Check if using remote database."""
        return self.remote and isinstance(self.backend, RemoteD1Backend)
