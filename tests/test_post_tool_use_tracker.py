#!/usr/bin/env python3
"""
Comprehensive test suite for post_tool_use_tracker.sh hook.

This module tests the tracker hook's functionality including:
- JSON input validation and error handling
- Monorepo workspace detection logic
- Command discovery for various project types
- File filtering and path normalization
- Cache operations and logging functionality
- Security validation and error handling
"""

import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


class TestTrackerHookInputValidation:
    """Test JSON input validation and error handling."""

    def test_empty_input(self):
        """Test that empty input is handled gracefully."""
        result = subprocess.run(
            ["bash", "/Users/dlawson/.claude/hooks/post_tool_use_tracker.sh"],
            input="",
            text=True,
            capture_output=True,
        )
        assert result.returncode == 0
        assert result.stderr == ""

    def test_invalid_json_input(self):
        """Test that invalid JSON is handled gracefully."""
        invalid_json = '{"tool_name": "Edit", "tool_input": {"file_path": "test.js"'  # Missing closing brace
        result = subprocess.run(
            ["bash", "/Users/dlawson/.claude/hooks/post_tool_use_tracker.sh"],
            input=invalid_json,
            text=True,
            capture_output=True,
        )
        assert result.returncode == 0
        assert "Invalid JSON input" in result.stderr

    def test_missing_required_fields(self):
        """Test that missing required fields are handled gracefully."""
        incomplete_json = '{"tool_name": "Edit"}'  # Missing file_path
        result = subprocess.run(
            ["bash", "/Users/dlawson/.claude/hooks/post_tool_use_tracker.sh"],
            input=incomplete_json,
            text=True,
            capture_output=True,
        )
        assert result.returncode == 0

    def test_valid_complete_input(self):
        """Test that valid complete input is processed correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test file
            test_file = Path(temp_dir) / "test.js"
            test_file.write_text("console.log('test');")

            valid_input = {
                "tool_name": "Edit",
                "tool_input": {"file_path": str(test_file)},
                "session_id": "test-session-123",
            }

            env = os.environ.copy()
            env["CLAUDE_PROJECT_DIR"] = temp_dir

            result = subprocess.run(
                ["bash", "/Users/dlawson/.claude/hooks/post_tool_use_tracker.sh"],
                input=json.dumps(valid_input),
                text=True,
                capture_output=True,
                env=env,
            )
            assert result.returncode == 0
            assert result.stderr == ""

    def test_unsupported_tool_types(self):
        """Test that unsupported tool types are ignored."""
        unsupported_tools = ["Read", "Bash", "Grep", "Glob", "WebFetch"]

        for tool in unsupported_tools:
            input_data = {
                "tool_name": tool,
                "tool_input": {"file_path": "test.js"},
                "session_id": "test-session",
            }

            result = subprocess.run(
                ["bash", "/Users/dlawson/.claude/hooks/post_tool_use_tracker.sh"],
                input=json.dumps(input_data),
                text=True,
                capture_output=True,
            )
            assert result.returncode == 0


class TestTrackerHookWorkspaceDetection:
    """Test monorepo workspace detection logic."""

    def test_standard_monorepo_structure(self):
        """Test detection of standard monorepo structures."""
        test_cases = [
            ("packages/ui/src/Button.js", "packages/ui"),
            ("apps/web/src/main.js", "apps/web"),
            ("libs/shared/utils.js", "libs/shared"),
            ("services/api/server.js", "services/api"),
            ("examples/basic/index.js", "examples/basic"),
        ]

        for file_path, expected_repo in test_cases:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create directory structure
                full_path = Path(temp_dir) / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text("// test file")

                input_data = {
                    "tool_name": "Edit",
                    "tool_input": {"file_path": file_path},
                    "session_id": "test-session",
                }

                env = os.environ.copy()
                env["CLAUDE_PROJECT_DIR"] = temp_dir

                result = subprocess.run(
                    ["bash", "/Users/dlawson/.claude/hooks/post_tool_use_tracker.sh"],
                    input=json.dumps(input_data),
                    text=True,
                    capture_output=True,
                    env=env,
                )
                assert result.returncode == 0

                # Check if repo was logged correctly
                cache_dir = Path(temp_dir) / ".claude/tsc-cache/test-session"
                affected_repos_file = cache_dir / "affected-repos.log"
                if affected_repos_file.exists():
                    repos = affected_repos_file.read_text().strip().split('\n')
                    assert expected_repo in repos

    def test_top_level_folders(self):
        """Test detection of top-level folders."""
        test_cases = [
            ("frontend/src/App.js", "frontend"),
            ("backend/src/server.js", "backend"),
            ("client/src/index.js", "client"),
            ("server/src/main.js", "server"),
            ("web/src/main.js", "web"),
            ("api/src/routes.js", "api"),
        ]

        for file_path, expected_repo in test_cases:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create directory structure
                full_path = Path(temp_dir) / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text("// test file")

                input_data = {
                    "tool_name": "Edit",
                    "tool_input": {"file_path": file_path},
                    "session_id": "test-session",
                }

                env = os.environ.copy()
                env["CLAUDE_PROJECT_DIR"] = temp_dir

                result = subprocess.run(
                    ["bash", "/Users/dlawson/.claude/hooks/post_tool_use_tracker.sh"],
                    input=json.dumps(input_data),
                    text=True,
                    capture_output=True,
                    env=env,
                )
                assert result.returncode == 0

    def test_root_level_files(self):
        """Test detection of root-level files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a root-level file
            test_file = Path(temp_dir) / "index.js"
            test_file.write_text("// root level file")

            input_data = {
                "tool_name": "Edit",
                "tool_input": {"file_path": "index.js"},
                "session_id": "test-session",
            }

            env = os.environ.copy()
            env["CLAUDE_PROJECT_DIR"] = temp_dir

            result = subprocess.run(
                ["bash", "/Users/dlawson/.claude/hooks/post_tool_use_tracker.sh"],
                input=json.dumps(input_data),
                text=True,
                capture_output=True,
                env=env,
            )
            assert result.returncode == 0


