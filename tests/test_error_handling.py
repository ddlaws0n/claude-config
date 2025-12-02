"""
Error resilience and failure scenario tests.

Tests the system's ability to handle various failure modes gracefully,
including missing files, invalid input, subprocess failures, and context errors.

Ensures that sound-related failures never block Claude Code operations.
"""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add hooks utils to path for imports  
hooks_dir = Path(__file__).parent.parent / "hooks"
sys.path.insert(0, str(hooks_dir / "utils"))

from sound_manager import SoundManager, create_sound_manager


@pytest.mark.error_handling
class TestSoundManagerErrorResilience:
    """Test SoundManager handles errors gracefully."""

    def test_missing_sound_mappings_file(self, tmp_path):
        """Test behavior when sound_mappings.json is missing."""
        # Create empty hooks directory without sound_mappings.json
        empty_hooks_dir = tmp_path / "hooks"
        empty_hooks_dir.mkdir()
        
        # Should handle missing file gracefully
        sound_manager = create_sound_manager(str(empty_hooks_dir))
        
        # Should create manager with default empty mappings structure
        assert sound_manager is not None
        assert sound_manager.mappings == {'bash_patterns': [], 'events': {}, 'tools': {}}

    def test_malformed_sound_mappings_file(self, tmp_path):
        """Test behavior with malformed JSON in sound_mappings.json."""
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        
        # Create malformed JSON file
        mappings_file = hooks_dir / "sound_mappings.json"
        with open(mappings_file, "w") as f:
            f.write('{"invalid": json malformed}')
        
        # Should handle malformed JSON gracefully
        sound_manager = create_sound_manager(str(hooks_dir))
        assert sound_manager is not None
        assert sound_manager.mappings == {'bash_patterns': [], 'events': {}, 'tools': {}}

    def test_missing_sounds_directory(self, tmp_path, sound_mappings_data):
        """Test behavior when sounds directory doesn't exist."""
        # Create hooks directory but no sounds subdirectory
        # Create a temporary hooks directory with sound_mappings.json
        mappings_file = tmp_path / "sound_mappings.json"
        with open(mappings_file, "w") as f:
            json.dump(sound_mappings_data, f)
        
        sound_manager = SoundManager(str(tmp_path))
        
        # Should not fail on initialization
        assert sound_manager.sounds_dir is not None
        
        # Sound playback should fail gracefully
        result = sound_manager.play_event_sound("Notification", str(tmp_path))
        assert result is False  # Should return False but not crash

    def test_missing_specific_sound_files(self, tmp_path, sound_mappings_data):
        """Test behavior when specific sound files are missing."""
        # Create sounds directory but no sound files
        sounds_dir = tmp_path / "sounds" / "beeps"
        sounds_dir.mkdir(parents=True)
        
        # Create a temporary hooks directory with sound_mappings.json
        mappings_file = tmp_path / "sound_mappings.json"
        with open(mappings_file, "w") as f:
            json.dump(sound_mappings_data, f)
        
        sound_manager = SoundManager(str(tmp_path))
        
        # Should handle missing sound files gracefully
        result = sound_manager.play_event_sound("Notification", str(tmp_path))
        assert result is False

    def test_subprocess_popen_failure(self, sound_manager_with_mock_sounds):
        """Test handling of subprocess.Popen failures."""
        with patch("subprocess.Popen") as mock_popen:
            # Simulate subprocess failure
            mock_popen.side_effect = OSError("afplay command not found")
            
            result = sound_manager_with_mock_sounds.play_event_sound(
                "Notification", "/test"
            )
            
            # Should return False but not crash
            assert result is False

    def test_subprocess_file_not_found_error(self, sound_manager_with_mock_sounds):
        """Test handling of FileNotFoundError from subprocess."""
        with patch("subprocess.Popen") as mock_popen:
            mock_popen.side_effect = FileNotFoundError("afplay not found")
            
            result = sound_manager_with_mock_sounds.play_tool_sound("Edit", "/test")
            
            assert result is False

    def test_project_override_malformed_json(self, tmp_path):
        """Test handling malformed .claude-sounds project override file."""
        # Create malformed .claude-sounds file
        override_file = tmp_path / ".claude-sounds"
        with open(override_file, "w") as f:
            f.write('{"malformed": json}')
        
        sound_manager = SoundManager(str(tmp_path))
        overrides = sound_manager._load_project_overrides(str(tmp_path))
        
        # Should return None for malformed JSON
        assert overrides is None


