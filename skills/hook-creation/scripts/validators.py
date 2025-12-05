#!/usr/bin/env python3
"""
Common validation functions for Claude Code hooks.
Reusable utilities for validating file paths, commands, and content.
"""

import os
import re
from pathlib import Path
from typing import List, Optional, Tuple


def is_sensitive_file(file_path: str) -> bool:
    """
    Check if a file path points to a sensitive file that should be protected.

    Args:
        file_path: Path to check

    Returns:
        True if file is considered sensitive
    """
    path = Path(file_path)
    filename = path.name

    # Directories that should never be modified
    sensitive_dirs = [
        ".git",
        ".aws",
        ".kube",
        ".ssh",
        ".gnupg",
        "node_modules",
        ".venv",
        "venv",
        "__pycache__",
        "target",
        "build",
        "dist",
    ]

    # Sensitive file patterns
    sensitive_patterns = [
        ".env",
        ".env.local",
        ".env.production",
        "secrets.yaml",
        "secrets.json",
        "secrets.toml",
        "id_rsa",
        "id_ed25519",
        "id_dsa",
        "id_ecdsa",
        "authorized_keys",
        "known_hosts",
        "config",
        ".pem",
        ".key",
        ".crt",
        ".p12",
        ".pfx",
        "docker-compose.override.yml",
        ".aws/credentials",
        ".aws/config",
        ".npmrc",
        ".pgpass",
        ".my.cnf",
        ".netrc",
        ".babelrc",
        ".eslintrc",
        ".prettierrc",
    ]

    # Check if in sensitive directory
    for dir_name in sensitive_dirs:
        if f"/{dir_name}/" in str(path) or str(path).startswith(f"{dir_name}/"):
            return True

    # Check filename patterns
    for pattern in sensitive_patterns:
        if pattern.endswith("/"):
            # Directory pattern
            if pattern[:-1] in str(path.parent):
                return True
        elif "*" in pattern:
            # Wildcard pattern
            if filename.endswith(pattern.replace("*", "")):
                return True
        else:
            # Exact match
            if filename == pattern or pattern in str(path):
                return True

    return False


