#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = ["tqdm"]
# ///

"""
Migration utility to transfer local SQLite database to Cloudflare D1.

This script:
1. Dumps the local SQLite database to SQL format
2. Transforms the SQL for D1 compatibility
3. Imports the data via wrangler CLI
4. Validates the migration success

Usage:
    migrate_to_d1.py [--local-db PATH] [--remote-db NAME] [--dry-run]
"""

import argparse
import logging
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
from tqdm import tqdm

# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_LOCAL_DB = Path.home() / ".local/share/claude/conversations.db"
DEFAULT_REMOTE_DB = "claude"

# ============================================================================
# LOGGING SETUP
# ============================================================================


def setup_logging(verbose: bool = False) -> None:
    """Configure logging with appropriate level and format."""
    level = logging.DEBUG if verbose else logging.INFO
    log_format = "%(asctime)s [%(levelname)s] %(message)s"
    date_format = "%H:%M:%S"

    logging.basicConfig(level=level, format=log_format, datefmt=date_format)


# ============================================================================
# CLI ARGUMENT PARSING
# ============================================================================


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Migrate local SQLite database to Cloudflare D1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard migration
  migrate_to_d1.py

  # Custom local database
  migrate_to_d1.py --local-db /path/to/conversations.db

  # Custom remote database name
  migrate_to_d1.py --remote-db my-claude-db

  # Dry run to see SQL without executing
  migrate_to_d1.py --dry-run

  # Verbose output
  migrate_to_d1.py --verbose
        """,
    )

    parser.add_argument(
        "--local-db",
        type=Path,
        default=DEFAULT_LOCAL_DB,
        help=f"Local SQLite database path (default: {DEFAULT_LOCAL_DB})",
    )

    parser.add_argument(
        "--remote-db",
        type=str,
        default=DEFAULT_REMOTE_DB,
        help=f"Remote D1 database name (default: {DEFAULT_REMOTE_DB})",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate SQL but don't execute migration",
    )

    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging (DEBUG level)"
    )

    return parser.parse_args()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def get_table_record_count(conn: sqlite3.Connection, table: str) -> int:
    """Get record count for a specific table."""
    try:
        cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
        result = cursor.fetchone()
        return result[0] if result else 0
    except sqlite3.OperationalError as e:
        logging.warning(f"Could not count records in {table}: {e}")
        return 0


def get_database_stats(db_path: Path) -> Dict[str, int]:
    """Get statistics about the local database."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Get all table names
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    tables = [row[0] for row in cursor.fetchall()]

    stats = {}
    total_records = 0

    for table in tqdm(tables, desc="Analyzing local database"):
        count = get_table_record_count(conn, table)
        stats[table] = count
        total_records += count

    conn.close()

    logging.info(f"Local database stats: {total_records:,} total records across {len(tables)} tables")
    for table, count in sorted(stats.items()):
        logging.info(f"  {table}: {count:,} records")

    return stats


