"""
Core sound manager functionality tests.

Tests the foundational SoundManager class including sound mapping resolution,
bash pattern matching, project overrides, and error handling.

This is the most critical test module since SoundManager is the core of the
entire hook system.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add hooks utils to path for imports
hooks_dir = Path(__file__).parent.parent / "hooks"
sys.path.insert(0, str(hooks_dir / "utils"))

from sound_manager import (  # pyright: ignore[reportMissingImports]
    SoundManager,
    create_sound_manager,
)


@pytest.mark.sound_logic
class TestSoundManagerInitialization:
    """Test SoundManager initialization and configuration loading."""

    def test_create_sound_manager_success(self, hooks_dir):
        """Test successful sound manager creation."""
        sound_manager = create_sound_manager(str(hooks_dir))

        assert sound_manager is not None
        assert isinstance(sound_manager, SoundManager)
        assert sound_manager.hooks_dir == Path(hooks_dir)
        assert sound_manager.sounds_dir.name == "beeps"

    def test_sound_mappings_loading(self, sound_manager_with_real_config):
        """Test that sound mappings are loaded correctly from JSON."""
        mappings = sound_manager_with_real_config.mappings

        # Verify core event mappings
        assert "events" in mappings
        assert mappings["events"]["Notification"] == "ready"
        assert mappings["events"]["SessionStart"] == "ready"

        # Verify tool mappings
        assert "tools" in mappings
        assert mappings["tools"]["Edit"] == "edit"
        assert mappings["tools"]["TodoWrite"] == "list"

        # Verify bash patterns exist
        assert "bash_patterns" in mappings
        assert len(mappings["bash_patterns"]) > 0

    def test_sounds_directory_resolution(self, hooks_dir):
        """Test that sounds directory is resolved correctly."""
        sound_manager = create_sound_manager(str(hooks_dir))
        expected_sounds_dir = hooks_dir / "sounds" / "beeps"

        assert sound_manager.sounds_dir == expected_sounds_dir

    def test_default_volume_setting(self, hooks_dir):
        """Test default volume setting when no environment variable is set."""
        with patch.dict("os.environ", {}, clear=False):
            # Remove the env var if it exists
            if "CLAUDE_CODE_SOUNDS" in sys.modules.get("os", {}).environ:
                del sys.modules["os"].environ["CLAUDE_CODE_SOUNDS"]
            
            sound_manager = create_sound_manager(str(hooks_dir))
            assert sound_manager.volume == 1.0

    def test_volume_setting_disabled(self, hooks_dir):
        """Test volume setting when sounds are disabled."""
        with patch.dict("os.environ", {"CLAUDE_CODE_SOUNDS": "0"}, clear=False):
            sound_manager = create_sound_manager(str(hooks_dir))
            assert sound_manager.volume == 0.0

    def test_volume_setting_half_volume(self, hooks_dir):
        """Test volume setting at 50%."""
        with patch.dict("os.environ", {"CLAUDE_CODE_SOUNDS": "0.5"}, clear=False):
            sound_manager = create_sound_manager(str(hooks_dir))
            assert sound_manager.volume == 0.5

    def test_volume_setting_quiet(self, hooks_dir):
        """Test volume setting at 10%."""
        with patch.dict("os.environ", {"CLAUDE_CODE_SOUNDS": "0.1"}, clear=False):
            sound_manager = create_sound_manager(str(hooks_dir))
            assert sound_manager.volume == 0.1

    def test_volume_setting_full_volume(self, hooks_dir):
        """Test explicit full volume setting."""
        with patch.dict("os.environ", {"CLAUDE_CODE_SOUNDS": "1.0"}, clear=False):
            sound_manager = create_sound_manager(str(hooks_dir))
            assert sound_manager.volume == 1.0

    def test_volume_setting_clamped_high(self, hooks_dir):
        """Test volume setting is clamped to maximum 1.0."""
        with patch.dict("os.environ", {"CLAUDE_CODE_SOUNDS": "2.5"}, clear=False):
            sound_manager = create_sound_manager(str(hooks_dir))
            assert sound_manager.volume == 1.0

    def test_volume_setting_clamped_low(self, hooks_dir):
        """Test volume setting is clamped to minimum 0.0."""
        with patch.dict("os.environ", {"CLAUDE_CODE_SOUNDS": "-0.5"}, clear=False):
            sound_manager = create_sound_manager(str(hooks_dir))
            assert sound_manager.volume == 0.0

    def test_volume_setting_invalid_value(self, hooks_dir):
        """Test invalid volume setting falls back to default."""
        with patch.dict("os.environ", {"CLAUDE_CODE_SOUNDS": "invalid"}, clear=False):
            with patch("builtins.print") as mock_print:
                sound_manager = create_sound_manager(str(hooks_dir))
                assert sound_manager.volume == 1.0
                # Verify warning was printed
                mock_print.assert_called_once()
                assert "Warning: Invalid CLAUDE_CODE_SOUNDS value" in str(mock_print.call_args)

    def test_volume_setting_empty_string(self, hooks_dir):
        """Test empty string falls back to default volume."""
        with patch.dict("os.environ", {"CLAUDE_CODE_SOUNDS": ""}, clear=False):
            sound_manager = create_sound_manager(str(hooks_dir))
            assert sound_manager.volume == 1.0


@pytest.mark.sound_logic
class TestEventSoundMapping:
    """Test event-to-sound file mapping functionality."""

    def test_event_sound_mapping_notification(self, sound_manager_with_mock_sounds):
        """Test Notification event maps to ready.wav."""
        sound_file = sound_manager_with_mock_sounds._get_event_sound("Notification")

        assert sound_file is not None
        assert sound_file.name == "ready.wav"

    def test_event_sound_mapping_session_start(self, sound_manager_with_mock_sounds):
        """Test SessionStart event maps to ready.wav."""
        sound_file = sound_manager_with_mock_sounds._get_event_sound("SessionStart")

        assert sound_file is not None
        assert sound_file.name == "ready.wav"

    def test_event_sound_mapping_unknown_event(self, sound_manager_with_mock_sounds):
        """Test unknown event returns None."""
        sound_file = sound_manager_with_mock_sounds._get_event_sound("UnknownEvent")

        assert sound_file is None


@pytest.mark.sound_logic
class TestToolSoundMapping:
    """Test tool-to-sound file mapping functionality."""

    def test_tool_sound_mapping_edit(self, sound_manager_with_mock_sounds):
        """Test Edit tool maps to edit.wav."""
        sound_file = sound_manager_with_mock_sounds._get_tool_sound("Edit")

        assert sound_file is not None
        assert sound_file.name == "edit.wav"

    def test_tool_sound_mapping_multiedit(self, sound_manager_with_mock_sounds):
        """Test MultiEdit tool maps to edit.wav."""
        sound_file = sound_manager_with_mock_sounds._get_tool_sound("MultiEdit")

        assert sound_file is not None
        assert sound_file.name == "edit.wav"

    def test_tool_sound_mapping_todo_write(self, sound_manager_with_mock_sounds):
        """Test TodoWrite tool maps to list.wav."""
        sound_file = sound_manager_with_mock_sounds._get_tool_sound("TodoWrite")

        assert sound_file is not None
        assert sound_file.name == "list.wav"

    def test_tool_sound_mapping_unknown_tool(self, sound_manager_with_mock_sounds):
        """Test unknown tool returns None."""
        sound_file = sound_manager_with_mock_sounds._get_tool_sound("UnknownTool")

        assert sound_file is None


@pytest.mark.sound_logic
class TestBashCommandPatternMatching:
    """Test bash command pattern matching against regex patterns."""

    def test_git_commit_pattern_matching(self, sound_manager_with_mock_sounds):
        """Test git commit commands match commit pattern."""
        test_commands = [
            'git commit -m "Add feature"',
            'git commit -am "Fix bug"',
            'git commit --message="Update docs"',
        ]

        for command in test_commands:
            sound_file = sound_manager_with_mock_sounds._get_bash_sound(command)
            assert sound_file is not None
            assert sound_file.name == "commit.wav", f"Failed for command: {command}"

    def test_github_pr_pattern_matching(self, sound_manager_with_mock_sounds):
        """Test GitHub PR commands match pr pattern."""
        test_commands = ["gh pr create", "gh pr merge 123", "gh pr view"]

        for command in test_commands:
            sound_file = sound_manager_with_mock_sounds._get_bash_sound(command)
            assert sound_file is not None
            assert sound_file.name == "pr.wav", f"Failed for command: {command}"

    def test_test_runner_pattern_matching(self, sound_manager_with_mock_sounds):
        """Test various test runner commands match test pattern."""
        test_commands = [
            "npm test",
            "yarn test",
            "pytest",
            "go test",
            "bun test",
            "pnpm test",
            "just test",
        ]

        for command in test_commands:
            sound_file = sound_manager_with_mock_sounds._get_bash_sound(command)
            assert sound_file is not None
            assert sound_file.name == "test.wav", f"Failed for command: {command}"

    def test_fallback_bash_pattern(self, sound_manager_with_mock_sounds):
        """Test unknown commands fall back to bash.wav."""
        unknown_commands = ["ls -la", "grep pattern file.txt", "custom-command --flag"]

        for command in unknown_commands:
            sound_file = sound_manager_with_mock_sounds._get_bash_sound(command)
            assert sound_file is not None
            assert sound_file.name == "bash.wav", f"Failed for command: {command}"


@pytest.mark.sound_logic
class TestProjectOverrides:
    """Test project-specific sound override functionality."""

    def test_project_override_loading(self, tmp_path):
        """Test loading project override configuration."""
        # Create mock .claude-sounds file
        override_config = {
            "sounds_type": "beeps",
            "custom_mappings": {
                "Edit": "custom_edit",
                "bash_patterns": [["^npm run build", "build"]],
            },
        }

        override_file = tmp_path / ".claude-sounds"
        with open(override_file, "w") as f:
            json.dump(override_config, f)

        # Create sound manager with project override
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            sound_manager = SoundManager(str(tmp_path))
            overrides = sound_manager._load_project_overrides(str(tmp_path))

        assert overrides is not None
        assert "custom_mappings" in overrides
        assert overrides["custom_mappings"]["Edit"] == "custom_edit"

    def test_no_project_override_file(self, tmp_path):
        """Test behavior when no .claude-sounds file exists."""
        sound_manager = SoundManager(str(tmp_path))
        overrides = sound_manager._load_project_overrides(str(tmp_path))

        assert overrides is None


@pytest.mark.sound_logic
class TestSoundPlayback:
    """Test sound file playback functionality."""

    def test_play_sound_file_success(
        self, sound_manager_with_mock_sounds, mock_subprocess_popen
    ):
        """Test successful sound file playback."""
        sound_file = sound_manager_with_mock_sounds.sounds_dir / "ready.wav"
        result = sound_manager_with_mock_sounds._play_sound_file(sound_file)

        assert result is True
        mock_subprocess_popen.assert_called_once()

        # Verify afplay command with volume control
        call_args = mock_subprocess_popen.call_args[0][0]
        assert call_args[0] == "afplay"
        assert call_args[1] == "-v"
        assert call_args[2] == "1.0"  # Default volume
        assert str(sound_file) in call_args[3]

    def test_play_sound_file_missing_file(
        self, sound_manager_with_mock_sounds, mock_subprocess_popen
    ):
        """Test playback with missing sound file."""
        missing_file = Path("/nonexistent/sound.wav")

        # Mock OSError to simulate missing file
        mock_subprocess_popen.side_effect = OSError("No such file")

        result = sound_manager_with_mock_sounds._play_sound_file(missing_file)

        assert result is False

    def test_play_sound_file_with_volume_control(
        self, hooks_dir, mock_subprocess_popen
    ):
        """Test sound file playback includes volume parameter."""
        with patch.dict("os.environ", {"CLAUDE_CODE_SOUNDS": "0.5"}, clear=False):
            sound_manager = create_sound_manager(str(hooks_dir))
            sound_file = hooks_dir / "sounds" / "beeps" / "ready.wav"
            
            # Create the sound file for the test
            sound_file.parent.mkdir(parents=True, exist_ok=True)
            sound_file.touch()
            
            result = sound_manager._play_sound_file(sound_file)
            
            assert result is True
            mock_subprocess_popen.assert_called_once()
            call_args = mock_subprocess_popen.call_args[0][0]
            assert call_args[0] == "afplay"
            assert call_args[1] == "-v"
            assert call_args[2] == "0.5"
            assert str(sound_file) in call_args[3]

    def test_play_sound_file_disabled_volume(
        self, hooks_dir, mock_subprocess_popen
    ):
        """Test sound file playback is skipped when volume is 0."""
        with patch.dict("os.environ", {"CLAUDE_CODE_SOUNDS": "0"}, clear=False):
            sound_manager = create_sound_manager(str(hooks_dir))
            sound_file = hooks_dir / "sounds" / "beeps" / "ready.wav" 
            
            result = sound_manager._play_sound_file(sound_file)
            
            # Should return False for disabled sounds and not call subprocess
            assert result is False
            mock_subprocess_popen.assert_not_called()

    def test_play_sound_file_full_volume(
        self, hooks_dir, mock_subprocess_popen
    ):
        """Test sound file playback with full volume (1.0)."""
        with patch.dict("os.environ", {"CLAUDE_CODE_SOUNDS": "1.0"}, clear=False):
            sound_manager = create_sound_manager(str(hooks_dir))
            sound_file = hooks_dir / "sounds" / "beeps" / "ready.wav"
            
            # Create the sound file for the test
            sound_file.parent.mkdir(parents=True, exist_ok=True)
            sound_file.touch()
            
            result = sound_manager._play_sound_file(sound_file)
            
            assert result is True
            mock_subprocess_popen.assert_called_once()
            call_args = mock_subprocess_popen.call_args[0][0]
            assert call_args[0] == "afplay"
            assert call_args[1] == "-v"
            assert call_args[2] == "1.0"
            assert str(sound_file) in call_args[3]

    def test_play_sound_file_quiet_volume(
        self, hooks_dir, mock_subprocess_popen
    ):
        """Test sound file playback with quiet volume (0.1)."""
        with patch.dict("os.environ", {"CLAUDE_CODE_SOUNDS": "0.1"}, clear=False):
            sound_manager = create_sound_manager(str(hooks_dir))
            sound_file = hooks_dir / "sounds" / "beeps" / "ready.wav"
            
            # Create the sound file for the test
            sound_file.parent.mkdir(parents=True, exist_ok=True)
            sound_file.touch()
            
            result = sound_manager._play_sound_file(sound_file)
            
            assert result is True
            mock_subprocess_popen.assert_called_once()
            call_args = mock_subprocess_popen.call_args[0][0]
            assert call_args[0] == "afplay"
            assert call_args[1] == "-v"
            assert call_args[2] == "0.1"
            assert str(sound_file) in call_args[3]


@pytest.mark.integration
class TestSoundManagerIntegration:
    """Test end-to-end sound manager functionality."""

    def test_play_event_sound_integration(
        self, sound_manager_with_mock_sounds, mock_subprocess_popen
    ):
        """Test complete event sound playback flow."""
        cwd = "/test/directory"

        result = sound_manager_with_mock_sounds.play_event_sound("Notification", cwd)

        assert result is True
        mock_subprocess_popen.assert_called_once()

    def test_play_tool_sound_integration(
        self, sound_manager_with_mock_sounds, mock_subprocess_popen
    ):
        """Test complete tool sound playback flow."""
        cwd = "/test/directory"

        result = sound_manager_with_mock_sounds.play_tool_sound("Edit", cwd)

        assert result is True
        mock_subprocess_popen.assert_called_once()

    def test_play_bash_sound_integration(
        self, sound_manager_with_mock_sounds, mock_subprocess_popen
    ):
        """Test complete bash command sound playback flow."""
        cwd = "/test/directory"

        result = sound_manager_with_mock_sounds.play_bash_sound("git commit -m test", cwd)

        assert result is True
        mock_subprocess_popen.assert_called_once()


# Additional fixtures for this test module
@pytest.fixture
def sound_manager_with_real_config(hooks_dir):
    """Create sound manager with real configuration files."""
    return create_sound_manager(str(hooks_dir))


@pytest.fixture
def sound_manager_with_mock_sounds(mock_sounds_dir, sound_mappings_data):
    """Create sound manager with mock sounds directory."""
    # Create a temporary hooks directory with sound_mappings.json
    hooks_dir = mock_sounds_dir.parent.parent
    mappings_file = hooks_dir / "sound_mappings.json"
    with open(mappings_file, "w") as f:
        json.dump(sound_mappings_data, f)
    
    return SoundManager(str(hooks_dir))