class TestTrackerHookCommandDiscovery:
    """Test command discovery for various project types."""

    def test_package_json_build_script(self):
        """Test discovery of build scripts in package.json."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create package.json with build script
            package_json = {
                "name": "test-package",
                "scripts": {
                    "build": "webpack --mode production",
                    "dev": "webpack serve",
                },
            }

            package_file = Path(temp_dir) / "packages/web/package.json"
            package_file.parent.mkdir(parents=True, exist_ok=True)
            package_file.write_text(json.dumps(package_json))

            # Create a test file
            test_file = Path(temp_dir) / "packages/web/src/main.js"
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text("console.log('test');")

            input_data = {
                "tool_name": "Edit",
                "tool_input": {"file_path": "packages/web/src/main.js"},
                "session_id": "test-session",
            }

            env = os.environ.copy()
            env["CLAUDE_PROJECT_DIR"] = temp_dir

            result = subprocess.run(
                ["bash", "/Users/dlawson/.claude/hooks/post_tool_use_tracker.sh"],
                input=json.dumps(input_data),
                text=True,
                capture_output=True,
                env=env,
            )
            assert result.returncode == 0

            # Check if build command was discovered
            cache_dir = Path(temp_dir) / ".claude/tsc-cache/test-session"
            commands_file = cache_dir / "commands.log"
            if commands_file.exists():
                commands = commands_file.read_text().strip()
                assert "packages/web:build:cd" in commands
                assert "bun run build" in commands

    def test_typescript_projects(self):
        """Test discovery of TypeScript projects."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create tsconfig.json
            tsconfig = {
                "compilerOptions": {
                    "target": "ES2020",
                    "module": "commonjs",
                    "outDir": "./dist",
                },
                "include": ["src/**/*"],
            }

            tsconfig_file = Path(temp_dir) / "packages/backend/tsconfig.json"
            tsconfig_file.parent.mkdir(parents=True, exist_ok=True)
            tsconfig_file.write_text(json.dumps(tsconfig))

            # Create a test file
            test_file = Path(temp_dir) / "packages/backend/src/server.ts"
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text("export class Server {}")

            input_data = {
                "tool_name": "Edit",
                "tool_input": {"file_path": "packages/backend/src/server.ts"},
                "session_id": "test-session",
            }

            env = os.environ.copy()
            env["CLAUDE_PROJECT_DIR"] = temp_dir

            result = subprocess.run(
                ["bash", "/Users/dlawson/.claude/hooks/post_tool_use_tracker.sh"],
                input=json.dumps(input_data),
                text=True,
                capture_output=True,
                env=env,
            )
            assert result.returncode == 0

            # Check if TypeScript command was discovered
            cache_dir = Path(temp_dir) / ".claude/tsc-cache/test-session"
            commands_file = cache_dir / "commands.log"
            if commands_file.exists():
                commands = commands_file.read_text().strip()
                assert "packages/backend:tsc:cd" in commands
                assert "bun run tsc --noEmit" in commands

    def test_prisma_project(self):
        """Test discovery of Prisma projects."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a Prisma schema file
            schema_file = Path(temp_dir) / "database/prisma/schema.prisma"
            schema_file.parent.mkdir(parents=True, exist_ok=True)
            schema_file.write_text("model User { id String @id }")

            input_data = {
                "tool_name": "Edit",
                "tool_input": {"file_path": "database/prisma/schema.prisma"},
                "session_id": "test-session",
            }

            env = os.environ.copy()
            env["CLAUDE_PROJECT_DIR"] = temp_dir

            result = subprocess.run(
                ["bash", "/Users/dlawson/.claude/hooks/post_tool_use_tracker.sh"],
                input=json.dumps(input_data),
                text=True,
                capture_output=True,
                env=env,
            )
            assert result.returncode == 0

            # Check if Prisma command was discovered
            cache_dir = Path(temp_dir) / ".claude/tsc-cache/test-session"
            commands_file = cache_dir / "commands.log"
            if commands_file.exists():
                commands = commands_file.read_text().strip()
                assert "database:build:cd" in commands
                assert "bun x prisma generate" in commands


class TestTrackerHookFileFiltering:
    """Test file filtering and path normalization."""

    def test_excluded_file_types(self):
        """Test that excluded file types are ignored."""
        excluded_extensions = [".md", ".markdown", ".txt", ".json", ".lock", ".log"]

        for ext in excluded_extensions:
            with tempfile.TemporaryDirectory() as temp_dir:
                test_file = Path(temp_dir) / f"test{ext}"
                test_file.write_text("test content")

                input_data = {
                    "tool_name": "Edit",
                    "tool_input": {"file_path": f"test{ext}"},
                    "session_id": "test-session",
                }

                env = os.environ.copy()
                env["CLAUDE_PROJECT_DIR"] = temp_dir

                result = subprocess.run(
                    ["bash", "/Users/dlawson/.claude/hooks/post_tool_use_tracker.sh"],
                    input=json.dumps(input_data),
                    text=True,
                    capture_output=True,
                    env=env,
                )
                assert result.returncode == 0

                # Ensure no cache files were created
                cache_dir = Path(temp_dir) / ".claude/tsc-cache/test-session"
                assert not cache_dir.exists()

    def test_included_file_types(self):
        """Test that code files are processed."""
        included_extensions = [".js", ".ts", ".jsx", ".tsx", ".py", ".go", ".rs"]

        for ext in included_extensions:
            with tempfile.TemporaryDirectory() as temp_dir:
                test_file = Path(temp_dir) / f"test{ext}"
                test_file.write_text("// test code")

                input_data = {
                    "tool_name": "Edit",
                    "tool_input": {"file_path": f"test{ext}"},
                    "session_id": "test-session",
                }

                env = os.environ.copy()
                env["CLAUDE_PROJECT_DIR"] = temp_dir

                result = subprocess.run(
                    ["bash", "/Users/dlawson/.claude/hooks/post_tool_use_tracker.sh"],
                    input=json.dumps(input_data),
                    text=True,
                    capture_output=True,
                    env=env,
                )
                assert result.returncode == 0

                # Ensure cache files were created
                cache_dir = Path(temp_dir) / ".claude/tsc-cache/test-session"
                assert cache_dir.exists()
                assert (cache_dir / "edited-files.log").exists()

    def test_absolute_paths(self):
        """Test handling of absolute file paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.js"
            test_file.write_text("console.log('test');")

            input_data = {
                "tool_name": "Edit",
                "tool_input": {"file_path": str(test_file.absolute())},
                "session_id": "test-session",
            }

            env = os.environ.copy()
            env["CLAUDE_PROJECT_DIR"] = temp_dir

            result = subprocess.run(
                ["bash", "/Users/dlawson/.claude/hooks/post_tool_use_tracker.sh"],
                input=json.dumps(input_data),
                text=True,
                capture_output=True,
                env=env,
            )
            assert result.returncode == 0


