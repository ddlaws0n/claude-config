#!/usr/bin/env python3
"""
General utilities for Claude Code hooks.
Common helper functions and utilities.
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


def read_hook_input() -> Dict[str, Any]:
    """
    Read JSON input from stdin for hook processing.

    Returns:
        Parsed JSON data as dictionary
    """
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading input: {e}", file=sys.stderr)
        sys.exit(1)


def write_hook_output(data: Dict[str, Any], exit_code: int = 0):
    """
    Write JSON output and exit.

    Args:
        data: Data to output as JSON
        exit_code: Exit code (0 for success, 2 to block)
    """
    try:
        print(json.dumps(data))
        sys.exit(exit_code)
    except Exception as e:
        print(f"Error writing output: {e}", file=sys.stderr)
        sys.exit(1 if exit_code == 0 else exit_code)


def get_project_root(start_path: Optional[str] = None) -> Optional[str]:
    """
    Find the project root directory.

    Args:
        start_path: Path to start searching from (defaults to current directory)

    Returns:
        Path to project root or None if not found
    """
    if start_path is None:
        start_path = os.getcwd()

    path = Path(start_path).resolve()

    # Common project indicators
    indicators = [
        ".git",
        "package.json",
        "pyproject.toml",
        "Cargo.toml",
        "go.mod",
        "pom.xml",
        "build.gradle",
        "requirements.txt",
        "setup.py",
        "composer.json",
        "Gemfile",
        ".claude",
    ]

    # Walk up the directory tree
    while path != path.parent:
        for indicator in indicators:
            if (path / indicator).exists():
                return str(path)
        path = path.parent

    return None


def ensure_directory(path: str) -> bool:
    """
    Ensure directory exists, create if necessary.

    Args:
        path: Directory path

    Returns:
        True if directory exists or was created successfully
    """
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False


def get_tool_input_value(
    input_data: Dict[str, Any], key: str, default: Any = None
) -> Any:
    """
    Safely get a value from tool input data.

    Args:
        input_data: Hook input data
        key: Key to extract from tool_input
        default: Default value if key not found

    Returns:
        Extracted value or default
    """
    try:
        return input_data.get("tool_input", {}).get(key, default)
    except Exception:
        return default


def matches_pattern(text: str, pattern: str) -> bool:
    """
    Check if text matches a pattern (supports regex and simple strings).

    Args:
        text: Text to check
        pattern: Pattern to match against

    Returns:
        True if text matches pattern
    """
    import re

    # Handle regex patterns
    if pattern.startswith("regex:"):
        regex_pattern = pattern[6:]
        try:
            return bool(re.search(regex_pattern, text))
        except re.error:
            return False

    # Handle wildcard patterns
    elif "*" in pattern or "?" in pattern:
        # Convert shell glob to regex
        import fnmatch

        return fnmatch.fnmatch(text, pattern)

    # Simple string match
    else:
        return text == pattern


def debounce(
    file_path: str, delay_seconds: float = 5.0, marker_suffix: str = ".debounce"
) -> bool:
    """
    Check if an operation should be debounced (delayed to avoid frequent execution).

    Args:
        file_path: Path to file being operated on
        delay_seconds: Minimum time between operations
        marker_suffix: Suffix for debounce marker files

    Returns:
        True if operation should proceed (not debounced)
    """
    import os
    import time

    # Create debounce directory
    debounce_dir = os.path.expanduser("~/.claude/debounce")
    ensure_directory(debounce_dir)

    # Create marker file path
    marker_file = Path(debounce_dir) / f"{file_path.replace('/', '_')}{marker_suffix}"

    # Check if marker exists and is recent
    if marker_file.exists():
        mtime = marker_file.stat().st_mtime
        if time.time() - mtime < delay_seconds:
            return False  # Debounce

    # Update marker
    try:
        marker_file.touch()
    except Exception:
        pass  # Fail silently

    return True


def get_file_language(file_path: str) -> Optional[str]:
    """
    Get programming language from file extension.

    Args:
        file_path: File path

    Returns:
        Language string or None
    """
    ext = Path(file_path).suffix.lower()

    language_map = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".c": "c",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".cs": "csharp",
        ".php": "php",
        ".rb": "ruby",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "bash",
        ".fish": "fish",
        ".ps1": "powershell",
        ".bat": "batch",
        ".cmd": "batch",
        ".html": "html",
        ".htm": "html",
        ".css": "css",
        ".scss": "scss",
        ".sass": "sass",
        ".less": "less",
        ".sql": "sql",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".xml": "xml",
        ".md": "markdown",
        ".mdx": "markdown",
        ".dockerfile": "docker",
        ".dockerignore": "docker",
    }

    return language_map.get(ext)


def run_command(
    cmd: List[str],
    cwd: Optional[str] = None,
    timeout: Optional[int] = None,
    capture_output: bool = True,
) -> Dict[str, Any]:
    """
    Run a command safely.

    Args:
        cmd: Command to run (list of strings)
        cwd: Working directory
        timeout: Timeout in seconds
        capture_output: Whether to capture output

    Returns:
        Dictionary with results
    """
    result = {
        "success": False,
        "returncode": None,
        "stdout": "",
        "stderr": "",
        "timeout": False,
        "error": None,
    }

    try:
        import subprocess

        proc = subprocess.run(
            cmd,
            cwd=cwd or os.getcwd(),
            timeout=timeout,
            capture_output=capture_output,
            text=True,
        )

        result.update(
            {
                "success": proc.returncode == 0,
                "returncode": proc.returncode,
                "stdout": proc.stdout if capture_output else "",
                "stderr": proc.stderr if capture_output else "",
            }
        )

    except subprocess.TimeoutExpired:
        result["timeout"] = True
        result["error"] = f"Command timed out after {timeout} seconds"

    except FileNotFoundError:
        result["error"] = f"Command not found: {cmd[0]}"

    except Exception as e:
        result["error"] = str(e)

    return result


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def format_bytes(bytes_count: int) -> str:
    """
    Format bytes in human-readable format.

    Args:
        bytes_count: Number of bytes

    Returns:
        Formatted bytes string
    """
    count_float: float = float(bytes_count)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if count_float < 1024.0:
            return f"{count_float:.1f}{unit}"
        count_float /= 1024.0
    return f"{count_float:.1f}PB"


class RateLimiter:
    """Simple rate limiter."""

    def __init__(self, max_calls: int, time_window: float):
        """
        Initialize rate limiter.

        Args:
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []

    def is_allowed(self) -> bool:
        """
        Check if a call is allowed.

        Returns:
            True if call is allowed
        """
        now = time.time()

        # Remove old calls outside time window
        self.calls = [
            call_time for call_time in self.calls if now - call_time < self.time_window
        ]

        # Check if we're under the limit
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True

        return False

    def time_until_next_call(self) -> float:
        """
        Get time until next call is allowed.

        Returns:
            Seconds until next call (0 if allowed now)
        """
        if self.is_allowed():
            return 0

        oldest_call = min(self.calls)
        return self.time_window - (time.time() - oldest_call)


