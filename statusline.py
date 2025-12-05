#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""
Custom Claude Code statusline - replicates ccstatusline layout exactly.

Line 1: Model | Ctx: XXk (XX.X%) | ⎇ branch (+X,-Y)
Line 2: XXXk Xhr Xm
"""

import json
import os
import subprocess
import sys
from pathlib import Path

# ANSI color codes (256-color mode to match ccstatusline exactly)
RESET = "\033[39m"  # Reset foreground only (ccstatusline style)
FULL_RESET = "\033[0m"  # Full reset at line start
CYAN = "\033[38;5;30m"  # Model, context percentage, parens
BRIGHT_BLACK = "\033[38;5;245m"  # Context length label
MAGENTA = "\033[38;5;96m"  # Git branch
GRAY = "\033[38;5;188m"  # Spaces/neutral
YELLOW = "\033[38;5;178m"  # Git changes
RED = "\033[38;5;203m"  # Block timer

# Git branch symbol (U+2387 ALTERNATIVE KEY SYMBOL - same as ccstatusline)
GIT_BRANCH_SYMBOL = "⎇"


def format_tokens(count: int) -> str:
    """Format token count as human-readable (e.g., 53.8k, 1.2M)."""
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    elif count >= 1_000:
        return f"{count / 1_000:.1f}k"
    return str(count)


def format_duration(ms: int) -> str:
    """Format milliseconds as human-readable duration (e.g., 4hr 29m)."""
    total_seconds = ms // 1000
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    if hours > 0:
        return f"{hours}hr {minutes}m"
    elif minutes > 0:
        return f"{minutes}m"
    else:
        return f"{total_seconds}s"


def get_git_info(cwd: str) -> tuple[str, str]:
    """Get git branch and changes info."""
    branch = ""
    changes = ""

    try:
        # Check if in git repo
        subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--git-dir"],
            capture_output=True,
            check=True,
            timeout=2,
        )

        # Get branch name
        result = subprocess.run(
            [
                "git",
                "-C",
                cwd,
                "--no-optional-locks",
                "rev-parse",
                "--abbrev-ref",
                "HEAD",
            ],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            branch = result.stdout.strip()

        # Get changes: count added and removed lines
        result = subprocess.run(
            ["git", "-C", cwd, "--no-optional-locks", "diff", "--numstat"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        added, removed = 0, 0
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split("\n"):
                parts = line.split("\t")
                if len(parts) >= 2:
                    try:
                        added += int(parts[0]) if parts[0] != "-" else 0
                        removed += int(parts[1]) if parts[1] != "-" else 0
                    except ValueError:
                        pass

        if added > 0 or removed > 0:
            changes = f"(+{added},-{removed})"
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        pass

    return branch, changes


def parse_transcript(transcript_path: str) -> tuple[int, int]:
    """Parse transcript JSONL to get total tokens and context tokens."""
    total_tokens = 0
    context_tokens = 0  # Last known input tokens (approximates current context)

    if not transcript_path or not Path(transcript_path).exists():
        return 0, 0

    try:
        with open(transcript_path, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get("type") == "assistant":
                        usage = entry.get("message", {}).get("usage", {})
                        input_tokens = usage.get("input_tokens", 0)
                        output_tokens = usage.get("output_tokens", 0)
                        cache_read = usage.get("cache_read_input_tokens", 0)
                        cache_create = usage.get("cache_creation_input_tokens", 0)

                        total_tokens += (
                            input_tokens + output_tokens + cache_read + cache_create
                        )
                        context_tokens = input_tokens + cache_read + cache_create
                except json.JSONDecodeError:
                    continue
    except (IOError, OSError):
        pass

    return total_tokens, context_tokens


def main():
    # Read JSON input from stdin
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("Error: Invalid JSON input", file=sys.stderr)
        sys.exit(1)

    # Extract data from input
    model_name = data.get("model", {}).get("display_name", "Unknown")
    cwd = data.get("workspace", {}).get("current_dir", data.get("cwd", os.getcwd()))
    transcript_path = data.get("transcript_path", "")
    cost = data.get("cost", {})
    duration_ms = cost.get("total_duration_ms", 0)

    # Parse transcript for token data
    total_tokens, context_tokens = parse_transcript(transcript_path)

    # Calculate context percentage (200k context window for Claude)
    max_context = 200_000
    context_pct = (context_tokens / max_context * 100) if context_tokens > 0 else 0

    # Get git info
    branch, changes = get_git_info(cwd)

    # Build Line 1: Model | Ctx: XXk (XX.X%) | ⎇ branch (+X,-Y)
    # Format to match ccstatusline exactly
    ctx_str = format_tokens(context_tokens) if context_tokens > 0 else ""
    pct_str = f"{context_pct:.1f}%" if context_tokens > 0 else ""

    line1 = f"{FULL_RESET}{CYAN}{model_name}{RESET}"
    line1 += f" | {CYAN}Ctx: {ctx_str}{RESET} {CYAN}({pct_str}){RESET}"

    if branch:
        line1 += f" | {MAGENTA}{GIT_BRANCH_SYMBOL} {branch}{RESET}"
        line1 += f"{GRAY} {RESET}"
        if changes:
            line1 += f"{YELLOW}{changes}{RESET}"
        else:
            line1 += f"{YELLOW}(+0,-0){RESET}"

    # Build Line 2: XXXk Xhr Xm
    tokens_str = format_tokens(total_tokens) if total_tokens > 0 else ""
    line2 = f"{FULL_RESET}{GRAY}{tokens_str} {RESET}{RED}{format_duration(duration_ms)}{RESET}"

    # Output both lines
    print(line1)
    print(line2)


if __name__ == "__main__":
    main()
