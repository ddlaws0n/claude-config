"""Data extractors for ETL system - 6 data sources."""

import hashlib
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Iterator, List, Optional

from tqdm import tqdm

if TYPE_CHECKING:
    from etl_database import DatabaseManager
    from etl_state import StateTracker

logger = logging.getLogger(__name__)


# ============================================================================
# SUPPORTING INFRASTRUCTURE
# ============================================================================


@dataclass
class ExtractionResult:
    """Result of an extraction operation."""

    files_processed: int
    records_inserted: int
    errors_count: int
    duration: float


class BaseExtractor(ABC):
    """Abstract base class for all data extractors."""

    SOURCE_NAME = "base"

    def __init__(self, db: "DatabaseManager", state: "StateTracker", source_dir: Path):
        """Initialize extractor with database, state tracker, and source directory.

        Args:
            db: DatabaseManager instance
            state: StateTracker instance
            source_dir: Root directory where Claude Code stores session data
        """
        self.db = db
        self.state = state
        self.source_dir = source_dir

    @abstractmethod
    def extract(self, dry_run: bool = False) -> ExtractionResult:
        """Extract data from source.

        Args:
            dry_run: If True, count records without inserting

        Returns:
            ExtractionResult with counts and duration
        """
        pass

    def should_process_file(self, file_path: Path) -> bool:
        """Check if file should be processed based on state.

        Uses hybrid incremental strategy:
        - If --force: always True
        - If new file: True
        - If modified (mtime or size changed): True
        - Otherwise: False
        """
        return self.state.should_process_file(self.SOURCE_NAME, file_path)


# ============================================================================
# PROJECTS EXTRACTOR (lines 612-896)
# ============================================================================


