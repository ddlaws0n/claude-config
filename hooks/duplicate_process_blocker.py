#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""
Duplicate Process Blocker Hook for Claude Code

Prevents duplicate development server processes from running simultaneously
using PID-based atomic file locking with stale lock cleanup.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

# Configuration
DEFAULT_TIMEOUT_MINUTES = 5
LOCK_FILE_PREFIX = "claude-dev-server-"

# Optimized patterns: consolidated npm/yarn/pnpm variants to reduce regex engine overhead
DEFAULT_PATTERNS = [
    # Node: npm/yarn/pnpm/bun/deno/just (run) dev/start
    r"(?:npm|pnpm|yarn|bun|deno|just)\s+(?:run\s+)?(?:dev|start)\b",
    # Common Frameworks
    r"next\s+dev\b",
    r"vite\b",
    r"webpack-dev-server\b",
    # Python - Django
    r"(?:uv\s+run\s+)?(?:python3?)\s+.*manage\.py\s+runserver\b",
    r"(?:uv\s+run\s+)?django-admin\s+runserver\b",
    # Python - Flask
    r"(?:uv\s+run\s+)?(?:python3?)\s+.*(?:flask|app\.py)\s+run\b",
    r"(?:uv\s+run\s+)?flask\s+run\b",
    # Python - Generic dev servers
    r"(?:uv\s+run\s+)?(?:python3?)\s+-m\s+(?:flask|django|uvicorn|gunicorn)\b",
    r"uvicorn\s+.*--reload\b",
    r"(?:python3?)\s+-m\s+http\.server\b",
    # Ruby/Rails
    r"(?:bundle\s+exec\s+)?rails\s+(?:server|s)\b",
    # PHP
    r"php\s+artisan\s+serve\b",
    r"php\s+-S\s+",
]


@dataclass
class LockData:
    pid: int
    timestamp: float
    command_hash: str
    session_id: str
    command: str
    port: int | None = None

    @property
    def is_running(self) -> bool:
        """Check if the process specific to this lock is actually running."""
        if self.pid <= 0:
            return False
        try:
            # Signal 0 checks if process exists without killing it
            os.kill(self.pid, 0)
            return True
        except (ProcessLookupError, PermissionError):
            return False

    @property
    def age_minutes(self) -> float:
        return (time.time() - self.timestamp) / 60


