#!/usr/bin/env python3
"""
Code formatting utilities for Claude Code hooks.
Supports multiple languages and formatting tools.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


class FormatterBase:
    """Base class for code formatters."""

    def __init__(self, tool: str, check_only: bool = False):
        self.tool = tool
        self.check_only = check_only

    def is_available(self) -> bool:
        """Check if the formatter tool is available."""
        return shutil.which(self.tool) is not None

    def format_file(self, file_path: str) -> Tuple[bool, str]:
        """Format a single file. Returns (success, output)."""
        raise NotImplementedError

    def check_format(self, file_path: str) -> Tuple[bool, str]:
        """Check if file is properly formatted. Returns (success, output)."""
        raise NotImplementedError


class RuffFormatter(FormatterBase):
    """Python formatter using ruff."""

    def __init__(self, check_only: bool = False):
        super().__init__("uv", check_only)

    def is_available(self) -> bool:
        """Check if uv and ruff are available."""
        return super().is_available() and self._check_ruff()

    def _check_ruff(self) -> bool:
        """Check if ruff is available in the project."""
        try:
            result = subprocess.run(
                ["uv", "run", "ruff", "--version"], capture_output=True, text=True
            )
            return result.returncode == 0
        except Exception:  # noqa: BLE001
            return False

    def format_file(self, file_path: str) -> Tuple[bool, str]:
        """Format Python file with ruff."""
        cmd = ["uv", "run", "ruff", "format", file_path]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0, result.stderr
        except Exception as e:
            return False, str(e)

    def check_format(self, file_path: str) -> Tuple[bool, str]:
        """Check if Python file is formatted with ruff."""
        cmd = ["uv", "run", "ruff", "format", "--check", file_path]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0, result.stderr
        except Exception as e:
            return False, str(e)

    def lint_file(self, file_path: str) -> Tuple[bool, str]:
        """Lint Python file with ruff."""
        cmd = ["uv", "run", "ruff", "check", "--fix", file_path]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0, result.stderr
        except Exception as e:
            return False, str(e)


class BiomeFormatter(FormatterBase):
    """JavaScript/TypeScript formatter using Biome."""

    def __init__(self, check_only: bool = False):
        super().__init__("biome", check_only)

    def format_file(self, file_path: str) -> Tuple[bool, str]:
        """Format file with Biome."""
        cmd = ["biome", "check", "--write", "--unsafe", file_path]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0, result.stderr
        except Exception as e:
            return False, str(e)

    def check_format(self, file_path: str) -> Tuple[bool, str]:
        """Check if file is formatted with Biome."""
        cmd = ["biome", "check", file_path]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0, result.stderr
        except Exception as e:
            return False, str(e)

    def lint_file(self, file_path: str) -> Tuple[bool, str]:
        """Lint file with Biome."""
        cmd = ["biome", "lint", file_path]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0, result.stderr
        except Exception as e:
            return False, str(e)


class PrettierFormatter(FormatterBase):
    """Generic formatter using Prettier."""

    def __init__(self, check_only: bool = False):
        super().__init__("prettier", check_only)

    def format_file(self, file_path: str) -> Tuple[bool, str]:
        """Format file with Prettier."""
        cmd = ["prettier", "--write", file_path]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0, result.stderr
        except Exception as e:
            return False, str(e)

    def check_format(self, file_path: str) -> Tuple[bool, str]:
        """Check if file is formatted with Prettier."""
        cmd = ["prettier", "--check", file_path]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0, result.stderr
        except Exception as e:
            return False, str(e)


class ESLintFormatter(FormatterBase):
    """JavaScript/TypeScript linter using ESLint."""

    def __init__(self):
        super().__init__("eslint")

    def is_available(self) -> bool:
        """Check if ESLint is available."""
        # Check for eslint command
        if super().is_available():
            return True

        # Check for local installation
        return os.path.exists("./node_modules/.bin/eslint")

    def lint_file(self, file_path: str) -> Tuple[bool, str]:
        """Lint file with ESLint."""
        # Try local ESLint first
        if os.path.exists("./node_modules/.bin/eslint"):
            cmd = ["./node_modules/.bin/eslint", file_path]
        else:
            cmd = ["eslint", file_path]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0, result.stderr
        except Exception as e:
            return False, str(e)


class ShellCheckFormatter(FormatterBase):
    """Shell script linter using ShellCheck."""

    def __init__(self):
        super().__init__("shellcheck")

    def lint_file(self, file_path: str) -> Tuple[bool, str]:
        """Check shell script with ShellCheck."""
        cmd = ["shellcheck", file_path]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0, result.stderr
        except Exception as e:
            return False, str(e)


def detect_markdown_language(code: str) -> str:
    """
    Detect programming language in code block.

    Args:
        code: Code content to analyze

    Returns:
        Detected language string
    """
    import re

    s = code.strip()

    # JSON detection
    if re.search(r"^\s*[{\[]", s):
        try:
            import json

            json.loads(s)
            return "json"
        except Exception:  # noqa: BLE001
            pass

    # YAML detection
    if re.search(r"^[a-zA-Z_]+:", s, re.MULTILINE):
        return "yaml"

    # Python detection
    if (
        re.search(r"^\s*def\s+\w+\s*\(", s, re.MULTILINE)
        or re.search(r"^\s*(import|from)\s+\w+", s, re.MULTILINE)
        or re.search(r"^\s*class\s+\w+", s, re.MULTILINE)
    ):
        return "python"

    # JavaScript/TypeScript detection
    if (
        re.search(r"\b(function\s+\w+\s*\(|const\s+\w+\s*=)", s)
        or re.search(r"=>", s)
        or re.search(r"console\.(log|error)", s)
        or re.search(r"\b(var|let|const)\s+\w+\s*=", s)
    ):
        return "javascript"

    # TypeScript detection (JavaScript + type annotations)
    if re.search(r":\s*(string|number|boolean|void)", s) or re.search(
        r"<[^>]+>(?!\s*>)", s
    ):  # Generic syntax
        return "typescript"

    # Bash detection
    if (
        re.search(r"#!.*\b(bash|sh)\b", s, re.MULTILINE)
        or re.search(r"\b(if|then|fi|for|in|do|done)\b", s)
        or re.search(r"\$\{?\w+\}?", s)
    ):
        return "bash"

    # SQL detection
    if re.search(
        r"\b(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)\s+", s, re.IGNORECASE
    ):
        return "sql"

    # Go detection
    if (
        re.search(r"func\s+\w+\(", s)
        or re.search(r"package\s+main", s)
        or re.search(r"import\s*\(", s)
    ):
        return "go"

    # Rust detection
    if (
        re.search(r"fn\s+\w+\(", s)
        or re.search(r"use\s+std::", s)
        or re.search(r"impl\s+\w+", s)
    ):
        return "rust"

    # HTML detection
    if re.search(r"<[a-zA-Z][^>]*>", s):
        return "html"

    # CSS detection
    if re.search(r"[a-zA-Z-]+\s*:\s*[^;]+;", s):
        return "css"

    return "text"


def format_markdown_fences(content: str) -> str:
    """
    Fix markdown code fences by adding language tags.

    Args:
        content: Markdown content to format

    Returns:
        Formatted markdown content
    """
    import re

    def add_lang_to_fence(match):
        indent, info, body, closing = match.groups()
        if not info.strip():
            lang = detect_markdown_language(body)
            return f"{indent}```{lang}\n{body}{closing}\n"
        return match.group(0)

    fence_pattern = r"(?ms)^([ \t]{0,3})```([^\n]*)\n(.*?)(\n\1```)\s*$"
    formatted = re.sub(fence_pattern, add_lang_to_fence, content)

    # Fix excessive blank lines outside code fences
    formatted = re.sub(r"\n{3,}", "\n\n", formatted)

    return formatted.rstrip() + "\n"


def get_formatter_for_file(file_path: str) -> Optional[FormatterBase]:
    """
    Get appropriate formatter for a file.

    Args:
        file_path: Path to file

    Returns:
        Formatter instance or None
    """
    ext = Path(file_path).suffix.lower()

    # Python
    if ext == ".py":
        if RuffFormatter().is_available():
            return RuffFormatter()

    # JavaScript/TypeScript
    elif ext in [".js", ".jsx", ".ts", ".tsx"]:
        if BiomeFormatter().is_available():
            return BiomeFormatter()
        elif PrettierFormatter().is_available():
            return PrettierFormatter()

    # Shell scripts
    elif ext in [".sh", ".bash", ".zsh", ".fish"]:
        if ShellCheckFormatter().is_available():
            return ShellCheckFormatter()

    # Generic files
    elif ext in [".json", ".yaml", ".yml", ".md", ".html", ".css", ".xml"]:
        if PrettierFormatter().is_available():
            return PrettierFormatter()

    return None


def format_file(file_path: str, check_only: bool = False) -> Dict[str, Any]:
    """
    Format a file using the appropriate tool.

    Args:
        file_path: Path to file to format
        check_only: If True, only check formatting without modifying

    Returns:
        Dictionary with results
    """
    result: Dict[str, Any] = {
        "file": file_path,
        "success": False,
        "formatted": False,
        "linted": False,
        "errors": [],
        "warnings": [],
    }

    # Check if file exists
    if not os.path.exists(file_path):
        errors = result.get("errors", [])
        if isinstance(errors, list):
            errors.append(f"File not found: {file_path}")
        return result

    # Get appropriate formatter
    formatter = get_formatter_for_file(file_path)
    if not formatter:
        warnings = result.get("warnings", [])
        if isinstance(warnings, list):
            warnings.append(f"No formatter available for {Path(file_path).suffix}")
        result["success"] = True  # No formatting needed
        return result

    try:
        # Format/lint based on formatter type
        errors: list[str] = []
        warnings: list[str] = []

        if isinstance(formatter, RuffFormatter):
            success, output = formatter.format_file(file_path)
            if success:
                result["formatted"] = True
            else:
                errors.append(f"Format failed: {output}")

            # Also lint with ruff
            success, output = formatter.lint_file(file_path)
            if success:
                result["linted"] = True
            else:
                warnings.append(f"Lint issues: {output}")

        elif isinstance(formatter, BiomeFormatter):
            # Biome can both format and lint
            success, output = formatter.format_file(file_path)
            if success:
                result["formatted"] = True
                result["linted"] = True
            else:
                errors.append(f"Biome failed: {output}")

        elif isinstance(formatter, PrettierFormatter):
            success, output = formatter.format_file(file_path)
            if success:
                result["formatted"] = True
            else:
                errors.append(f"Prettier failed: {output}")

        elif isinstance(formatter, ShellCheckFormatter):
            success, output = formatter.lint_file(file_path)
            if success:
                result["linted"] = True
            else:
                warnings.append(f"ShellCheck issues: {output}")

        else:
            warnings.append(f"Formatter {formatter.tool} not implemented")
            result["success"] = True

        result["errors"] = errors
        result["warnings"] = warnings

    except Exception as e:
        errors = result.get("errors", [])
        if isinstance(errors, list):
            errors.append(f"Exception: {str(e)}")

    result["success"] = len(result.get("errors", [])) == 0
    return result


def main():
    """
    Command line interface for formatters.
    """
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Code formatting utilities")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Format file
    format_parser = subparsers.add_parser("format", help="Format a file")
    format_parser.add_argument("file_path", help="File to format")
    format_parser.add_argument(
        "--check", action="store_true", help="Check only, don't modify"
    )

    # Detect language
    detect_parser = subparsers.add_parser("detect", help="Detect language from code")
    detect_parser.add_argument("code", help="Code to analyze")

    args = parser.parse_args()

    if args.command == "format":
        result = format_file(args.file_path, check_only=args.check)
        print(json.dumps(result, indent=2))

    elif args.command == "detect":
        lang = detect_markdown_language(args.code)
        print(json.dumps({"language": lang}))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