class ProjectsExtractor(BaseExtractor):
    """Extract project sessions, agents, messages, and tool usage from projects/ directory.

    File structure (actual):
    - projects/{encoded_path}/{session_id}.jsonl
    - projects/{encoded_path}/agent-{agent_id}.jsonl

    The encoded_path decodes from format like:
    - -Users-dlawson-repos-foo → /Users/dlawson/repos/foo
    """

    SOURCE_NAME = "projects"

    def extract(self, dry_run: bool = False) -> ExtractionResult:
        """Extract all project data."""
        start_time = datetime.now()
        files_processed = 0
        records_inserted = 0
        errors_count = 0

        projects_dir = self.source_dir / "projects"
        if not projects_dir.exists():
            logger.info(f"Projects directory not found: {projects_dir}")
            return ExtractionResult(0, 0, 0, 0)

        # Find all project directories
        project_dirs = list(projects_dir.iterdir())
        logger.info(f"Found {len(project_dirs)} projects")

        # Process each project
        for project_dir in tqdm(project_dirs, desc="Projects"):
            try:
                if not project_dir.is_dir():
                    continue

                # Decode project path
                project_path = self._decode_project_path(project_dir.name)

                # Ensure project exists in database
                with self.db.transaction():
                    assert self.db.conn is not None
                    self.db.conn.execute(
                        """
                        INSERT OR IGNORE INTO projects
                        (path, name, first_seen, last_seen)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            str(project_path),
                            project_dir.name,
                            datetime.now().isoformat(),
                            datetime.now().isoformat(),
                        ),
                    )

                # Find all JSONL files directly in project directory
                jsonl_files = list(project_dir.glob("*.jsonl"))

                for jsonl_file in jsonl_files:
                    if not self.should_process_file(jsonl_file):
                        continue

                    try:
                        result = self._process_jsonl_file(
                            project_path, jsonl_file, dry_run
                        )
                        records_inserted += result
                        files_processed += 1
                        self.state.mark_processed(self.SOURCE_NAME, jsonl_file)
                    except Exception as e:
                        logger.error(f"Error processing {jsonl_file.name}: {e}")
                        errors_count += 1
                        continue

            except Exception as e:
                logger.error(f"Error processing project {project_dir.name}: {e}")
                errors_count += 1
                continue

        duration = (datetime.now() - start_time).total_seconds()
        self.state.log_run(
            self.SOURCE_NAME,
            files_processed,
            records_inserted,
            errors_count,
            duration,
            "success" if errors_count == 0 else "partial",
        )

        return ExtractionResult(files_processed, records_inserted, errors_count, duration)

    def _decode_project_path(self, encoded: str) -> Path:
        """Decode project path from encoded format.

        Example: -Users-dlawson-repos-foo → /Users/dlawson/repos/foo
        """
        # Remove leading dash and replace dashes with slashes
        parts = encoded.split("-")

        # First part is empty due to leading dash, skip it
        if parts and parts[0] == "":
            parts = parts[1:]

        return Path("/".join(parts))

    def _process_jsonl_file(
        self, project_path: Path, jsonl_file: Path, dry_run: bool
    ) -> int:
        """Process a JSONL file (either session or agent file).

        Filename patterns:
        - {session_id}.jsonl: Main session file
        - agent-{agent_id}.jsonl: Agent/sidechain file

        Returns number of records inserted.
        """
        filename = jsonl_file.name

        # Read first message to get session_id and metadata
        first_msg = None
        for msg in self._stream_jsonl(jsonl_file):
            first_msg = msg
            break

        if not first_msg:
            logger.debug(f"Empty file: {jsonl_file.name}")
            return 0

        # Determine session_id: from message or from filename
        session_id = first_msg.get("sessionId")
        if not session_id:
            # Try to extract from filename (for session files: {uuid}.jsonl)
            if filename.endswith(".jsonl") and not filename.startswith("agent-"):
                session_id = filename[:-6]  # Remove .jsonl extension
            else:
                logger.warning(f"No sessionId in {jsonl_file.name}")
                return 0

        # Extract session metadata from first message
        cwd = first_msg.get("cwd")
        git_branch = first_msg.get("gitBranch")
        version = first_msg.get("version")

        # Ensure session exists in database
        if not dry_run:
            with self.db.transaction():
                assert self.db.conn is not None
                self.db.conn.execute(
                    """
                    INSERT OR IGNORE INTO sessions
                    (id, project_path, cwd, git_branch, version, started_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        str(project_path),
                        cwd,
                        git_branch,
                        version,
                        first_msg.get("timestamp", datetime.now().isoformat()),
                    ),
                )

        # Now process all messages
        return self._process_session(project_path, session_id, jsonl_file, dry_run)

    def _stream_jsonl(self, file_path: Path) -> Iterator[Dict]:
        """Stream JSONL file line by line for memory efficiency."""
        try:
            with open(file_path, "r") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError as e:
                        logger.warning(
                            f"Invalid JSON at line {line_num} in {file_path}: {e}"
                        )
                        continue
        except Exception as e:
            logger.error(f"Error reading JSONL file {file_path}: {e}")

    def _transform_message(self, content) -> str:
        """Normalize message content to string format.

        Content can be a string or array of objects with text field.
        """
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict):
                    if "text" in item:
                        parts.append(item["text"])
                elif isinstance(item, str):
                    parts.append(item)
            return "\n".join(parts)

        return str(content)

    def _extract_tools(self, content) -> List[Dict]:
        """Extract tool_use blocks from message content.

        Returns list of tool use objects.
        """
        tools = []

        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "tool_use":
                    tools.append(item)

        return tools

    def _extract_tool_results(self, content) -> List[Dict]:
        """Extract tool_result blocks from message content.

        Returns list of tool result objects.
        """
        results = []

        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "tool_result":
                    results.append(item)

        return results

    def _process_session(
        self, project_path: Path, session_id: str, messages_file: Path, dry_run: bool
    ) -> int:
        """Process all messages in a session file.

        Returns number of records inserted.
        """
        records_inserted = 0

        # Stream messages
        messages = []
        agents = {}  # Map agent_id -> (is_sidechain, parent_uuid)
        tool_uses = []
        tool_results: list[dict] = []

        for msg_data in self._stream_jsonl(messages_file):
            try:
                # Extract message fields
                uuid = msg_data.get("uuid", "")
                msg_type = msg_data.get("type", "")

                # Skip messages without UUID (file-history-snapshot, summary, queue-operation)
                # These are metadata/system messages that don't fit the message model
                if not uuid:
                    # Log these for visibility but don't process
                    if msg_type in ("file-history-snapshot", "summary", "queue-operation"):
                        logger.debug(f"Skipping {msg_type} message (no UUID)")
                    continue

                parent_uuid = msg_data.get("parentUuid")
                timestamp = msg_data.get("timestamp", datetime.now().isoformat())

                # Handle different message formats
                role = msg_data.get("role")
                if not role and "message" in msg_data:
                    # Format: {"message": {"role": "...", "content": "..."}}
                    inner_msg = msg_data.get("message", {})
                    role = inner_msg.get("role")
                    content = inner_msg.get("content")
                else:
                    content = msg_data.get("content")

                content_text = self._transform_message(content) if content else None

                # Extract agent ID and sidechain info
                agent_id = msg_data.get("agentId")
                if agent_id and agent_id not in agents:
                    is_sidechain = msg_data.get("isSidechain", False)
                    agents[agent_id] = (is_sidechain, parent_uuid)

                # Extract token usage
                usage = msg_data.get("usage", {})
                input_tokens = usage.get("input_tokens")
                output_tokens = usage.get("output_tokens")
                cache_creation_tokens = usage.get("cache_creation_tokens")
                cache_read_tokens = usage.get("cache_read_tokens")

                # Extract assistant-specific fields
                model = msg_data.get("model")
                message_id = msg_data.get("message_id")
                stop_reason = msg_data.get("stop_reason")

                messages.append(
                    (
                        uuid,
                        parent_uuid,
                        session_id,
                        agent_id,
                        timestamp,
                        msg_type,
                        role,
                        content_text,
                        None,
                        model,
                        message_id,
                        stop_reason,
                        input_tokens,
                        output_tokens,
                        cache_creation_tokens,
                        cache_read_tokens,
                    )
                )

                # Extract tool uses from content
                if content:
                    for tool_data in self._extract_tools(content):
                        tool_id = tool_data.get("id", "")
                        tool_name = tool_data.get("name", "")
                        tool_input = tool_data.get("input", {})

                        tool_uses.append(
                            (uuid, tool_id, tool_name, json.dumps(tool_input))
                        )

                    # Extract tool results from content
                    for result_data in self._extract_tool_results(content):
                        tool_use_id = result_data.get("tool_use_id", "")
                        is_error = result_data.get("is_error", False)
                        result_content = result_data.get("content", "")

                        # Create preview from content
                        if isinstance(result_content, str):
                            preview = result_content[:500]
                        elif isinstance(result_content, list):
                            # Content is array of text blocks
                            preview = json.dumps(result_content)[:500]
                        else:
                            preview = str(result_content)[:500]

                        tool_results.append(
                            (uuid, tool_use_id, is_error, preview)
                        )

            except Exception as e:
                logger.warning(f"Error processing message in {messages_file}: {e}")
                continue

        # Insert agents
        if agents and not dry_run:
            agent_records = [
                (agent_id, session_id, is_sidechain, parent_uuid, datetime.now().isoformat())
                for agent_id, (is_sidechain, parent_uuid) in agents.items()
            ]
            inserted = self.db.execute_batch(
                """
                INSERT OR IGNORE INTO agents
                (id, session_id, is_sidechain, parent_message_uuid, first_seen)
                VALUES (?, ?, ?, ?, ?)
                """,
                agent_records,
            )
            records_inserted += inserted
        elif agents:
            records_inserted += len(agents)

        # Insert messages
        if messages and not dry_run:
            inserted = self.db.execute_batch(
                """
                INSERT OR IGNORE INTO messages
                (uuid, parent_uuid, session_id, agent_id, timestamp, type,
                 role, content_text, content_json, model, message_id, stop_reason,
                 input_tokens, output_tokens, cache_creation_tokens, cache_read_tokens)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                messages,
            )
            records_inserted += inserted
        else:
            records_inserted += len(messages)

        # Insert tool uses
        if tool_uses and not dry_run:
            inserted = self.db.execute_batch(
                """
                INSERT INTO tool_uses
                (message_uuid, tool_id, tool_name, input_json)
                VALUES (?, ?, ?, ?)
                """,
                tool_uses,
            )
            records_inserted += inserted
        else:
            records_inserted += len(tool_uses)

        # Insert tool results
        if tool_results and not dry_run:
            inserted = self.db.execute_batch(
                """
                INSERT INTO tool_results
                (message_uuid, tool_use_id, is_error, content_preview)
                VALUES (?, ?, ?, ?)
                """,
                tool_results,
            )
            records_inserted += inserted
        else:
            records_inserted += len(tool_results)

        return records_inserted


# ============================================================================
# TODOS EXTRACTOR (lines 898-977)
# ============================================================================


class TodosExtractor(BaseExtractor):
    """Extract todos from todos/ directory.

    File format: {parent_session_id}-agent-{ref_session_id}.json
    Generates todo_id: {parent_session_id}-{ref_session_id}-{idx}

    The ref_session_id can be:
    - Same as parent_session_id (main session todos)
    - Different UUID (subagent/sidechain todos)
    """

    SOURCE_NAME = "todos"

    def extract(self, dry_run: bool = False) -> ExtractionResult:
        """Extract all todo records."""
        start_time = datetime.now()
        files_processed = 0
        records_inserted = 0
        errors_count = 0

        todos_dir = self.source_dir / "todos"
        if not todos_dir.exists():
            logger.info(f"Todos directory not found: {todos_dir}")
            return ExtractionResult(0, 0, 0, 0)

        # Find all todo files
        todo_files = sorted(todos_dir.glob("*.json"))
        logger.info(f"Found {len(todo_files)} todo files")

        for todo_file in tqdm(todo_files, desc="Todos"):
            try:
                if not self.should_process_file(todo_file):
                    continue

                result = self._process_todo_file(todo_file, dry_run)
                records_inserted += result
                files_processed += 1
                self.state.mark_processed(self.SOURCE_NAME, todo_file)

            except Exception as e:
                logger.error(f"Error processing todo file {todo_file.name}: {e}")
                errors_count += 1
                continue

        duration = (datetime.now() - start_time).total_seconds()
        self.state.log_run(
            self.SOURCE_NAME,
            files_processed,
            records_inserted,
            errors_count,
            duration,
            "success" if errors_count == 0 else "partial",
        )

        return ExtractionResult(files_processed, records_inserted, errors_count, duration)

    def _parse_todo_filename(self, filename: str) -> tuple:
        """Parse filename to extract parent and reference session IDs.

        Format: {parent_session_id}-agent-{ref_session_id}.json
        Returns: (parent_session_id, ref_session_id)
        """
        # Remove .json extension
        name = filename[:-5] if filename.endswith(".json") else filename

        # Split on "-agent-"
        parts = name.split("-agent-")
        if len(parts) == 2:
            return parts[0], parts[1]

        return name, ""

    def _process_todo_file(self, todo_file: Path, dry_run: bool) -> int:
        """Process a single todo JSON file.

        Filename format: {parent_session_id}-agent-{ref_session_id}.json

        The ref_session_id can be:
        - Same as parent (main session todos)
        - Different UUID (subagent todos)

        Returns number of records inserted.
        """
        try:
            with open(todo_file, "r") as f:
                todos_data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {todo_file.name}: {e}")
            return 0

        parent_session_id, ref_session_id = self._parse_todo_filename(todo_file.name)

        if not isinstance(todos_data, list):
            logger.warning(f"Todo file {todo_file.name} does not contain a list")
            return 0

        # Try to find agent by ref_session_id (optional - agent may not exist yet)
        agent_id = None
        if ref_session_id and not dry_run:
            # Try to find agent where this ref_session_id is the agent's session
            agent_record = self.db.query_one(
                "SELECT id FROM agents WHERE session_id = ?", (ref_session_id,)
            )
            if agent_record:
                agent_id = agent_record[0]
            # If not found, that's OK - agent_id will be NULL

        records = []
        for idx, todo_data in enumerate(todos_data):
            try:
                todo_id = f"{parent_session_id}-{ref_session_id}-{idx}"
                content = todo_data.get("content", "")
                active_form = todo_data.get("activeForm", "")
                status = todo_data.get("status", "pending")

                records.append(
                    (
                        todo_id,
                        parent_session_id,
                        ref_session_id,
                        agent_id,
                        idx,
                        content,
                        active_form,
                        status,
                    )
                )
            except Exception as e:
                logger.warning(
                    f"Error processing todo at index {idx} in {todo_file.name}: {e}"
                )
                continue

        if not records:
            return 0

        if dry_run:
            return len(records)

        inserted = self.db.execute_batch(
            """
            INSERT OR IGNORE INTO todos
            (id, parent_session_id, ref_session_id, agent_id, sequence, content, active_form, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            records,
        )

        return inserted


# ============================================================================
# FILE HISTORY EXTRACTOR (lines 979-1046)
# ============================================================================


class FileHistoryExtractor(BaseExtractor):
    """Extract file version history from file-history/ directory.

    File format: {hash}@v{version}
    Generates file_id: {session_id}/{name}
    """

    SOURCE_NAME = "file-history"

    def extract(self, dry_run: bool = False) -> ExtractionResult:
        """Extract all file version records."""
        start_time = datetime.now()
        files_processed = 0
        records_inserted = 0
        errors_count = 0

        history_dir = self.source_dir / "file-history"
        if not history_dir.exists():
            logger.info(f"File history directory not found: {history_dir}")
            return ExtractionResult(0, 0, 0, 0)

        # Find all session directories
        session_dirs = [d for d in history_dir.iterdir() if d.is_dir()]
        logger.info(f"Found {len(session_dirs)} session directories in file-history")

        # Process each session directory
        for session_dir in tqdm(session_dirs, desc="File History Sessions"):
            try:
                session_id = session_dir.name

                # Find all version files in this session directory
                version_files = sorted(session_dir.glob("*"))

                for version_file in version_files:
                    try:
                        if not version_file.is_file():
                            continue

                        if not self.should_process_file(version_file):
                            continue

                        result = self._process_version_file(
                            session_id, version_file, dry_run
                        )
                        records_inserted += result
                        files_processed += 1
                        self.state.mark_processed(self.SOURCE_NAME, version_file)

                    except Exception as e:
                        logger.error(
                            f"Error processing file version {version_file.name}: {e}"
                        )
                        errors_count += 1
                        continue

            except Exception as e:
                logger.error(f"Error processing session directory {session_dir.name}: {e}")
                errors_count += 1
                continue

        duration = (datetime.now() - start_time).total_seconds()
        self.state.log_run(
            self.SOURCE_NAME,
            files_processed,
            records_inserted,
            errors_count,
            duration,
            "success" if errors_count == 0 else "partial",
        )

        return ExtractionResult(files_processed, records_inserted, errors_count, duration)

    def _parse_version_filename(self, filename: str) -> tuple:
        """Parse filename to extract hash and version.

        Format: {hash}@v{version}
        Returns: (hash, version)
        """
        if "@v" in filename:
            parts = filename.split("@v")
            if len(parts) == 2:
                try:
                    return parts[0], int(parts[1])
                except ValueError:
                    pass

        return filename, 0

    def _process_version_file(
        self, session_id: str, version_file: Path, dry_run: bool
    ) -> int:
        """Process a single file version.

        Args:
            session_id: Session UUID from parent directory
            version_file: Path to version file
            dry_run: If True, count without inserting

        Returns number of records inserted.
        """
        try:
            content = version_file.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            logger.error(f"Error reading file version {version_file.name}: {e}")
            return 0

        file_hash, version = self._parse_version_filename(version_file.name)

        # Use session_id from directory structure
        file_id = f"{session_id}/{file_hash}@v{version}"

        file_size = len(content.encode("utf-8"))

        if dry_run:
            return 1

        try:
            with self.db.transaction():
                assert self.db.conn is not None
                self.db.conn.execute(
                    """
                    INSERT OR IGNORE INTO file_versions
                    (id, session_id, file_hash, version, content, file_size)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (file_id, session_id, file_hash, version, content, file_size),
                )
            return 1
        except Exception as e:
            logger.error(f"Error inserting file version {version_file.name}: {e}")
            return 0


# ============================================================================
# SHELL SNAPSHOTS EXTRACTOR (lines 1048-1106)
# ============================================================================


class ShellSnapshotsExtractor(BaseExtractor):
    """Extract shell snapshots from shell-snapshots/ directory.

    File format: snapshot-zsh-{timestamp_ms}-{random_id}.sh
    Converts timestamp from milliseconds to datetime.
    """

    SOURCE_NAME = "shell-snapshots"

    def extract(self, dry_run: bool = False) -> ExtractionResult:
        """Extract all shell snapshot records."""
        start_time = datetime.now()
        files_processed = 0
        records_inserted = 0
        errors_count = 0

        snapshots_dir = self.source_dir / "shell-snapshots"
        if not snapshots_dir.exists():
            logger.info(f"Shell snapshots directory not found: {snapshots_dir}")
            return ExtractionResult(0, 0, 0, 0)

        # Find all snapshot files
        snapshot_files = sorted(snapshots_dir.glob("snapshot-*.sh"))
        logger.info(f"Found {len(snapshot_files)} shell snapshots")

        for snapshot_file in tqdm(snapshot_files, desc="Shell Snapshots"):
            try:
                if not self.should_process_file(snapshot_file):
                    continue

                result = self._process_snapshot(snapshot_file, dry_run)
                if result > 0:
                    records_inserted += result
                    files_processed += 1
                    self.state.mark_processed(self.SOURCE_NAME, snapshot_file)

            except Exception as e:
                logger.error(f"Error processing snapshot {snapshot_file.name}: {e}")
                errors_count += 1
                continue

        duration = (datetime.now() - start_time).total_seconds()
        self.state.log_run(
            self.SOURCE_NAME,
            files_processed,
            records_inserted,
            errors_count,
            duration,
            "success" if errors_count == 0 else "partial",
        )

        return ExtractionResult(files_processed, records_inserted, errors_count, duration)

    def _parse_snapshot_filename(self, filename: str) -> tuple:
        """Parse snapshot filename to extract shell type and timestamp.

        Format: snapshot-{shell_type}-{timestamp_ms}-{random_id}.sh
        Returns: (shell_type, timestamp_ms)
        """
        # Remove .sh extension and 'snapshot-' prefix
        name = filename[:-3] if filename.endswith(".sh") else filename
        if name.startswith("snapshot-"):
            name = name[9:]

        # Split by '-' and extract parts
        parts = name.split("-")
        if len(parts) >= 2:
            shell_type = parts[0]
            try:
                timestamp_ms = int(parts[1])
                return shell_type, timestamp_ms
            except ValueError:
                pass

        return "unknown", 0

    def _process_snapshot(self, snapshot_file: Path, dry_run: bool) -> int:
        """Process a single shell snapshot file.

        Returns number of records inserted.
        """
        try:
            content = snapshot_file.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            logger.error(f"Error reading snapshot {snapshot_file.name}: {e}")
            return 0

        shell_type, timestamp_ms = self._parse_snapshot_filename(snapshot_file.name)

        # Convert timestamp from milliseconds to datetime
        if timestamp_ms > 0:
            try:
                timestamp = datetime.fromtimestamp(timestamp_ms / 1000.0)
            except (ValueError, OSError):
                timestamp = datetime.now()
        else:
            timestamp = datetime.now()

        # Generate snapshot ID from filename
        snapshot_id = snapshot_file.name[:-3]  # Remove .sh

        # Compute content hash
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        if dry_run:
            return 1

        try:
            with self.db.transaction():
                assert self.db.conn is not None
                self.db.conn.execute(
                    """
                    INSERT OR IGNORE INTO shell_snapshots
                    (id, timestamp, shell_type, content, content_hash)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        snapshot_id,
                        timestamp.isoformat(),
                        shell_type,
                        content,
                        content_hash,
                    ),
                )
            return 1
        except Exception as e:
            logger.error(f"Error inserting snapshot {snapshot_file.name}: {e}")
            return 0


