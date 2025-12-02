"""
Test configuration and fixtures for Claude Code hooks test suite.

Provides real hook event JSON fixtures and test helpers for comprehensive testing
of the cchooks-based sound hook implementation.
"""

import json
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def hooks_dir() -> Path:
    """Return the hooks directory path."""
    path: Path = Path(__file__).parent.parent / "hooks"
    return path


@pytest.fixture
def sound_mappings_path(hooks_dir) -> Path:
    """Return the sound mappings JSON file path."""
    path: Path = hooks_dir / "sound_mappings.json"
    return path


@pytest.fixture
def sound_mappings_data(sound_mappings_path) -> dict[str, Any]:
    """Load and return sound mappings configuration."""
    with open(sound_mappings_path) as f:
        data: dict[str, Any] = json.load(f)
        return data


@pytest.fixture
def mock_sounds_dir():
    """Create a temporary sounds directory with mock sound files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        sounds_dir = Path(temp_dir) / "sounds" / "beeps"
        sounds_dir.mkdir(parents=True)
        
        # Create mock sound files
        for sound_name in ["ready", "edit", "list", "commit", "pr", "test", "bash", "stop"]:
            (sounds_dir / f"{sound_name}.wav").touch()
        
        yield sounds_dir


@pytest.fixture
def mock_subprocess_popen():
    """Mock subprocess.Popen for sound playback testing."""
    with patch("subprocess.Popen") as mock_popen:
        mock_process = MagicMock()
        mock_popen.return_value = mock_process
        yield mock_popen


# Real hook event fixtures from actual Claude Code testing
@pytest.fixture
def post_tool_write_fixture() -> dict[str, Any]:
    """PostToolUse hook event for Write tool completion."""
    return {
        "session_id": "test-session-123",
        "transcript_path": "/test/transcript.jsonl",
        "cwd": "/Users/test/.claude",
        "hook_event_name": "PostToolUse", 
        "tool_name": "Write",
        "tool_input": {
            "file_path": "/test/example.py",
            "content": "print('Hello World')"
        },
        "tool_response": {
            "filePath": "/test/example.py",
            "success": True
        }
    }


@pytest.fixture
def pre_tool_bash_commit_fixture() -> dict[str, Any]:
    """PreToolUse hook event for git commit command."""
    return {
        "session_id": "test-session-456",
        "transcript_path": "/test/transcript.jsonl", 
        "cwd": "/Users/test/project",
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {
            "command": "git commit -m \"Add new feature\""
        }
    }


@pytest.fixture
def pre_tool_bash_test_fixture() -> dict[str, Any]:
    """PreToolUse hook event for npm test command."""
    return {
        "session_id": "test-session-789",
        "transcript_path": "/test/transcript.jsonl",
        "cwd": "/Users/test/project", 
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {
            "command": "npm test"
        }
    }


@pytest.fixture
def notification_waiting_fixture() -> dict[str, Any]:
    """Notification hook event for user input waiting."""
    return {
        "session_id": "test-session-abc",
        "transcript_path": "/test/transcript.jsonl",
        "cwd": "/Users/test/.claude",
        "hook_event_name": "Notification",
        "message": "Claude is waiting for your input"
    }


@pytest.fixture
def session_start_fixture() -> dict[str, Any]:
    """SessionStart hook event for startup."""
    return {
        "session_id": "test-session-def", 
        "transcript_path": "/test/transcript.jsonl",
        "hook_event_name": "SessionStart",
        "source": "startup"
    }


@pytest.fixture
def todo_write_fixture() -> dict[str, Any]:
    """PostToolUse hook event for TodoWrite tool."""
    return {
        "session_id": "test-session-ghi",
        "transcript_path": "/test/transcript.jsonl",
        "cwd": "/Users/test/project",
        "hook_event_name": "PostToolUse",
        "tool_name": "TodoWrite", 
        "tool_input": {
            "todos": [
                {"content": "Implement feature X", "status": "pending"}
            ]
        },
        "tool_response": {
            "success": True
        }
    }


@pytest.fixture
def project_override_config():
    """Mock .claude-sounds project override configuration."""
    return {
        "sounds_type": "beeps",
        "custom_mappings": {
            "Edit": "custom_edit",
            "bash_patterns": [
                ["^npm run build", "build"],
                ["^docker", "docker"]
            ]
        }
    }


@pytest.fixture
def mock_project_override_file(tmp_path):
    """Create temporary .claude-sounds file for project override testing."""
    override_config = {
        "sounds_type": "beeps", 
        "custom_mappings": {
            "Edit": "custom_edit",
            "bash_patterns": [
                ["^npm run build", "build"],
                ["^docker", "docker"]
            ]
        }
    }
    
    override_file = tmp_path / ".claude-sounds"
    with open(override_file, "w") as f:
        json.dump(override_config, f)
    
    return override_file


class MockContext:
    """Mock context object for testing hook handlers without cchooks dependency."""
    
    def __init__(self, hook_type: str, **kwargs):
        self.hook_event_name = hook_type
        self.output = MockOutput()
        
        # Set attributes based on hook type
        for key, value in kwargs.items():
            setattr(self, key, value)


class MockOutput:
    """Mock output object for testing context output methods."""
    
    def __init__(self):
        self.calls = []
    
    def exit_success(self, message: str | None = None):
        self.calls.append(("exit_success", message))
    
    def acknowledge(self, message: str | None = None):
        self.calls.append(("acknowledge", message))
    
    def add_context(self, context: str):
        self.calls.append(("add_context", context))


@pytest.fixture
def mock_create_context():
    """Mock cchooks create_context function for isolated testing."""
    def _create_mock_context(hook_data: dict[str, Any]) -> MockContext:
        hook_type = hook_data["hook_event_name"]
        return MockContext(hook_type, **hook_data)
    
    return _create_mock_context


# Pytest configuration for hook testing
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "sound_logic: Sound mapping and pattern matching tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests with real Claude Code events" 
    )
    config.addinivalue_line(
        "markers", "error_handling: Error resilience and failure scenario tests"
    )
    config.addinivalue_line(
        "markers", "performance: Performance and timeout tests"
    )