class ProcessBlocker:
    """Manages atomic locks for development server processes."""

    def __init__(self) -> None:
        self.enabled = self._get_env_bool("CLAUDE_DEV_SERVER_BLOCKER_ENABLED", True)
        self.timeout = int(
            os.environ.get("CLAUDE_DEV_SERVER_TIMEOUT", DEFAULT_TIMEOUT_MINUTES)
        )
        self.lock_dir = Path(os.environ.get("CLAUDE_DEV_SERVER_LOCK_DIR", "/tmp"))

        # Lazy load patterns only if enabled
        if self.enabled:
            self.patterns = self._load_patterns()
            self._regex_cache = [re.compile(p, re.IGNORECASE) for p in self.patterns]

    def _get_env_bool(self, key: str, default: bool) -> bool:
        val = os.environ.get(key, str(default)).lower()
        return val in ("1", "true", "yes", "on")

    def _load_patterns(self) -> list[str]:
        patterns = DEFAULT_PATTERNS.copy()
        if custom := os.environ.get("CLAUDE_DEV_SERVER_PATTERNS"):
            patterns.extend(custom.split(":"))
        return patterns

    def _get_hash(self, command: str) -> str:
        """Generate a consistent hash for a normalized command."""
        normalized = re.sub(r"\s+", " ", command.strip().lower())
        return hashlib.sha256(normalized.encode()).hexdigest()[:12]

    def _get_lock_path(self, cmd_hash: str) -> Path:
        return self.lock_dir / f"{LOCK_FILE_PREFIX}{cmd_hash}.lock"

    def _extract_port(self, command: str) -> int | None:
        """Extract port number from command if present."""
        # Common port patterns:
        # --port 3000, --port=3000, -p 3000, -p=3000
        # :3000, localhost:3000, 0.0.0.0:3000
        # runserver 3000, runserver 0.0.0.0:3000
        port_patterns = [
            r"(?:--port[=\s]+|:)(\d{2,5})\b",  # --port=3000, :3000
            r"(?:-p[=\s]+)(\d{2,5})\b",  # -p 3000
            r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{2,5})\b",  # 0.0.0.0:3000
            r"\brunserver\s+(?:\S+:)?(\d{2,5})\b",  # runserver 3000 or runserver 0.0.0.0:3000
        ]

        for pattern in port_patterns:
            if match := re.search(pattern, command):
                # Take the last captured group (handles both single and multi-group matches)
                port_str = match.group(match.lastindex or 1)
                try:
                    port = int(port_str)
                    if 1 <= port <= 65535:
                        return port
                except ValueError:
                    continue

        # Default ports for known frameworks
        defaults = {
            "next": 3000,
            "vite": 5173,
            "flask": 5000,
            "django": 8000,
            "rails": 3000,
            "php": 8000,
        }

        cmd_lower = command.lower()
        for framework, default_port in defaults.items():
            if framework in cmd_lower:
                return default_port

        return None

    def _read_lock(self, path: Path) -> LockData | None:
        """Read and parse lock file using JSON."""
        try:
            if not path.exists():
                return None
            data = json.loads(path.read_text(encoding="utf-8"))
            return LockData(**data)
        except (json.JSONDecodeError, OSError, TypeError):
            return None

    def _write_lock(self, path: Path, command: str, session_id: str) -> bool:
        """Atomically write lock file."""
        data = LockData(
            pid=os.getpid(),
            timestamp=time.time(),
            command_hash=self._get_hash(command),
            session_id=session_id,
            command=command,
            port=self._extract_port(command),
        )
        try:
            # Create lock file exclusively (fails if exists)
            with path.open("x", encoding="utf-8") as f:
                json.dump(asdict(data), f)
            return True
        except FileExistsError:
            return False
        except OSError:
            return False  # Fail open on permission errors

    def _cleanup_path(self, path: Path) -> bool:
        """Attempt to unlink a path, return True if successful."""
        try:
            path.unlink(missing_ok=True)
            return True
        except OSError:
            return False

    def _clean_stale_locks(self) -> int:
        """Iterate and clean all stale locks in the directory."""
        cleaned = 0
        if not self.lock_dir.exists():
            return 0

        for path in self.lock_dir.glob(f"{LOCK_FILE_PREFIX}*.lock"):
            lock = self._read_lock(path)
            # If lock is unreadable (corrupt) or logic deems it stale
            if not lock or (not lock.is_running or lock.age_minutes > self.timeout):
                if self._cleanup_path(path):
                    cleaned += 1
        return cleaned

    def should_process(self, command: str) -> bool:
        """Fast check if command matches any patterns."""
        if not self.enabled or not command:
            return False
        cmd_lower = command.lower()
        return any(p.search(cmd_lower) for p in self._regex_cache)

    def check_and_lock(self, command: str, session_id: str) -> tuple[bool, str]:
        """
        Main logic:
        1. If pattern matches, check lock.
        2. If lock exists but stale, remove it.
        3. Try to acquire lock.
        Returns (should_block, message).
        """
        if not self.should_process(command):
            return False, ""

        # Ensure lock directory exists
        self.lock_dir.mkdir(parents=True, exist_ok=True)

        # Note: Stale lock cleanup is handled by SessionStart hook (--cleanup flag)
        # to avoid I/O overhead on every Bash command

        lock_hash = self._get_hash(command)
        lock_path = self._get_lock_path(lock_hash)

        # 1. Try to acquire immediately
        if self._write_lock(lock_path, command, session_id):
            return False, self._fmt_success(command, lock_path)

        # 2. Lock failed, inspect existing lock
        existing_lock = self._read_lock(lock_path)

        # If file exists but is unreadable/corrupt, force claim it
        if not existing_lock:
            self._cleanup_path(lock_path)
            if self._write_lock(lock_path, command, session_id):
                return False, self._fmt_success(
                    command, lock_path, "corrupt lock replaced"
                )
            return False, ""  # Should not happen, but fail open

        # 3. Check staleness of valid lock
        if not existing_lock.is_running or existing_lock.age_minutes > self.timeout:
            self._cleanup_path(lock_path)
            if self._write_lock(lock_path, command, session_id):
                reason = "stale process" if not existing_lock.is_running else "timeout"
                return False, self._fmt_success(command, lock_path, f"{reason} cleaned")

        # 4. Valid lock exists -> BLOCK
        return True, self._fmt_block_msg(existing_lock)

    def _fmt_success(self, cmd: str, path: Path, note: str = "") -> str:
        msg = f"✓ Development server started: '{cmd}' (PID: {os.getpid()})\n"
        msg += f"   Lock acquired: {path}"
        if note:
            msg += f" ({note})"
        return msg

    def _fmt_block_msg(self, lock: LockData) -> str:
        dt = datetime.fromtimestamp(lock.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        msg = (
            f"🚫 Development server blocked: '{lock.command}' is already running\n"
            f"   PID: {lock.pid} | Started: {dt}\n"
            f"   Session: {lock.session_id}\n"
        )

        if lock.port:
            msg += f"   Port: {lock.port}\n"

        msg += "\n   To resolve:\n"

        # Provide specific commands to find and kill the process
        if lock.port:
            msg += f"   1. Find process: lsof -ti:{lock.port}\n"
            msg += f"   2. Kill process: kill $(lsof -ti:{lock.port})\n"
        else:
            msg += f"   1. Find process: ps -p {lock.pid}\n"
            msg += f"   2. Kill process: kill {lock.pid}\n"

        msg += f"   3. Or force remove lock: ~/.claude/hooks/duplicate_process_blocker.py --kill {lock.command_hash}\n"
        msg += "\n   Alternative: Use a different port for the new server"

        return msg

    # --- CLI Reporting Methods ---

    def show_status(self) -> None:
        print("🔍 Active Development Server Locks:\n")
        found = False
        for path in self.lock_dir.glob(f"{LOCK_FILE_PREFIX}*.lock"):
            lock = self._read_lock(path)
            if lock and lock.is_running:
                found = True
                dt = datetime.fromtimestamp(lock.timestamp).strftime("%Y-%m-%d %H:%M:%S")
                print(f"📋 Command: {lock.command}")
                print(f"   PID: {lock.pid}")
                print(f"   Started: {dt} ({lock.age_minutes:.1f} mins ago)")
                print(f"   Session: {lock.session_id}")
                print(f"   Lock: {path}\n")

        if not found:
            print("✅ No active development server locks found.")

    def manual_cleanup(self) -> None:
        print("🧹 Cleaning up stale development server locks...")
        count = self._clean_stale_locks()
        print(
            f"✅ Cleaned up {count} stale lock file(s)."
            if count
            else "✅ No stale locks found."
        )

    def kill_lock(self, cmd_hash: str) -> bool:
        """Force remove a specific lock by command hash."""
        lock_path = self._get_lock_path(cmd_hash)

        if not lock_path.exists():
            print(f"❌ No lock found with hash: {cmd_hash}")
            return False

        lock = self._read_lock(lock_path)
        if lock:
            print(f"🔍 Found lock: '{lock.command}' (PID: {lock.pid})")
            if lock.is_running:
                print(f"⚠️  Warning: Process {lock.pid} is still running!")
                print(f"   Consider killing it first: kill {lock.pid}")

        if self._cleanup_path(lock_path):
            print(f"✅ Lock removed: {lock_path}")
            return True
        else:
            print(f"❌ Failed to remove lock: {lock_path}")
            return False

    def cleanup_session(self, session_id: str) -> int:
        """Clean up all locks created by a specific session."""
        cleaned = 0
        if not self.lock_dir.exists():
            return 0

        for path in self.lock_dir.glob(f"{LOCK_FILE_PREFIX}*.lock"):
            lock = self._read_lock(path)
            if lock and lock.session_id == session_id:
                if self._cleanup_path(path):
                    cleaned += 1
                    print(f"🧹 Cleaned session lock: {lock.command} (PID: {lock.pid})")

        return cleaned


def main():
    parser = argparse.ArgumentParser(description="Duplicate Process Blocker Hook")
    parser.add_argument("--status", action="store_true", help="Show active locks")
    parser.add_argument("--cleanup", action="store_true", help="Clean stale locks")
    parser.add_argument(
        "--kill", type=str, metavar="HASH", help="Force remove lock by command hash"
    )
    parser.add_argument(
        "--session-cleanup",
        type=str,
        metavar="SESSION_ID",
        help="Clean locks for specific session",
    )
    args = parser.parse_args()

    # Fail open logic: verify we can initialize without crashing
    try:
        blocker = ProcessBlocker()
    except Exception as e:
        print(f"Warning: Process blocker init failed: {e}", file=sys.stderr)
        sys.exit(0)

    if args.status:
        blocker.show_status()
        sys.exit(0)
    if args.cleanup:
        blocker.manual_cleanup()
        sys.exit(0)
    if args.kill:
        success = blocker.kill_lock(args.kill)
        sys.exit(0 if success else 1)
    if args.session_cleanup:
        count = blocker.cleanup_session(args.session_cleanup)
        if count > 0:
            print(f"✅ Cleaned up {count} session lock(s)")
        else:
            print("✅ No locks found for this session")
        sys.exit(0)

    # Hook Mode: Process stdin
    try:
        # Peek at stdin to see if there is data without blocking indefinitely
        # (Though in hook context, stdin is usually ready)
        if sys.stdin.isatty():
            sys.exit(0)

        input_data = json.load(sys.stdin)

        # Fast exit if not a relevant tool
        if input_data.get("tool_name") != "Bash":
            sys.exit(0)

        command = input_data.get("tool_input", {}).get("command", "")
        session_id = input_data.get("session_id", "unknown")

        should_block, msg = blocker.check_and_lock(command, session_id)

        if msg:
            print(msg)

        # Exit 2 tells Claude the tool failed/was rejected
        sys.exit(2 if should_block else 0)

    except (json.JSONDecodeError, BrokenPipeError):
        # Fail open if input is malformed
        sys.exit(0)
    except Exception as e:
        # Log error to stderr but allow process to continue (fail open)
        print(f"Error in dev-server-blocker: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
