# Changelog

All notable changes to this project are documented here. The format follows Keep a Changelog, and the project adheres to Semantic Versioning.

## [Unreleased]

* No entries yet.

## [1.3.0] - 2025-12-02

### Added

* Implemented `_extract_tool_results()` with support for both string and array payloads plus preview truncation.

### Changed

* FileHistoryExtractor now traverses session directories, passes session identifiers through `_process_version_file()`, and encodes the session in file IDs.
* TodosExtractor schema updates: nullable `agent_id`, new `ref_session_id`, and removal of the premature `parent_session_id` foreign key.
* PlansExtractor now queries agents by `session_id`, tolerates missing agents, and records sidechain metadata consistently.

### Fixed

* Non-UUID message types (`file-history-snapshot`, `summary`, `queue-operation`) now log-and-skip instead of attempting inserts.
* TodosExtractor and PlansExtractor handle agent lookups without triggering constraint errors.

## [1.2.0] - 2025-12-02

### Changed

* Added complete mypy type coverage across `etl_extractors.py`, `etl_database.py`, and `etl_state.py`, including forward references via `TYPE_CHECKING`.
* Introduced explicit connection asserts before every SQLite execution path.

### Fixed

* Guarded `execute_batch()` and `query_one()` against `None` connections and annotated `cursor.fetchone()` return handling to satisfy type checking.

## [1.1.1] - 2025-12-02

### Fixed

* TodosExtractor and PlansExtractor now confirm agent existence before inserts, logging skipped files instead of raising foreign key violations.

## [1.1.0] - 2025-12-02

### Changed

* ProjectsExtractor rewritten to consume flat `.jsonl` files (`{session_id}.jsonl`, `agent-{id}.jsonl`) via a new `_process_jsonl_file()` helper.
* TodosExtractor filename parsing now treats the second component as an agent `session_id`, resolving the canonical agent ID through a database lookup.

### Fixed

* Todos referencing non-existent agents are skipped safely without aborting the ETL run.

## [1.0.0] - 2025-12-02

### Added

* Introduced the full SQLite schema with UUID primary keys, supporting tables, and indexes.
* Implemented database manager utilities (WAL mode, foreign key enforcement, transactional batching).
* Added incremental state tracking for per-file `mtime`/`size`, force mode, and run statistics.
* Built six dedicated extractors (Projects, Todos, File History, Shell Snapshots, History Log, Plans) with streaming parsing, tqdm progress, and dry-run support.
* Created the CLI entry point (`bin/etl.py`) for orchestration, logging, source filtering, and summary reporting.

### Fixed

* Validated end-to-end execution via manual tests covering CLI help, dry-run, force mode, source filtering, data insertion, and incremental skipping logic.