class Cache:
    """Simple file-based cache."""

    def __init__(self, cache_dir: Optional[str] = None, ttl_seconds: int = 3600):
        """
        Initialize cache.

        Args:
            cache_dir: Cache directory path
            ttl_seconds: Time-to-live for cache entries
        """
        self.cache_dir = cache_dir or os.path.expanduser("~/.claude/cache")
        self.ttl_seconds = ttl_seconds
        ensure_directory(self.cache_dir)

    def _get_cache_path(self, key: str) -> str:
        """Get cache file path for key."""
        import hashlib

        safe_key = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{safe_key}.cache")

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        cache_path = self._get_cache_path(key)

        if not os.path.exists(cache_path):
            return None

        # Check if expired
        if time.time() - os.path.getmtime(cache_path) > self.ttl_seconds:
            try:
                os.remove(cache_path)
            except Exception:
                pass
            return None

        # Read cached value
        try:
            with open(cache_path, "r") as f:
                return json.load(f)
        except Exception:
            return None

    def set(self, key: str, value: Any) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache

        Returns:
            True if successfully cached
        """
        cache_path = self._get_cache_path(key)

        try:
            with open(cache_path, "w") as f:
                json.dump(value, f)
            return True
        except Exception:
            return False

    def clear(self, pattern: Optional[str] = None):
        """
        Clear cache entries.

        Args:
            pattern: Optional pattern to match keys (clears all if None)
        """
        try:
            import fnmatch

            for cache_file in os.listdir(self.cache_dir):
                if cache_file.endswith(".cache"):
                    if pattern is None or fnmatch.fnmatch(
                        cache_file, f"*{pattern}*.cache"
                    ):
                        os.remove(os.path.join(self.cache_dir, cache_file))
        except Exception:
            pass


# Global cache instance
_cache = Cache()


def cached(ttl_seconds: int = 3600):
    """Decorator for caching function results."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

            # Try to get from cache
            result = _cache.get(cache_key)
            if result is not None:
                return result

            # Compute and cache result
            result = func(*args, **kwargs)
            _cache.set(cache_key, result)
            return result

        return wrapper

    return decorator


def main():
    """
    Command line interface for testing utilities.
    """
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Hook utilities")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Project root
    root_parser = subparsers.add_parser("project-root", help="Find project root")
    root_parser.add_argument("--path", help="Start path")

    # Language detection
    lang_parser = subparsers.add_parser("language", help="Detect file language")
    lang_parser.add_argument("file_path", help="File path")

    # Rate limit test
    rate_parser = subparsers.add_parser("rate-limit", help="Test rate limiter")
    rate_parser.add_argument("--calls", type=int, default=5)
    rate_parser.add_argument("--window", type=float, default=2.0)

    args = parser.parse_args()

    if args.command == "project-root":
        root = get_project_root(args.path)
        print(json.dumps({"project_root": root}))

    elif args.command == "language":
        lang = get_file_language(args.file_path)
        print(json.dumps({"language": lang}))

    elif args.command == "rate-limit":
        limiter = RateLimiter(args.calls, args.window)
        print(f"Testing rate limiter: {args.calls} calls per {args.window}s")
        for i in range(10):
            if limiter.is_allowed():
                print(f"  Call {i + 1}: Allowed")
            else:
                wait = limiter.time_until_next_call()
                print(f"  Call {i + 1}: Rate limited (wait {wait:.1f}s)")
            time.sleep(0.5)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