def dump_local_database(db_path: Path) -> str:
    """Dump local SQLite database to SQL format."""
    logging.info(f"Dumping local database: {db_path}")

    try:
        result = subprocess.run(
            ["sqlite3", str(db_path), ".dump"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to dump local database: {e.stderr}")
    except FileNotFoundError:
        raise RuntimeError("sqlite3 command not found. Please install sqlite3.")


def transform_sql_for_d1(sql_dump: str) -> str:
    """Transform SQLite dump for D1 compatibility."""
    logging.info("Transforming SQL for D1 compatibility")

    lines = sql_dump.split('\n')
    transformed_lines = []

    # Tables to skip (SQLite system tables)
    skip_statements = [
        'sqlite_sequence',
        'sqlite_stat1',
    ]

    for line in lines:
        line = line.strip()

        # Skip empty lines and comments
        if not line or line.startswith('--'):
            continue

        # Skip SQLite-specific pragmas
        if line.upper().startswith('PRAGMA'):
            continue

        # Skip certain table statements
        if any(skip in line.upper() for skip in skip_statements):
            continue

        # Skip BEGIN/COMMIT transactions (D1 handles differently)
        if line.upper() in ('BEGIN TRANSACTION;', 'COMMIT;'):
            continue

        # Transform AUTOINCREMENT (D1 uses standard SQL)
        line = line.replace('AUTOINCREMENT', '')

        # Transform any other SQLite-specific syntax if needed
        # Add more transformations as discovered during testing

        transformed_lines.append(line)

    return '\n'.join(transformed_lines)


def execute_d1_migration(sql: str, db_name: str) -> None:
    """Execute migration via wrangler CLI."""
    logging.info(f"Executing migration to D1 database: {db_name}")

    # Write SQL to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
        f.write(sql)
        temp_file = f.name

    try:
        result = subprocess.run(
            [
                "wrangler",
                "d1",
                "execute",
                db_name,
                "--remote",
                "--file",
                temp_file,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        logging.info("✅ Migration executed successfully")
        if result.stdout:
            logging.debug(f"Wrangler output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Migration failed: {e.stderr}")
    except FileNotFoundError:
        raise RuntimeError("wrangler command not found. Please install wrangler.")
    finally:
        # Clean up temporary file
        Path(temp_file).unlink(missing_ok=True)


def get_remote_d1_stats(db_name: str) -> Dict[str, int]:
    """Get statistics about the remote D1 database."""
    logging.info(f"Getting remote D1 database stats: {db_name}")

    try:
        # Get table names
        result = subprocess.run(
            [
                "wrangler",
                "d1",
                "execute",
                db_name,
                "--remote",
                "--command",
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'",
                "--json",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        import json
        tables_result = json.loads(result.stdout)
        if not tables_result or not tables_result[0]:
            return {}

        tables = [row['name'] for row in tables_result[0]['results']]

        stats = {}
        total_records = 0

        for table in tqdm(tables, desc="Analyzing remote database"):
            try:
                result = subprocess.run(
                    [
                        "wrangler",
                        "d1",
                        "execute",
                        db_name,
                        "--remote",
                        "--command",
                        f"SELECT COUNT(*) as count FROM {table}",
                        "--json",
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )

                count_result = json.loads(result.stdout)
                if count_result and count_result[0] and count_result[0]['results']:
                    count = count_result[0]['results'][0]['count']
                    stats[table] = count
                    total_records += count
                else:
                    stats[table] = 0

            except subprocess.CalledProcessError as e:
                logging.warning(f"Could not count records in {table}: {e}")
                stats[table] = 0

        logging.info(f"Remote D1 database stats: {total_records:,} total records across {len(tables)} tables")
        for table, count in sorted(stats.items()):
            logging.info(f"  {table}: {count:,} records")

        return stats

    except Exception as e:
        logging.error(f"Failed to get remote D1 stats: {e}")
        return {}


def validate_migration(local_stats: Dict[str, int], remote_stats: Dict[str, int]) -> bool:
    """Validate that migration was successful."""
    logging.info("Validating migration...")

    all_tables_match = True
    missing_tables = []
    mismatched_counts = []

    # Check all local tables exist remotely and have matching counts
    for table, local_count in local_stats.items():
        if table not in remote_stats:
            missing_tables.append(table)
            all_tables_match = False
        elif remote_stats[table] != local_count:
            mismatched_counts.append((table, local_count, remote_stats[table]))
            all_tables_match = False

    # Report results
    if all_tables_match:
        logging.info("✅ Migration validation successful - all records match")
        return True
    else:
        logging.error("❌ Migration validation failed:")
        if missing_tables:
            logging.error(f"  Missing tables in remote: {missing_tables}")
        if mismatched_counts:
            logging.error("  Record count mismatches:")
            for table, local, remote in mismatched_counts:
                logging.error(f"    {table}: local={local:,}, remote={remote:,}")
        return False


# ============================================================================
# MAIN EXECUTION
# ============================================================================


def main() -> int:
    """Main migration execution."""
    args = parse_args()
    setup_logging(args.verbose)

    logger = logging.getLogger(__name__)

    # Validate local database exists
    if not args.local_db.exists():
        logger.error(f"Local database not found: {args.local_db}")
        return 1

    try:
        # Step 1: Get local database statistics
        logger.info("=" * 60)
        logger.info("STEP 1: Analyzing local database")
        logger.info("=" * 60)
        local_stats = get_database_stats(args.local_db)

        # Step 2: Dump local database
        logger.info("=" * 60)
        logger.info("STEP 2: Dumping local database to SQL")
        logger.info("=" * 60)
        sql_dump = dump_local_database(args.local_db)
        logger.info(f"✅ Dumped {len(sql_dump):,} characters of SQL")

        # Step 3: Transform SQL for D1
        logger.info("=" * 60)
        logger.info("STEP 3: Transforming SQL for D1 compatibility")
        logger.info("=" * 60)
        d1_sql = transform_sql_for_d1(sql_dump)
        logger.info(f"✅ Transformed SQL (reduced to {len(d1_sql):,} characters)")

        # Step 4: Execute migration (unless dry run)
        if args.dry_run:
            logger.info("=" * 60)
            logger.info("STEP 4: DRY RUN - Not executing migration")
            logger.info("=" * 60)
            logger.info("SQL generated but not executed. Use without --dry-run to perform migration.")
            return 0
        else:
            logger.info("=" * 60)
            logger.info("STEP 4: Executing migration to remote D1")
            logger.info("=" * 60)
            execute_d1_migration(d1_sql, args.remote_db)

        # Step 5: Validate migration
        logger.info("=" * 60)
        logger.info("STEP 5: Validating migration")
        logger.info("=" * 60)
        remote_stats = get_remote_d1_stats(args.remote_db)

        if validate_migration(local_stats, remote_stats):
            logger.info("=" * 60)
            logger.info("🎉 MIGRATION COMPLETED SUCCESSFULLY!")
            logger.info("=" * 60)
            return 0
        else:
            logger.error("=" * 60)
            logger.error("❌ MIGRATION VALIDATION FAILED!")
            logger.error("=" * 60)
            return 1

    except Exception as e:
        logger.exception(f"Migration failed with error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())