class TestTrackerHookSecurity:
    """Test security validation and error handling."""

    def test_path_traversal_attempts(self):
        """Test that path traversal attempts are blocked."""
        path_traversal_attempts = [
            "../../../etc/passwd",
            "../../secrets.txt",
            "/etc/passwd",
            "~/.ssh/id_rsa",
        ]

        for malicious_path in path_traversal_attempts:
            input_data = {
                "tool_name": "Edit",
                "tool_input": {"file_path": malicious_path},
                "session_id": "test-session",
            }

            result = subprocess.run(
                ["bash", "/Users/dlawson/.claude/hooks/post_tool_use_tracker.sh"],
                input=json.dumps(input_data),
                text=True,
                capture_output=True,
            )
            assert result.returncode == 0
            # Should exit early without processing

    def test_files_outside_project_bounds(self):
        """Test that files outside project bounds are ignored."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a file outside the project directory
            outside_file = Path(temp_dir).parent / "outside.js"
            outside_file.write_text("// outside file")

            input_data = {
                "tool_name": "Edit",
                "tool_input": {"file_path": str(outside_file)},
                "session_id": "test-session",
            }

            env = os.environ.copy()
            env["CLAUDE_PROJECT_DIR"] = temp_dir

            result = subprocess.run(
                ["bash", "/Users/dlawson/.claude/hooks/post_tool_use_tracker.sh"],
                input=json.dumps(input_data),
                text=True,
                capture_output=True,
                env=env,
            )
            assert result.returncode == 0

    def test_nonexistent_files(self):
        """Test that nonexistent files are handled gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nonexistent_file = "does-not-exist.js"

            input_data = {
                "tool_name": "Edit",
                "tool_input": {"file_path": nonexistent_file},
                "session_id": "test-session",
            }

            env = os.environ.copy()
            env["CLAUDE_PROJECT_DIR"] = temp_dir

            result = subprocess.run(
                ["bash", "/Users/dlawson/.claude/hooks/post_tool_use_tracker.sh"],
                input=json.dumps(input_data),
                text=True,
                capture_output=True,
                env=env,
            )
            assert result.returncode == 0


