#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///

"""
TypeCheck Hook for Claude Code Stop Event

Runs comprehensive type checking when the agent finishes working.
- TypeScript: Runs tsc --noEmit on project
- Python: Runs mypy on project
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_typecheck(name: str, cmd_args: list[str], cwd: str) -> tuple[bool, str]:
    """
    Run a typecheck command and return (success, error_message).
    """
    exe = cmd_args[0]

    # Check if executable exists
    if not shutil.which(exe) and not os.path.exists(os.path.join(cwd, exe)):
        print(f"⚠️  {name.upper()} SKIPPED: Command '{exe}' not found", file=sys.stderr)
        return True, ""

    try:
        result = subprocess.run(
            cmd_args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        if result.returncode != 0:
            stderr_output = result.stderr.strip()
            stdout_output = result.stdout.strip()

            # Combine outputs for error message
            output = f"❌ {name.upper()} FAILED:\n{stdout_output}\n{stderr_output}".strip()
            return False, output

        return True, ""

    except subprocess.TimeoutExpired:
        return False, f"❌ {name.upper()} TIMEOUT: Type checking took longer than 5 minutes"
    except Exception as e:
        print(f"⚠️  {name.upper()} ERROR: {e}", file=sys.stderr)
        return True, ""  # Fail open on unexpected errors


def check_typescript_project(project_dir: Path) -> tuple[bool, str]:
    """Check if this is a TypeScript project and run tsc if so."""
    tsconfig_files = [
        "tsconfig.json",
        "tsconfig.build.json",
        "tsconfig.app.json",
    ]

    # Find which tsconfig exists
    tsconfig = None
    for config in tsconfig_files:
        if (project_dir / config).exists():
            tsconfig = config
            break

    if not tsconfig:
        return True, ""  # No TypeScript config, skip

    # Build tsc command
    if tsconfig == "tsconfig.json":
        cmd = ["bun", "run", "tsc", "--noEmit"]
    else:
        cmd = ["bun", "run", "tsc", "--project", tsconfig, "--noEmit"]

    print(f"🔍 Running TypeScript type check on {project_dir.name}...", file=sys.stderr)
    return run_typecheck("typescript", cmd, str(project_dir))


def check_python_project(project_dir: Path) -> tuple[bool, str]:
    """Check if this is a Python project and run mypy if so."""

    # Check for Python files or common Python project indicators
    has_python = (
        list(project_dir.glob("**/*.py")) or
        (project_dir / "pyproject.toml").exists() or
        (project_dir / "setup.py").exists()
    )

    if not has_python:
        return True, ""  # No Python project, skip

    # Run mypy on project root
    cmd = ["uv", "run", "mypy", "."]

    print(f"🔍 Running Python type check on {project_dir.name}...", file=sys.stderr)
    return run_typecheck("python", cmd, str(project_dir))


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    # Get project directory
    cwd = input_data.get("cwd", ".")
    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", cwd))

    # Check if stop_hook_active to avoid infinite loops
    if input_data.get("stop_hook_active", False):
        print("⚠️  Stop hook already active, skipping typecheck", file=sys.stderr)
        sys.exit(0)

    errors = []

    # Run TypeScript type check
    success, error = check_typescript_project(project_dir)
    if not success:
        errors.append(error)

    # Run Python type check
    success, error = check_python_project(project_dir)
    if not success:
        errors.append(error)

    # Report errors if any
    if errors:
        output = {
            "decision": "block",
            "reason": "\n\n".join(errors),
            "hookSpecificOutput": {
                "hookEventName": "Stop",
            },
        }
        print(json.dumps(output))
        sys.exit(0)

    # Success - let Claude stop
    print("✅ Type checking passed", file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()