def contains_secrets(content: str) -> List[Tuple[str, int]]:
    """
    Scan content for potential secrets or sensitive information.

    Args:
        content: Text content to scan

    Returns:
        List of (secret_type, line_number) tuples
    """
    findings = []
    lines = content.split("\n")

    # Secret patterns (pattern: description)
    secret_patterns = [
        (r"password\s*[:=]\s*[\"\'`][^\"\'`]{8,}[\"\'`]", "Password in config"),
        (r"api[_-]?key\s*[:=]\s*[\"\'`][A-Za-z0-9_\-]{20,}[\"\'`]", "API key"),
        (r"secret[_-]?key\s*[:=]\s*[\"\'`][A-Za-z0-9_\-]{20,}[\"\'`]", "Secret key"),
        (r"access[_-]?token\s*[:=]\s*[\"\'`][A-Za-z0-9_\-]{20,}[\"\'`]", "Access token"),
        (r"aws[_-]?secret[_-]?access[_-]?key\s*[:=]", "AWS secret key"),
        (
            r"aws[_-]?access[_-]?key\s*[:=]\s*[\"\'`]?AKIA[0-9A-Z]{16}[\"\'`]?",
            "AWS access key",
        ),
        (
            r"github[_-]?token\s*[:=]\s*[\"\'`]?ghp_[a-zA-Z0-9]{36}[\"\'`]?",
            "GitHub token",
        ),
        (r"private[_-]?key", "Private key reference"),
        (r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----", "Private key block"),
        (r"-----BEGIN\s+EC\s+PRIVATE\s+KEY-----", "EC private key"),
        (r"-----BEGIN\s+OPENSSH\s+PRIVATE\s+KEY-----", "OpenSSH private key"),
        (
            r"jwt\s*[:=]\s*[\"\'`]?eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*",
            "JWT token",
        ),
        (r"mysql://[^:]+:[^@]+@", "MySQL connection string"),
        (r"postgresql://[^:]+:[^@]+@", "PostgreSQL connection string"),
        (r"mongodb://[^:]+:[^@]+@", "MongoDB connection string"),
        (r"redis://[^:]*:[^@]+@", "Redis connection string with password"),
        (r"begin\s+password\s+", "PGP password"),
        (r"machine\s+.*\s+login\s+.*\s+password\s+", "Netrc password"),
        (r"Authorization:\s*Bearer\s+[A-Za-z0-9_\-]{20,}", "Bearer token"),
        (r"X-API-Key:\s*[A-Za-z0-9_\-]{20,}", "API key header"),
        (r"client[_-]?secret\s*[:=]", "Client secret"),
    ]

    for i, line in enumerate(lines, 1):
        line_lower = line.lower()

        # Skip common false positives
        if any(
            skip in line_lower
            for skip in [
                "example",
                "sample",
                "test",
                "mock",
                "fake",
                "placeholder",
                "your_",
                "xxx",
                "yyy",
                "zzz",
                "***",
                "...secret",
                "secret_url",
            ]
        ):
            continue

        for pattern, description in secret_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                findings.append((description, i))
                break

    return findings


def validate_command_safety(command: str) -> Tuple[bool, List[str]]:
    """
    Validate if a command is safe to execute.

    Args:
        command: Command string to validate

    Returns:
        Tuple of (is_safe, warnings_list)
    """
    warnings = []
    command_lower = command.lower()

    # Dangerous command patterns
    dangerous_patterns = [
        (r"rm\s+-rf\s+/", "Attempting to delete root directory"),
        (r"rm\s+-rf\s+\*", "Attempting to delete all files"),
        (r":\(\)\{\s*:\|:\&\s*\};:", "Fork bomb detected"),
        (r"dd\s+if=/dev/zero", "Writing zeros to device"),
        (r"mkfs\.", "Attempting to format filesystem"),
        (r"fdisk", "Disk partitioning tool"),
        (r"iptables\s+-F", "Flushing firewall rules"),
        (r"chmod\s+-R\s+777", "Setting world-writable permissions"),
        (r"chown\s+-R", "Recursive ownership change"),
        (r"echo\s+.*>\s+/dev/", "Writing directly to device"),
        (r"sudo\s+rm\s+-rf", "Running destructive command with sudo"),
        (r">\s+/dev/sda", "Writing to disk device"),
        (r"format\s+", "Windows format command"),
        (r"del\s+/[sS]", "Windows recursive delete"),
        (r"rmdir\s+/[sS]", "Windows recursive directory delete"),
    ]

    # Check each pattern
    for pattern, message in dangerous_patterns:
        if re.search(pattern, command_lower):
            warnings.append(f"DANGEROUS: {message}")

    # Suspicious patterns
    suspicious_patterns = [
        (r"curl.*\|\s*sh", "Downloading and executing script"),
        (r"wget.*\|\s*bash", "Downloading and executing script"),
        (r"eval\s*\$", "Evaluating variable as command"),
        (r"sh.*<<<", "Executing string as shell command"),
        (r"bash.*<<<", "Executing string as bash command"),
        (r"\\$\\(.*\\)", "Command substitution"),
        (r"`.*`", "Backtick command substitution"),
    ]

    for pattern, message in suspicious_patterns:
        if re.search(pattern, command):
            warnings.append(f"SUSPICIOUS: {message}")

    is_safe = len(warnings) == 0
    return is_safe, warnings


def is_production_environment() -> bool:
    """
    Check if we're running in a production environment.

    Returns:
        True if environment appears to be production
    """
    indicators = [
        os.getenv("NODE_ENV") == "production",
        os.getenv("ENV") == "production",
        os.getenv("APP_ENV") == "production",
        os.getenv("RAILS_ENV") == "production",
        os.getenv("FLASK_ENV") == "production",
        os.getenv("DJANGO_SETTINGS_MODULE", "").endswith("production"),
        "prod" in os.getenv("HOSTNAME", "").lower(),
        os.getenv("ENVIRONMENT", "").lower() == "production",
        os.path.exists("/.dockerenv")
        and os.getenv("ENV", "") not in ["development", "dev", "test"],
    ]

    return any(indicators)


def validate_file_path(
    file_path: str, base_dir: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Validate that a file path is safe and within allowed bounds.

    Args:
        file_path: File path to validate
        base_dir: Base directory to check against (defaults to current)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file_path:
        return False, "Empty file path"

    # Normalize path
    path = Path(file_path).resolve()

    # Check for path traversal
    if ".." in str(path):
        return False, f"Path traversal detected: {file_path}"

    # Check if it's within base directory if specified
    if base_dir:
        base = Path(base_dir).resolve()
        try:
            path.relative_to(base)
        except ValueError:
            return False, f"Path outside project directory: {file_path}"

    return True, ""


def get_file_language(file_path: str) -> Optional[str]:
    """
    Determine programming language from file extension.

    Args:
        file_path: File path to analyze

    Returns:
        Language string or None if unknown
    """
    ext = Path(file_path).suffix.lower()

    language_map = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".c": "c",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".cs": "csharp",
        ".php": "php",
        ".rb": "ruby",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "bash",
        ".fish": "fish",
        ".ps1": "powershell",
        ".bat": "batch",
        ".cmd": "batch",
        ".html": "html",
        ".htm": "html",
        ".css": "css",
        ".scss": "scss",
        ".sass": "sass",
        ".less": "less",
        ".sql": "sql",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".xml": "xml",
        ".md": "markdown",
        ".mdx": "markdown",
        ".dockerfile": "docker",
    }

    return language_map.get(ext)


def main():
    """
    Command line interface for testing validators.
    """
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Hook validation utilities")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Check sensitive file
    file_parser = subparsers.add_parser("check-file", help="Check if file is sensitive")
    file_parser.add_argument("file_path", help="File path to check")

    # Scan for secrets
    secrets_parser = subparsers.add_parser("scan-secrets", help="Scan file for secrets")
    secrets_parser.add_argument("file_path", help="File to scan")

    # Validate command
    cmd_parser = subparsers.add_parser("check-command", help="Check command safety")
    cmd_parser.add_argument("command", help="Command to validate")

    args = parser.parse_args()

    if args.command == "check-file":
        is_sensitive = is_sensitive_file(args.file_path)
        print(json.dumps({"file": args.file_path, "is_sensitive": is_sensitive}))

    elif args.command == "scan-secrets":
        try:
            with open(args.file_path, "r") as f:
                content = f.read()
            findings = contains_secrets(content)
            print(
                json.dumps(
                    {
                        "file": args.file_path,
                        "secrets_found": len(findings),
                        "findings": findings,
                    }
                )
            )
        except Exception as e:
            print(json.dumps({"error": str(e)}))

    elif args.command == "check-command":
        is_safe, warnings = validate_command_safety(args.command)
        print(
            json.dumps(
                {"command": args.command, "is_safe": is_safe, "warnings": warnings}
            )
        )

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
