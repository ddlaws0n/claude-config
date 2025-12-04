"""Database abstraction layer supporting local SQLite and remote Cloudflare D1."""

import json
import logging
import sqlite3
import subprocess
import tempfile
from abc import ABC, abstractmethod
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DatabaseBackend(ABC):
    """Abstract base class for database backends."""

    @abstractmethod
    def connect(self) -> None:
        """Establish database connection."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close database connection."""
        pass

    @abstractmethod
    def setup_schema(self) -> None:
        """Initialize database schema."""
        pass

    @abstractmethod
    def execute_batch(
        self, sql: str, records: List[tuple], batch_size: int = 1000
    ) -> int:
        """Execute batch insert/update operations."""
        pass

    @abstractmethod
    def query_one(self, sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Execute query and return single result."""
        pass

    @abstractmethod
    def transaction(self):
        """Transaction context manager."""
        pass


class LocalSQLiteBackend(DatabaseBackend):
    """Local SQLite database backend (existing functionality)."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        """Establish local SQLite connection."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

        # WAL mode for better concurrency
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")

        logger.info(f"Connected to local SQLite: {self.db_path}")

    def close(self) -> None:
        """Close local SQLite connection."""
        if self.conn:
            self.conn.close()

    @contextmanager
    def transaction(self):
        """Local SQLite transaction context manager."""
        try:
            yield self.conn
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def setup_schema(self) -> None:
        """Initialize schema from schema.sql file."""
        schema_path = Path(__file__).parent / "schema.sql"

        with open(schema_path) as f:
            schema_sql = f.read()

        with self.transaction():
            if self.conn is not None:
                self.conn.executescript(schema_sql)

        logger.info("Local SQLite schema initialized")

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
                if self.conn is not None:
                    cursor = self.conn.executemany(sql, batch)
                    total_inserted += cursor.rowcount

        return total_inserted

    def query_one(self, sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Execute query, return single result as dict."""
        if self.conn is not None:
            cursor = self.conn.execute(sql, params)
            row = cursor.fetchone()
            return dict(row) if row else None
        return None


class RemoteD1Backend(DatabaseBackend):
    """Remote Cloudflare D1 database backend via wrangler CLI."""

    def __init__(self, db_name: str = "claude"):
        self.db_name = db_name
        self._connected = False
        # Smart buffering to reduce CLI overhead
        self._buffer: Dict[str, List[tuple]] = {}
        self._buffer_limit = 500  # Records per buffer
        self._statement_char_limit = 50000  # Characters per SQL statement

    def connect(self) -> None:
        """Verify D1 database connection."""
        try:
            result = self._execute_wrangler("SELECT 1 as test", json_output=True)
            if isinstance(result, list) and len(result) > 0:
                self._connected = True
                logger.info(f"Connected to remote D1 database: {self.db_name}")
            else:
                raise RuntimeError("D1 connection test failed - invalid response format")
        except Exception as e:
            self._connected = False
            raise RuntimeError(f"Failed to connect to D1 database '{self.db_name}': {e}")

    def close(self) -> None:
        """Flush buffer and close connection."""
        self._flush_all_buffers()
        self._connected = False
        logger.info("D1 connection closed")

    def setup_schema(self) -> None:
        """Initialize schema using wrangler and schema.sql file."""
        schema_path = Path(__file__).parent / "schema.sql"
        try:
            subprocess.run(
                ["wrangler", "d1", "execute", self.db_name, "--file", str(schema_path)],
                capture_output=True,
                text=True,
                check=True,
            )
            logger.info("D1 schema initialized successfully")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Schema setup failed: {e.stderr}")

    @contextmanager
    def transaction(self):
        """
        D1 transaction context.
        WARNING: D1 interactions via CLI are sequential and NOT truly atomic.
        A failure in the middle of a batch will leave previous records committed.
        """
        commands = []

        class D1Transaction:
            def __init__(self, backend):
                self.backend = backend
                self.commands = commands

            def execute(self, sql: str, params: tuple = ()):
                self.commands.append((sql, params))
                return self

        try:
            yield D1Transaction(self)
            for sql, params in commands:
                # Format parameters into the SQL string for execution
                formatted_sql = sql
                for param in params:
                    formatted_sql = formatted_sql.replace("?", self.backend._format_value(param), 1)
                self.backend._execute_wrangler(formatted_sql, json_output=False)
        except Exception as e:
            logger.error(f"D1 transaction failed: {e}")
            raise

    def execute_batch(
        self, sql: str, records: List[tuple], batch_size: int = 1000
    ) -> int:
        """
        Smart buffering batch execute for D1.

        This method accumulates records across multiple calls and only executes
        when the buffer reaches the limit or when explicitly flushed.
        This dramatically reduces CLI overhead from hundreds of subprocess calls
        to just a few dozen.
        """
        if not records:
            return 0

        # Use SQL as buffer key (normalized)
        buffer_key = sql.strip()

        # Initialize buffer if needed
        if buffer_key not in self._buffer:
            self._buffer[buffer_key] = []

        # Add records to buffer
        self._buffer[buffer_key].extend(records)
        total_buffered = len(self._buffer[buffer_key])

        # Check if we should flush the buffer
        should_flush = (
            total_buffered >= self._buffer_limit or
            self._estimate_statement_size(buffer_key, self._buffer[buffer_key]) > self._statement_char_limit
        )

        if should_flush:
            return self._flush_buffer(buffer_key)
        else:
            # Return number of records buffered but not yet executed
            return len(records)

    def _estimate_statement_size(self, sql: str, records: List[tuple]) -> int:
        """Estimate the size of the SQL statement if we were to execute it."""
        if not records:
            return len(sql)

        # Get the INSERT part (before VALUES)
        if "VALUES" in sql:
            insert_part = sql.split("VALUES")[0].strip()
        else:
            insert_part = sql.strip()

        # Estimate a few records to get average size
        sample_size = min(5, len(records))
        sample_records = records[:sample_size]

        sample_values = []
        for record in sample_records:
            formatted = [self._format_value(v) for v in record]
            sample_values.append(f"({','.join(formatted)})")

        avg_record_size = sum(len(v) for v in sample_values) / len(sample_values)

        # Estimate total size
        estimated_size = len(insert_part) + len(" VALUES ") + (avg_record_size * len(records))
        return int(estimated_size)

    def _flush_buffer(self, buffer_key: str) -> int:
        """Execute buffered records and clear the buffer."""
        if buffer_key not in self._buffer or not self._buffer[buffer_key]:
            return 0

        records = self._buffer[buffer_key]
        self._buffer[buffer_key] = []  # Clear buffer immediately

        try:
            # Extract the INSERT part (before VALUES)
            if "VALUES" in buffer_key:
                insert_part = buffer_key.split("VALUES")[0].strip()
            else:
                logger.warning("Could not split SQL on VALUES, using as is")
                insert_part = buffer_key.strip()

            # Process records in smaller chunks to avoid SQLITE_TOOBIG
            chunk_size = 100  # Conservative chunk size
            total_inserted = 0

            for i in range(0, len(records), chunk_size):
                chunk = records[i:i + chunk_size]
                values_groups = []

                # Construct VALUES clauses for this chunk
                for record in chunk:
                    formatted = [self._format_value(v) for v in record]
                    values_groups.append(f"({','.join(formatted)})")

                # Create SQL for this chunk
                all_values = ",\n".join(values_groups)
                chunk_sql = f"{insert_part} VALUES {all_values};"

                # Execute this chunk
                self._execute_wrangler_file(chunk_sql)
                total_inserted += len(chunk)
                logger.debug(f"Flushed chunk of {len(chunk)} records")

            logger.info(f"Successfully flushed {total_inserted} records from buffer")
            return total_inserted

        except Exception as e:
            logger.error(f"Buffer flush failed: {e}")
            # Put remaining records back in buffer for retry
            self._buffer[buffer_key] = records[len(records) - total_inserted:] if total_inserted > 0 else records
            raise

    def _flush_all_buffers(self) -> int:
        """Flush all buffered records across all SQL statements."""
        total_flushed = 0
        buffer_keys = list(self._buffer.keys())  # Copy keys to avoid modification during iteration

        for buffer_key in buffer_keys:
            if self._buffer[buffer_key]:
                try:
                    flushed = self._flush_buffer(buffer_key)
                    total_flushed += flushed
                except Exception as e:
                    logger.error(f"Failed to flush buffer for {buffer_key[:50]}...: {e}")

        if total_flushed > 0:
            logger.info(f"Flushed {total_flushed} total records from all buffers")

        return total_flushed

    def query_one(self, sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Execute query on D1 and return single result."""
        try:
            formatted_sql = sql
            for param in params:
                formatted_sql = formatted_sql.replace("?", self._format_value(param), 1)

            result = self._execute_wrangler(formatted_sql, json_output=True)

            if isinstance(result, list) and len(result) > 0:
                result_set = result[0]
                if isinstance(result_set, dict) and "results" in result_set:
                    results = result_set["results"]
                    return results[0] if results else None
                elif isinstance(result_set, dict):
                    return result_set if result_set else None
            return None
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return None

    def _execute_wrangler(self, sql: str, json_output: bool = True) -> Any:
        """Execute SQL command via wrangler CLI string argument."""
        cmd = ["wrangler", "d1", "execute", self.db_name, "--command", sql]
        if json_output:
            cmd.append("--json")

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, timeout=600
            )
            if json_output:
                return json.loads(result.stdout)
            return {"success": True}
        except Exception as e:
            # Clean up error message for logging
            msg = str(e)
            if hasattr(e, 'stderr'):
                msg += f"\nStderr: {e.stderr}"
            raise RuntimeError(f"D1 operation failed: {msg}")

    def _execute_wrangler_file(self, sql_content: str) -> None:
        """Write SQL to temp file and execute via wrangler."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
            f.write(sql_content)
            temp_path = f.name

        try:
            subprocess.run(
                ["wrangler", "d1", "execute", self.db_name, "--file", temp_path],
                capture_output=True,
                text=True,
                check=True,
                timeout=600
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"D1 batch operation failed: {e.stderr}")
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def _format_value(self, value: Any) -> str:
        """Format value for SQL insertion."""
        if value is None:
            return "NULL"
        elif isinstance(value, bool):
            return "1" if value else "0"
        elif isinstance(value, (int, float)):
            return str(value)
        else:
            # String escaping
            str_val = str(value).replace("'", "''")
            return f"'{str_val}'"