# ============================================================================
# HISTORY LOG EXTRACTOR (lines 1108-1166)
# ============================================================================


class HistoryLogExtractor(BaseExtractor):
    """Extract history log from history.jsonl file."""

    SOURCE_NAME = "history"

    def extract(self, dry_run: bool = False) -> ExtractionResult:
        """Extract all history log records."""
        start_time = datetime.now()
        files_processed = 0
        records_inserted = 0
        errors_count = 0

        history_file = self.source_dir / "history.jsonl"
        if not history_file.exists():
            logger.info(f"History file not found: {history_file}")
            return ExtractionResult(0, 0, 0, 0)

        if not self.should_process_file(history_file):
            logger.info("History file not modified since last run")
            return ExtractionResult(0, 0, 0, 0)

        try:
            records = self._process_history_file(history_file, dry_run)
            records_inserted += records
            files_processed = 1
            self.state.mark_processed(self.SOURCE_NAME, history_file)
        except Exception as e:
            logger.error(f"Error processing history file: {e}")
            errors_count = 1

        duration = (datetime.now() - start_time).total_seconds()
        self.state.log_run(
            self.SOURCE_NAME,
            files_processed,
            records_inserted,
            errors_count,
            duration,
            "success" if errors_count == 0 else "partial",
        )

        return ExtractionResult(files_processed, records_inserted, errors_count, duration)

    def _stream_jsonl(self, file_path: Path) -> Iterator[Dict]:
        """Stream JSONL file line by line for memory efficiency."""
        try:
            with open(file_path, "r") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Invalid JSON at line {line_num}: {e}")
                        continue
        except Exception as e:
            logger.error(f"Error reading JSONL file {file_path}: {e}")

    def _process_history_file(self, history_file: Path, dry_run: bool) -> int:
        """Process history JSONL file.

        Returns number of records inserted.
        """
        records = []

        for entry in self._stream_jsonl(history_file):
            try:
                timestamp = entry.get("timestamp", datetime.now().isoformat())
                project_path = entry.get("project_path")
                display = entry.get("display", "")

                records.append((timestamp, project_path, display))
            except Exception as e:
                logger.warning(f"Error processing history entry: {e}")
                continue

        if not records:
            return 0

        if dry_run:
            return len(records)

        inserted = self.db.execute_batch(
            """
            INSERT INTO history_log
            (timestamp, project_path, display)
            VALUES (?, ?, ?)
            """,
            records,
        )

        return inserted


