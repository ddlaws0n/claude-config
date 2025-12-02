"""
Simplified hook handler integration tests.

Tests the actual hook handler executables to ensure they execute successfully
without crashing and handle various input scenarios gracefully.

Focus on integration testing rather than detailed sound verification.
"""

import json
import subprocess
from pathlib import Path

import pytest


@pytest.mark.integration
class TestHookHandlerExecution:
    """Test all hook handlers execute successfully with valid inputs."""

    def test_pre_tool_handler_git_commit(self, pre_tool_bash_commit_fixture):
        """Test pre_tool_handler with git commit command."""
        hook_path = Path(__file__).parent.parent / "hooks" / "pre_tool_handler"
        json_input = json.dumps(pre_tool_bash_commit_fixture)
        
        result = subprocess.run(
            [str(hook_path)],
            input=json_input,
            text=True,
            capture_output=True
        )
        
        assert result.returncode == 0

    def test_post_tool_handler_write(self, post_tool_write_fixture):
        """Test post_tool_handler with Write tool."""
        hook_path = Path(__file__).parent.parent / "hooks" / "post_tool_handler"
        json_input = json.dumps(post_tool_write_fixture)
        
        result = subprocess.run(
            [str(hook_path)],
            input=json_input,
            text=True,
            capture_output=True
        )
        
        assert result.returncode == 0

    def test_notification_handler(self, notification_waiting_fixture):
        """Test notification_handler with waiting message."""
        hook_path = Path(__file__).parent.parent / "hooks" / "notification_handler"
        json_input = json.dumps(notification_waiting_fixture)
        
        result = subprocess.run(
            [str(hook_path)],
            input=json_input,
            text=True,
            capture_output=True
        )
        
        assert result.returncode == 0
        # Notification handler should acknowledge
        assert "Sound notification played" in result.stdout

    def test_session_start_handler(self, session_start_fixture):
        """Test session_start_handler with startup source."""
        hook_path = Path(__file__).parent.parent / "hooks" / "session_start_handler"
        json_input = json.dumps(session_start_fixture)
        
        result = subprocess.run(
            [str(hook_path)],
            input=json_input,
            text=True,
            capture_output=True
        )
        
        assert result.returncode == 0
        # Session start should add context message (check JSON output)
        try:
            output_data = json.loads(result.stdout)
            additional_context = output_data.get("hookSpecificOutput", {}).get("additionalContext", "")
            assert "Claude Code session started" in additional_context
        except json.JSONDecodeError:
            # Fallback: check if context message is in plain stdout
            assert "Claude Code session started" in result.stdout


@pytest.mark.error_handling
class TestHookErrorResilience:
    """Test hook handlers handle errors gracefully."""

    def test_all_handlers_handle_malformed_json(self):
        """Test all handlers handle malformed JSON gracefully."""
        hook_names = ["pre_tool_handler", "post_tool_handler", 
                     "notification_handler", "session_start_handler"]
        
        hooks_dir = Path(__file__).parent.parent / "hooks"
        malformed_json = '{"invalid": json malformed}'
        
        for hook_name in hook_names:
            hook_path = hooks_dir / hook_name
            
            result = subprocess.run(
                [str(hook_path)],
                input=malformed_json,
                text=True,
                capture_output=True
            )
            
            # Should exit with code 0 (graceful failure)
            assert result.returncode == 0, f"Hook {hook_name} failed with malformed JSON"

    def test_all_handlers_handle_empty_input(self):
        """Test all handlers handle empty input gracefully."""
        hook_names = ["pre_tool_handler", "post_tool_handler",
                     "notification_handler", "session_start_handler"]
        
        hooks_dir = Path(__file__).parent.parent / "hooks"
        
        for hook_name in hook_names:
            hook_path = hooks_dir / hook_name
            
            result = subprocess.run(
                [str(hook_path)],
                input="",
                text=True,
                capture_output=True
            )
            
            # Should exit with code 0 (graceful failure)
            assert result.returncode == 0, f"Hook {hook_name} failed with empty input"

    def test_wrong_context_type_handling(self):
        """Test hooks handle wrong context types gracefully."""
        # Send PostToolUse data to PreToolUse handler
        wrong_type_fixture = {
            "session_id": "test",
            "transcript_path": "/test/path",
            "cwd": "/test",
            "hook_event_name": "PostToolUse",  # Wrong for pre_tool_handler
            "tool_name": "Write",
            "tool_response": {"success": True}
        }
        
        hook_path = Path(__file__).parent.parent / "hooks" / "pre_tool_handler"
        json_input = json.dumps(wrong_type_fixture)
        
        result = subprocess.run(
            [str(hook_path)],
            input=json_input,
            text=True,
            capture_output=True
        )
        
        # Should exit successfully (context type check should handle this)
        assert result.returncode == 0


@pytest.mark.performance
class TestHookPerformance:
    """Test hook execution performance."""

    def test_hook_execution_speed(self, post_tool_write_fixture):
        """Test that hooks execute quickly (under timeout)."""
        import time
        
        hook_path = Path(__file__).parent.parent / "hooks" / "post_tool_handler"
        json_input = json.dumps(post_tool_write_fixture)
        
        start_time = time.time()
        
        result = subprocess.run(
            [str(hook_path)],
            input=json_input,
            text=True,
            capture_output=True,
            timeout=5  # 5-second timeout (hooks configured with 5s timeout)
        )
        
        execution_time = time.time() - start_time
        
        assert result.returncode == 0
        assert execution_time < 1.0, f"Hook execution took {execution_time}s, should be < 1s"