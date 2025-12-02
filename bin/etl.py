#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = ["tqdm"]
# ///
"""
ETL tool for Claude Code conversation history.

Extracts data from ~/.claude into SQLite database with support
for incremental loading and multi-computer synchronization.

Usage:
    etl.py [--force] [--source DIR] [--db PATH] [--sources LIST]
"""

import argparse
import logging
import sys
from pathlib import Path

from etl_database import DatabaseManager
from etl_extractors import (
    FileHistoryExtractor,
    HistoryLogExtractor,
    PlansExtractor,
    ProjectsExtractor,
    ShellSnapshotsExtractor,
    TodosExtractor,
)
from etl_state import StateTracker

# ============================================================================
# CONSTANTS
# ============================================================================

DEFAULT_SOURCE = Path.home() / ".claude"
DEFAULT_DB = Path.home() / ".local/share/claude/conversations.db"

# ============================================================================
# LOGGING SETUP
# ============================================================================


def setup_logging(verbose: bool = False) -> None:
    """Configure logging with appropriate level and format.

    Args:
        verbose: If True, set level to DEBUG; otherwise INFO
    """
    level = logging.DEBUG if verbose else logging.INFO
    log_format = "%(asctime)s [%(levelname)s] %(message)s"
    date_format = "%H:%M:%S"

    logging.basicConfig(level=level, format=log_format, datefmt=date_format)


# ============================================================================
# CLI ARGUMENT PARSING
# ============================================================================


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments namespace with all CLI options
    """
    parser = argparse.ArgumentParser(
        description="ETL tool for Claude Code conversation history",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard run with incremental loading
  etl.py

  # Force re-process all files
  etl.py --force

  # Process only projects and todos
  etl.py --sources projects,todos

  # Use custom paths
  etl.py --source /path/to/.claude --db /path/to/conversations.db

  # Dry run to see what would be processed
  etl.py --dry-run --verbose
        """,
    )

    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help=f"Source directory (default: {DEFAULT_SOURCE})",
    )

    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help=f"Database path (default: {DEFAULT_DB})",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-process all files (ignore incremental state)",
    )

    parser.add_argument(
        "--sources",
        type=str,
        help="Comma-separated list of sources to extract (projects,todos,file-history,history,plans,shell-snapshots)",
    )

    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging (DEBUG level)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Count records without inserting into database",
    )

    return parser.parse_args()


# ============================================================================
# MAIN EXECUTION
# ============================================================================


def main() -> int:
    """Main ETL execution entry point.

    Returns:
        Exit code (0 for success, 1 for errors)
    """
    # Parse arguments and setup logging
    args = parse_args()
    setup_logging(args.verbose)

    logger = logging.getLogger(__name__)

    # Validate source directory exists
    if not args.source.exists():
        logger.error(f"Source directory not found: {args.source}")
        return 1

    try:
        # Initialize database
        logger.info(f"Using database: {args.db}")
        db = DatabaseManager(args.db)
        db.connect()
        db.setup_schema()

        # Initialize state tracker
        state = StateTracker(db, force=args.force)

        # Define all available extractors
        all_extractors = [
            ("projects", ProjectsExtractor(db, state, args.source)),
            ("todos", TodosExtractor(db, state, args.source)),
            ("file-history", FileHistoryExtractor(db, state, args.source)),
            ("history", HistoryLogExtractor(db, state, args.source)),
            ("plans", PlansExtractor(db, state, args.source)),
            ("shell-snapshots", ShellSnapshotsExtractor(db, state, args.source)),
        ]

        # Filter extractors based on --sources argument
        if args.sources:
            requested = set(s.strip() for s in args.sources.split(","))
            extractors = [
                (name, ext) for name, ext in all_extractors if name in requested
            ]
            if len(extractors) != len(requested):
                found = {name for name, _ in extractors}
                missing = requested - found
                logger.warning(f"Unknown sources requested: {missing}")
        else:
            extractors = all_extractors

        # Track aggregate statistics
        total_files = 0
        total_records = 0
        total_errors = 0

        # Process each extractor
        for source_name, extractor in extractors:
            # Print separator and header
            logger.info("=" * 60)
            logger.info(f"Processing: {source_name}")

            # Extract data
            result = extractor.extract(dry_run=args.dry_run)

            # Log result with emoji
            logger.info(
                f"✅ {source_name}: {result.files_processed} files, "
                f"{result.records_inserted} records, "
                f"{result.errors_count} errors ({result.duration:.1f}s)"
            )

            # Accumulate totals
            total_files += result.files_processed
            total_records += result.records_inserted
            total_errors += result.errors_count

            # Log extraction to state tracker
            status = "success" if result.errors_count == 0 else "partial"
            state.log_run(
                source_name,
                result.files_processed,
                result.records_inserted,
                result.errors_count,
                result.duration,
                status,
            )

        # Print final summary
        logger.info("=" * 60)
        logger.info("ETL SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Files processed:  {total_files}")
        logger.info(f"Records inserted: {total_records}")
        logger.info(f"Errors:           {total_errors}")
        logger.info("=" * 60)

        # Close database
        db.close()

        # Determine exit code
        exit_code = 0 if total_errors == 0 else 1

        if args.dry_run:
            logger.info("(Dry run - no data committed)")

        return exit_code

    except Exception as e:
        logger.exception(f"ETL failed with error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
