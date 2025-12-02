#!/usr/bin/env python3
"""
Configuration validation and health checking system for Claude Code hooks.

This module provides comprehensive validation of hook configurations, dependencies,
and system health. It ensures all hooks are properly configured and executable.
"""

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ConfigurationValidator:
    """Validates Claude Code hook configuration and system health."""

    def __init__(self, project_dir: Optional[str] = None):
        """Initialize validator with project directory."""
        self.project_dir = Path(project_dir) if project_dir else Path.cwd()
        self.hooks_dir = self.project_dir / ".claude" / "hooks"
        self.settings_file = self.project_dir / ".claude" / "settings.json"
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """
        Perform comprehensive validation of the entire hook system.

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []

        # Validate configuration file
        self._validate_settings_file()

        # Validate hook files
        if self.settings_file.exists():
            self._validate_hook_configuration()

        # Validate dependencies
        self._validate_dependencies()

        # Validate permissions
        self._validate_permissions()

        return len(self.errors) == 0, self.errors, self.warnings

    def _validate_settings_file(self):
        """Validate the settings.json file."""
        if not self.settings_file.exists():
            self.errors.append(f"Settings file not found: {self.settings_file}")
            return

        try:
            with open(self.settings_file, "r") as f:
                settings = json.load(f)

            if not isinstance(settings, dict):
                self.errors.append("Settings file must be a JSON object")
                return

            # Validate hooks configuration
            if "hooks" in settings:
                hooks_config = settings["hooks"]
                if not isinstance(hooks_config, dict):
                    self.errors.append("'hooks' configuration must be a JSON object")
                else:
                    self._validate_hooks_structure(hooks_config)

        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in settings file: {e}")
        except Exception as e:
            self.errors.append(f"Error reading settings file: {e}")

    def _validate_hooks_structure(self, hooks_config: Dict):
        """Validate the structure of hooks configuration."""
        valid_events = [
            "PreToolUse",
            "PostToolUse",
            "PermissionRequest",
            "Notification",
            "UserPromptSubmit",
            "Stop",
            "SubagentStop",
            "PreCompact",
            "SessionStart",
            "SessionEnd",
        ]

        for event, hook_configs in hooks_config.items():
            if event not in valid_events:
                self.warnings.append(f"Unknown hook event: {event}")
                continue

            if not isinstance(hook_configs, list):
                self.errors.append(f"Hook configuration for '{event}' must be a list")
                continue

            for i, hook_config in enumerate(hook_configs):
                self._validate_individual_hook(event, hook_config, i)

    def _validate_individual_hook(self, event: str, hook_config: Dict, index: int):
        """Validate an individual hook configuration."""
        if not isinstance(hook_config, dict):
            self.errors.append(f"Hook {index} for '{event}' must be a JSON object")
            return

        # Validate matcher (optional for some events)
        if "matcher" in hook_config:
            matcher = hook_config["matcher"]
            if not isinstance(matcher, str):
                self.errors.append(
                    f"Matcher for hook {index} in '{event}' must be a string"
                )

        # Validate hooks array
        if "hooks" not in hook_config:
            self.errors.append(f"Missing 'hooks' array in hook {index} for '{event}'")
            return

        hooks = hook_config["hooks"]
        if not isinstance(hooks, list):
            self.errors.append(f"'hooks' must be a list in hook {index} for '{event}'")
            return

        for j, hook in enumerate(hooks):
            self._validate_hook_command(event, hook, index, j)

    def _validate_hook_command(
        self, event: str, hook: Dict, config_index: int, hook_index: int
    ):
        """Validate a hook command configuration."""
        if not isinstance(hook, dict):
            self.errors.append(
                (
                    f"Hook {hook_index} in config {config_index} for '{event}'"
                    + "must be a JSON object"
                )
            )
            return

        # Validate type
        if "type" not in hook:
            self.errors.append(f"Missing 'type' in hook {hook_index} for '{event}'")
            return

        hook_type = hook["type"]
        if hook_type not in ["command", "prompt"]:
            self.errors.append(
                f"Invalid hook type '{hook_type}' in hook {hook_index} for '{event}'"
            )
            return

        # For command hooks, validate command
        if hook_type == "command":
            if "command" not in hook:
                self.errors.append(
                    f"Missing 'command' in command hook {hook_index} for '{event}'"
                )
                return

            command = hook["command"]
            if not isinstance(command, str):
                self.errors.append(
                    f"Command must be a string in hook {hook_index} for '{event}'"
                )
                return

            # Validate timeout if present
            if "timeout" in hook:
                timeout = hook["timeout"]
                if not isinstance(timeout, (int, float)) or timeout <= 0:
                    self.errors.append(
                        (
                            "Timeout must be a positive number in hook "
                            + f"{hook_index} for '{event}'"
                        )
                    )

    def _validate_hook_configuration(self):
        """Validate hook files referenced in configuration."""
        try:
            with open(self.settings_file, "r") as f:
                settings = json.load(f)

            hooks_config = settings.get("hooks", {})

            for event, hook_configs in hooks_config.items():
                for hook_config in hook_configs:
                    self._validate_hook_files(hook_config)

        except Exception as e:
            self.errors.append(f"Error validating hook configuration: {e}")

    def _validate_hook_files(self, hook_config: Dict):
        """Validate that hook files exist and are executable."""
        hooks = hook_config.get("hooks", [])

        for hook in hooks:
            if hook.get("type") == "command":
                command = hook.get("command", "")

                # Expand environment variables and resolve paths
                command = os.path.expandvars(command)

                # Extract file path from command (simple heuristic)
                # Look for common patterns like "/path/to/script.py" or "python /path/to/script"
                parts = command.split()
                script_path = None

                for part in parts:
                    if "/" in part and not part.startswith("-"):
                        script_path = part
                        break

                if script_path:
                    # Resolve relative paths
                    if script_path.startswith('"$CLAUDE_PROJECT_DIR"'):
                        script_path = script_path.replace(
                            '"$CLAUDE_PROJECT_DIR"', str(self.project_dir)
                        )
                    elif script_path.startswith("~"):
                        script_path = Path(script_path).expanduser()
                    elif not script_path.startswith("/"):
                        script_path = self.project_dir / script_path

                    script_path = Path(str(script_path).strip("\"'"))

                    if not script_path.exists():
                        self.errors.append(f"Hook script not found: {script_path}")
                    elif not os.access(script_path, os.X_OK) and script_path.suffix in [
                        ".py",
                        ".sh",
                    ]:
                        self.warnings.append(
                            f"Hook script may not be executable: {script_path}"
                        )

    def _validate_dependencies(self):
        """Validate required dependencies for hooks."""
        required_tools = {
            "python": ["python3", "python"],
            "jq": ["jq"],
            "bun": ["bun"],
            "node": ["node", "nodejs"],
            "npm": ["npm"],
        }

        for tool_name, commands in required_tools.items():
            if not self._check_command_exists(commands):
                # Check if any hooks require this tool
                if self._tool_needed_by_hooks(tool_name):
                    self.warnings.append(f"Required tool '{tool_name}' not found in PATH")

    def _check_command_exists(self, commands: List[str]) -> bool:
        """Check if any of the given commands exist."""
        for cmd in commands:
            if shutil.which(cmd):
                return True
        return False

    def _tool_needed_by_hooks(self, tool_name: str) -> bool:
        """Check if any hooks require the specified tool."""
        try:
            with open(self.settings_file, "r") as f:
                settings = json.load(f)

            hooks_config = settings.get("hooks", {})

            for event, hook_configs in hooks_config.items():
                for hook_config in hook_configs:
                    hooks = hook_config.get("hooks", [])
                    for hook in hooks:
                        command = hook.get("command", "")

                        # Simple heuristic to check if tool is needed
                        if tool_name == "python" and (
                            ".py" in command or "python" in command
                        ):
                            return True
                        elif tool_name == "jq" and "jq" in command:
                            return True
                        elif tool_name == "bun" and "bun" in command:
                            return True
                        elif tool_name == "node" and (
                            "node" in command or "npm" in command
                        ):
                            return True

        except Exception:
            pass

        return False

    def _validate_permissions(self):
        """Validate file and directory permissions."""
        # Check .claude directory permissions
        claude_dir = self.project_dir / ".claude"
        if claude_dir.exists():
            if not os.access(claude_dir, os.R_OK | os.W_OK | os.X_OK):
                self.warnings.append(
                    f".claude directory may have permission issues: {claude_dir}"
                )

        # Check hooks directory permissions
        if self.hooks_dir.exists():
            if not os.access(self.hooks_dir, os.R_OK | os.X_OK):
                self.warnings.append(
                    f"hooks directory may have permission issues: {self.hooks_dir}"
                )

        # Check individual hook file permissions
        for hook_file in self.hooks_dir.glob("*.py"):
            if not os.access(hook_file, os.R_OK):
                self.warnings.append(f"Hook file not readable: {hook_file}")

        for hook_file in self.hooks_dir.glob("*.sh"):
            if not os.access(hook_file, os.R_OK):
                self.warnings.append(f"Hook file not readable: {hook_file}")
            elif not os.access(hook_file, os.X_OK):
                self.warnings.append(f"Shell hook file not executable: {hook_file}")


def print_validation_results(is_valid: bool, errors: List[str], warnings: List[str]):
    """Print validation results in a formatted way."""
    if is_valid:
        print("✅ Hook system validation passed")
    else:
        print("❌ Hook system validation failed")

    if errors:
        print("\n🚨 Errors:")
        for error in errors:
            print(f"  • {error}")

    if warnings:
        print("\n⚠️  Warnings:")
        for warning in warnings:
            print(f"  • {warning}")

    if not errors and not warnings:
        print("✨ No issues found")


def main():
    """Main function for running validation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate Claude Code hook configuration"
    )
    parser.add_argument(
        "--project-dir",
        help="Project directory (default: current directory)",
        default=None,
    )
    parser.add_argument(
        "--json", action="store_true", help="Output results in JSON format"
    )
    parser.add_argument(
        "--fix-permissions",
        action="store_true",
        help="Attempt to fix file permission issues",
    )

    args = parser.parse_args()

    validator = ConfigurationValidator(args.project_dir)
    is_valid, errors, warnings = validator.validate_all()

    if args.fix_permissions:
        # Attempt to fix permission issues
        fixed_count = 0
        claude_dir = Path(args.project_dir or ".") / ".claude"

        # Make shell scripts executable
        for hook_file in claude_dir.glob("hooks/*.sh"):
            if hook_file.exists() and not os.access(hook_file, os.X_OK):
                try:
                    hook_file.chmod(0o755)
                    fixed_count += 1
                    print(f"Fixed permissions: {hook_file}")
                except Exception as e:
                    print(f"Failed to fix permissions for {hook_file}: {e}")

        if fixed_count > 0:
            print(f"Fixed permissions for {fixed_count} files")

    if args.json:
        result = {"valid": is_valid, "errors": errors, "warnings": warnings}
        print(json.dumps(result, indent=2))
    else:
        print_validation_results(is_valid, errors, warnings)

    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