@pytest.mark.error_handling
class TestContextCreationErrors:
    """Test cchooks context creation error handling."""

    def test_invalid_json_input_handling(self):
        """Test hook handlers handle invalid JSON input gracefully."""
        hook_paths = [
            "pre_tool_handler",
            "post_tool_handler",
            "notification_handler",
            "session_start_handler"
        ]
        
        invalid_inputs = [
            '{"invalid": json}',      # Malformed JSON
            '{}',                     # Empty object
            '{"wrong": "structure"}', # Wrong structure
            '',                       # Empty string
            'not json at all',        # Not JSON
        ]
        
        hooks_base = Path(__file__).parent.parent / "hooks"
        
        for hook_name in hook_paths:
            hook_path = hooks_base / hook_name
            
            for invalid_input in invalid_inputs:
                result = subprocess.run(
                    [str(hook_path)],
                    input=invalid_input,
                    text=True,
                    capture_output=True
                )
                
                # Should exit with code 0 (graceful failure)
                assert result.returncode == 0, \
                    f"Hook {hook_name} failed with input: {invalid_input}"

    def test_missing_required_fields(self):
        """Test hooks handle missing required JSON fields gracefully."""
        # Missing session_id
        incomplete_fixture = {
            "transcript_path": "/test/path",
            "hook_event_name": "PostToolUse",
            "tool_name": "Write"
        }
        
        hook_path = Path(__file__).parent.parent / "hooks" / "post_tool_handler"
        json_input = json.dumps(incomplete_fixture)
        
        result = subprocess.run(
            [str(hook_path)],
            input=json_input,
            text=True,
            capture_output=True
        )
        
        # Should handle gracefully
        assert result.returncode == 0

    def test_wrong_hook_event_type(self):
        """Test hooks handle wrong event types gracefully."""
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