# ============================================================================
# PLANS EXTRACTOR (lines 1168-1237)
# ============================================================================


class PlansExtractor(BaseExtractor):
    """Extract plans from plans/ directory.

    File format: *.md
    Extracts agent_id from filename suffix: -{uuid}
    Extracts title from first '# ' heading.
    """

    SOURCE_NAME = "plans"

    def extract(self, dry_run: bool = False) -> ExtractionResult:
        """Extract all plan records."""
        start_time = datetime.now()
        files_processed = 0
        records_inserted = 0
        errors_count = 0

        plans_dir = self.source_dir / "plans"
        if not plans_dir.exists():
            logger.info(f"Plans directory not found: {plans_dir}")
            return ExtractionResult(0, 0, 0, 0)

        # Find all plan files
        plan_files = sorted(plans_dir.glob("*.md"))
        logger.info(f"Found {len(plan_files)} plan files")

        for plan_file in tqdm(plan_files, desc="Plans"):
            try:
                if not self.should_process_file(plan_file):
                    continue

                result = self._process_plan(plan_file, dry_run)
                if result > 0:
                    records_inserted += result
                    files_processed += 1
                    self.state.mark_processed(self.SOURCE_NAME, plan_file)

            except Exception as e:
                logger.error(f"Error processing plan {plan_file.name}: {e}")
                errors_count += 1
                continue

        duration = (datetime.now() - start_time).total_seconds()
        self.state.log_run(
            self.SOURCE_NAME,
            files_processed,
            records_inserted,
            errors_count,
            duration,
            "success" if errors_count == 0 else "partial",
        )

        return ExtractionResult(files_processed, records_inserted, errors_count, duration)

    def _extract_agent_id(self, filename: str) -> Optional[str]:
        """Extract agent_id from filename suffix.

        Format: {name}-agent-{uuid}.md
        Returns: agent_id (uuid) or None
        """
        # Remove .md extension
        name = filename[:-3] if filename.endswith(".md") else filename

        if "-agent-" in name:
            parts = name.split("-agent-")
            if len(parts) == 2:
                return parts[1]

        return None

    def _extract_title(self, content: str) -> Optional[str]:
        """Extract title from first '# ' heading in content.

        Returns: Title text or None
        """
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()

        return None

    def _process_plan(self, plan_file: Path, dry_run: bool) -> int:
        """Process a single plan file.

        Returns number of records inserted.
        """
        try:
            content = plan_file.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Error reading plan {plan_file.name}: {e}")
            return 0

        ref_id = self._extract_agent_id(plan_file.name)
        title = self._extract_title(content)

        # Try to find agent by session_id (ref_id is a UUID from filename)
        # If found, use the agent's 8-char hex ID; otherwise, allow NULL
        agent_id = None
        if ref_id and not dry_run:
            # ref_id from filename is a session UUID
            # Try to find agent where session_id matches
            agent_record = self.db.query_one(
                "SELECT id FROM agents WHERE session_id = ?", (ref_id,)
            )
            if agent_record:
                agent_id = agent_record[0]
            # If not found, that's OK - agent_id will be NULL

        # Get file timestamps
        stat = plan_file.stat()
        created_at = datetime.fromtimestamp(stat.st_ctime).isoformat()
        modified_at = datetime.fromtimestamp(stat.st_mtime).isoformat()

        if dry_run:
            return 1

        try:
            with self.db.transaction():
                assert self.db.conn is not None
                self.db.conn.execute(
                    """
                    INSERT OR REPLACE INTO plans
                    (filename, agent_id, title, content, created_at, modified_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (plan_file.name, agent_id, title, content, created_at, modified_at),
                )
            return 1
        except Exception as e:
            logger.error(f"Error inserting plan {plan_file.name}: {e}")
            return 0
