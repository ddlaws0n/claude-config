#!/usr/bin/env python3
"""
Sound Manager for Claude Code hooks using cchooks.

Provides contextual audio feedback for development events and actions.
Supports tool-specific sounds, bash command pattern matching, and project overrides.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


class SoundManager:
    """Manages sound playback for Claude Code hooks."""
    
    def __init__(self, hooks_dir: str | None = None):
        """Initialize sound manager with hooks directory path."""
        self.hooks_dir = Path(hooks_dir) if hooks_dir else Path(__file__).parent.parent
        self.sounds_dir = self.hooks_dir / "sounds" / "beeps"
        self.mappings_file = self.hooks_dir / "sound_mappings.json"
        self.mappings = self._load_sound_mappings()
        self.volume = self._get_volume_setting()
        
    def _load_sound_mappings(self) -> dict[str, Any]:
        """Load sound mappings from configuration file."""
        try:
            with open(self.mappings_file) as f:
                data: dict[str, Any] = json.load(f)
                return data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load sound mappings: {e}", file=sys.stderr)
            return {"events": {}, "tools": {}, "bash_patterns": []}
    
    def _get_volume_setting(self) -> float:
        """Get volume setting from environment variable."""
        env_value = os.environ.get("CLAUDE_CODE_SOUNDS", "1.0").strip()
        
        # Handle empty string as default enabled
        if not env_value:
            return 1.0
            
        try:
            volume = float(env_value)
            # Clamp volume to valid range (0.0 to 1.0)
            volume = max(0.0, min(1.0, volume))
            return volume
        except ValueError:
            print(f"Warning: Invalid CLAUDE_CODE_SOUNDS value '{env_value}', using default volume 1.0", file=sys.stderr)
            return 1.0
    
    def _get_project_overrides(self, cwd: str) -> dict[str, Any]:
        """Load project-specific sound overrides if available."""
        project_config = Path(cwd) / ".claude-sounds"
        if not project_config.exists():
            return {}
            
        try:
            with open(project_config) as f:
                data: dict[str, Any] = json.load(f)
                return data
        except (json.JSONDecodeError, OSError):
            return {}
    
    def _find_sound_file(self, sound_name: str, project_overrides: dict[str, Any] | None = None) -> Path | None:
        """Find sound file with support for project overrides."""
        project_overrides = project_overrides or {}
        
        # Check for custom mapping first
        if "custom_mappings" in project_overrides:
            custom_sound = project_overrides["custom_mappings"].get(sound_name)
            if custom_sound:
                sound_name = custom_sound
        
        # Look for sound file with common extensions
        for ext in [".wav", ".mp3", ".aiff", ".m4a"]:
            sound_file = self.sounds_dir / f"{sound_name}{ext}"
            if sound_file.exists():
                return sound_file
                
        return None
    
    def _match_bash_pattern(self, command: str, project_overrides: dict[str, Any] | None = None) -> str | None:
        """Match bash command against patterns to determine appropriate sound."""
        project_overrides = project_overrides or {}
        
        # Check project-specific bash patterns first
        if "custom_mappings" in project_overrides and "bash_patterns" in project_overrides["custom_mappings"]:
            for pattern_data in project_overrides["custom_mappings"]["bash_patterns"]:
                if isinstance(pattern_data, list) and len(pattern_data) >= 2:
                    pattern, sound = pattern_data[0], pattern_data[1]
                    if re.match(str(pattern), command):
                        return str(sound)
        
        # Check default bash patterns
        for pattern_data in self.mappings.get("bash_patterns", []):
            if isinstance(pattern_data, dict):
                pattern = pattern_data.get("pattern", "")
                sound = pattern_data.get("sound", "")
                if pattern and sound and re.match(pattern, command):
                    return str(sound)
        
        return None
    
    def _play_sound_file(self, sound_file: Path) -> bool:
        """Play sound file using macOS afplay with volume control."""
        # Early return if sounds are disabled (volume = 0)
        if self.volume == 0.0:
            return False
            
        try:
            # Use afplay for macOS with volume control - run in background without waiting
            subprocess.Popen(
                ["afplay", "-v", str(self.volume), str(sound_file)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except (OSError, FileNotFoundError) as e:
            print(f"Warning: Could not play sound {sound_file}: {e}", file=sys.stderr)
            return False
    
    def play_event_sound(self, event_name: str, cwd: str = ".") -> bool:
        """Play sound for a specific event (Notification, Stop, etc.)."""
        project_overrides = self._get_project_overrides(cwd)
        
        # Get sound name from event mapping
        sound_name = self.mappings.get("events", {}).get(event_name)
        if not sound_name:
            return False
            
        # Find and play sound file
        sound_file = self._find_sound_file(sound_name, project_overrides)
        if sound_file:
            return self._play_sound_file(sound_file)
            
        return False
    
    def play_tool_sound(self, tool_name: str, cwd: str = ".") -> bool:
        """Play sound for a specific tool (Write, Edit, etc.)."""
        project_overrides = self._get_project_overrides(cwd)
        
        # Get sound name from tool mapping
        sound_name = self.mappings.get("tools", {}).get(tool_name)
        if not sound_name:
            return False
            
        # Find and play sound file
        sound_file = self._find_sound_file(sound_name, project_overrides)
        if sound_file:
            return self._play_sound_file(sound_file)
            
        return False
    
    def play_bash_sound(self, command: str, cwd: str = ".") -> bool:
        """Play sound for bash command based on pattern matching."""
        project_overrides = self._get_project_overrides(cwd)
        
        # Match command against patterns
        sound_name = self._match_bash_pattern(command, project_overrides)
        if not sound_name:
            return False
            
        # Find and play sound file
        sound_file = self._find_sound_file(sound_name, project_overrides)
        if sound_file:
            return self._play_sound_file(sound_file)
            
        return False


    def _get_event_sound(self, event_name: str) -> Path | None:
        """Get sound file for event (testing helper)."""
        sound_name = self.mappings.get("events", {}).get(event_name)
        if not sound_name:
            return None
        return self._find_sound_file(sound_name)
    
    def _get_tool_sound(self, tool_name: str) -> Path | None:
        """Get sound file for tool (testing helper)."""
        sound_name = self.mappings.get("tools", {}).get(tool_name)
        if not sound_name:
            return None
        return self._find_sound_file(sound_name)
    
    def _get_bash_sound(self, command: str) -> Path | None:
        """Get sound file for bash command (testing helper)."""
        sound_name = self._match_bash_pattern(command)
        if not sound_name:
            return None
        return self._find_sound_file(sound_name)
    
    def _load_project_overrides(self, cwd: str) -> dict | None:
        """Load project overrides (testing helper - alias for _get_project_overrides)."""
        overrides = self._get_project_overrides(cwd)
        return overrides if overrides else None


def create_sound_manager(hooks_dir: str | None = None) -> SoundManager:
    """Factory function to create a SoundManager instance."""
    return SoundManager(hooks_dir)