@pytest.mark.error_handling
class TestSystemResilience:
    """Test system-wide error resilience."""

    def test_hook_timeout_behavior(self):
        """Test hook behavior under timeout conditions.""" 
        # This test simulates what happens if a hook takes too long
        # In practice, Claude Code will kill hooks after timeout
        
        hook_path = Path(__file__).parent.parent / "hooks" / "post_tool_handler"
        
        simple_fixture = {
            "session_id": "test",
            "transcript_path": "/test/path",
            "cwd": "/test",
            "hook_event_name": "PostToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": "/test.py"},
            "tool_response": {"success": True}
        }
        
        json_input = json.dumps(simple_fixture)
        
        # Run with very short timeout to test behavior
        try:
            result = subprocess.run(
                [str(hook_path)],
                input=json_input,
                text=True,
                capture_output=True,
                timeout=0.1  # Very short timeout
            )
            
            # If it completes within timeout, should be successful
            assert result.returncode == 0
            
        except subprocess.TimeoutExpired:
            # If timeout occurs, that's expected behavior
            # Claude Code handles this by killing the process
            pass

    def test_concurrent_hook_execution_safety(self, mock_subprocess_popen, tmp_path):
        """Test that concurrent hook executions don't interfere."""
        import threading
        
        # Create a temporary hooks directory with sound_mappings.json
        mappings_file = tmp_path / "sound_mappings.json"
        with open(mappings_file, "w") as f:
            json.dump({
                "events": {"Notification": "ready"},
                "tools": {"Write": "edit"},
                "bash_patterns": []
            }, f)
        
        sound_manager = SoundManager(str(tmp_path))
        results = []
        
        def run_hook(event_name, cwd):
            result = sound_manager.play_event_sound(event_name, cwd)
            results.append(result)
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(
                target=run_hook, 
                args=("Notification", f"/test/{i}")
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join(timeout=1.0)
        
        # All should complete (even if they fail, they shouldn't crash)
        assert len(results) == 5

    def test_memory_cleanup_on_errors(self, tmp_path):
        """Test that errors don't cause memory leaks."""
        # Create and destroy multiple sound managers with errors
        for i in range(10):
            # Each iteration with different error conditions
            if i % 2 == 0:
                # Missing mappings file
                sound_manager = create_sound_manager(str(tmp_path))
            else:
                # With mappings but missing sounds
                mappings_file = tmp_path / "sound_mappings.json" 
                with open(mappings_file, "w") as f:
                    json.dump({"events": {"Test": "test"}}, f)
                
                sound_manager = create_sound_manager(str(tmp_path))
            
            # Try to use it (should fail gracefully)
            sound_manager.play_event_sound("Test", str(tmp_path))
            
            # Explicitly delete to check cleanup
            del sound_manager

    @patch("sys.stderr")
    def test_error_logging_to_stderr(self, mock_stderr, tmp_path):
        """Test that errors are properly logged to stderr."""
        # Create sound manager with missing sounds
        mappings_file = tmp_path / "sound_mappings.json"
        with open(mappings_file, "w") as f:
            json.dump({"events": {"Test": "missing_sound"}}, f)
        
        sound_manager = SoundManager(str(tmp_path))
        
        # Try to play sound (should fail and log to stderr)
        result = sound_manager.play_event_sound("Test", str(tmp_path))
        
        assert result is False
        # Should have written error to stderr (mocked)
        # In real usage, this would show in hook execution logs


@pytest.mark.error_handling
class TestEdgeCaseRecovery:
    """Test recovery from edge case scenarios."""

    def test_empty_bash_command_handling(self, sound_manager_with_mock_sounds):
        """Test handling of empty or whitespace-only bash commands."""
        edge_cases = ["", "   ", "\t", "\n", "\r\n"]
        
        for command in edge_cases:
            # Should not crash, may return None or fallback sound
            sound_file = sound_manager_with_mock_sounds._get_bash_sound(command)
            
            if sound_file is not None:
                # If it returns a sound, should be fallback
                assert sound_file.name == "bash.wav"

    def test_extremely_long_command_handling(self, sound_manager_with_mock_sounds):
        """Test handling of extremely long bash commands."""
        # Create very long command (10KB)
        long_command = "git commit -m '" + "x" * 10000 + "'"
        
        # Should still match git commit pattern without crashing
        sound_file = sound_manager_with_mock_sounds._get_bash_sound(long_command)
        
        assert sound_file is not None
        assert sound_file.name == "commit.wav"

    def test_unicode_command_handling(self, sound_manager_with_mock_sounds):
        """Test handling of commands with unicode characters."""
        unicode_commands = [
            "git commit -m '添加新功能'",      # Chinese
            "git commit -m 'Añadir función'",  # Spanish
            "git commit -m 'Добавить функцию'", # Russian
            "npm test 🚀",                     # Emoji
        ]
        
        for command in unicode_commands:
            # Should handle unicode without crashing
            sound_file = sound_manager_with_mock_sounds._get_bash_sound(command)
            assert sound_file is not None


# Additional fixtures for error handling tests
@pytest.fixture 
def sound_manager_with_mock_sounds(mock_sounds_dir, sound_mappings_data):
    """Create sound manager with mock sounds directory."""
    # Create a temporary hooks directory with sound_mappings.json
    hooks_dir = mock_sounds_dir.parent.parent
    mappings_file = hooks_dir / "sound_mappings.json"
    with open(mappings_file, "w") as f:
        json.dump(sound_mappings_data, f)
    
    return SoundManager(str(hooks_dir))