class TestTrackerHookCacheOperations:
    """Test cache operations and logging functionality."""

    def test_cache_directory_creation(self):
        """Test that cache directories are created correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.js"
            test_file.write_text("console.log('test');")

            input_data = {
                "tool_name": "Edit",
                "tool_input": {"file_path": "test.js"},
                "session_id": "test-session-123",
            }

            env = os.environ.copy()
            env["CLAUDE_PROJECT_DIR"] = temp_dir

            result = subprocess.run(
                ["bash", "/Users/dlawson/.claude/hooks/post_tool_use_tracker.sh"],
                input=json.dumps(input_data),
                text=True,
                capture_output=True,
                env=env,
            )
            assert result.returncode == 0

            # Check cache directory structure
            cache_dir = Path(temp_dir) / ".claude/tsc-cache/test-session-123"
            assert cache_dir.exists()
            assert cache_dir.is_dir()

    def test_log_file_creation_and_content(self):
        """Test that log files are created with correct content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.js"
            test_file.write_text("console.log('test');")

            session_id = "test-session-123"
            input_data = {
                "tool_name": "Edit",
                "tool_input": {"file_path": "test.js"},
                "session_id": session_id,
            }

            env = os.environ.copy()
            env["CLAUDE_PROJECT_DIR"] = temp_dir

            result = subprocess.run(
                ["bash", "/Users/dlawson/.claude/hooks/post_tool_use_tracker.sh"],
                input=json.dumps(input_data),
                text=True,
                capture_output=True,
                env=env,
            )
            assert result.returncode == 0

            cache_dir = Path(temp_dir) / ".claude/tsc-cache" / session_id

            # Check edited-files.log
            edited_files = cache_dir / "edited-files.log"
            assert edited_files.exists()
            content = edited_files.read_text()
            assert "test.js" in content
            assert "root" in content  # Should detect as root-level file

            # Check affected-repos.log
            affected_repos = cache_dir / "affected-repos.log"
            assert affected_repos.exists()
            repos_content = affected_repos.read_text()
            assert "root" in repos_content

    def test_session_isolation(self):
        """Test that different sessions are isolated."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.js"
            test_file.write_text("console.log('test');")

            sessions = ["session-1", "session-2"]

            for session_id in sessions:
                input_data = {
                    "tool_name": "Edit",
                    "tool_input": {"file_path": "test.js"},
                    "session_id": session_id,
                }

                env = os.environ.copy()
                env["CLAUDE_PROJECT_DIR"] = temp_dir

                result = subprocess.run(
                    ["bash", "/Users/dlawson/.claude/hooks/post_tool_use_tracker.sh"],
                    input=json.dumps(input_data),
                    text=True,
                    capture_output=True,
                    env=env,
                )
                assert result.returncode == 0

            # Verify both session directories exist
            cache_dir = Path(temp_dir) / ".claude/tsc-cache"
            for session_id in sessions:
                session_cache = cache_dir / session_id
                assert session_cache.exists()
                assert (session_cache / "edited-files.log").exists()


class TestTrackerHookIntegration:
    """Integration testing with other hooks."""

    def test_compatibility_with_code_quality_hook(self):
        """Test compatibility with code_quality.py hook."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.js"
            test_file.write_text("console.log('test');")

            # Test input that would go to both hooks
            input_data = {
                "tool_name": "Edit",
                "tool_input": {"file_path": "test.js"},
                "session_id": "integration-test",
            }

            env = os.environ.copy()
            env["CLAUDE_PROJECT_DIR"] = temp_dir

            # Test tracker hook
            tracker_result = subprocess.run(
                ["bash", "/Users/dlawson/.claude/hooks/post_tool_use_tracker.sh"],
                input=json.dumps(input_data),
                text=True,
                capture_output=True,
                env=env,
            )
            assert tracker_result.returncode == 0

            # Test code quality hook
            quality_result = subprocess.run(
                ["python", "/Users/dlawson/.claude/hooks/code_quality.py"],
                input=json.dumps(input_data),
                text=True,
                capture_output=True,
                env=env,
            )
            # Code quality hook might fail due to missing dependencies, but should not crash

    def test_performance_with_multiple_edits(self):
        """Test performance impact with multiple file edits."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create multiple test files
            test_files = []
            for i in range(10):
                test_file = Path(temp_dir) / f"test{i}.js"
                test_file.write_text(f"console.log('test {i}');")
                test_files.append(test_file)

            start_time = time.time()

            for i, test_file in enumerate(test_files):
                input_data = {
                    "tool_name": "Edit",
                    "tool_input": {"file_path": f"test{i}.js"},
                    "session_id": "perf-test",
                }

                env = os.environ.copy()
                env["CLAUDE_PROJECT_DIR"] = temp_dir

                result = subprocess.run(
                    ["bash", "/Users/dlawson/.claude/hooks/post_tool_use_tracker.sh"],
                    input=json.dumps(input_data),
                    text=True,
                    capture_output=True,
                    env=env,
                )
                assert result.returncode == 0

            end_time = time.time()
            execution_time = end_time - start_time

            # Should complete all 10 operations within reasonable time
            assert execution_time < 5.0, f"Too slow: {execution_time:.2f}s for 10 operations"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])