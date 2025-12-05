# Code Quality & Testing Hook Templates

Templates for hooks that enforce code quality, run tests, and maintain coding standards.

## Python Code Quality Hooks

### PostToolUse: Python Formatting and Linting
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, os\nfrom pathlib import Path\n\ndata = json.load(sys.stdin)\nfile_path = data.get('tool_input', {}).get('file_path', '')\n\nif file_path.endswith('.py') and os.path.exists(file_path):\n    # Run ruff format\n    os.system(f'uv run ruff format {file_path}')\n    # Run ruff check with fixes\n    os.system(f'uv run ruff check --fix {file_path}')\n    print(f'✅ Python code formatted and linted: {Path(file_path).name}', file=sys.stderr)\n\"",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

### Stop: Python Type Checking
```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport os, subprocess, sys\nfrom pathlib import Path\n\ndef run_ty():\n    # Find project root with pyproject.toml\n    cwd = Path.cwd()\n    while cwd != cwd.parent:\n        if (cwd / 'pyproject.toml').exists() or (cwd / 'ty.ini').exists():\n            break\n        cwd = cwd.parent\n    \n    if not (cwd / 'pyproject.toml').exists():\n        print('⚠️ No pyproject.toml found, skipping type checking', file=sys.stderr)\n        return True\n    \n    result = subprocess.run(['uv', 'run', 'ty'], cwd=cwd, capture_output=True, text=True)\n    if result.returncode != 0:\n        print('❌ Type errors found:', file=sys.stderr)\n        print(result.stderr, file=sys.stderr)\n        sys.exit(2)  # Block with error\n    else:\n        print('✅ Type checking passed', file=sys.stderr)\n        return True\n\nrun_ty()\"",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

## TypeScript/JavaScript Code Quality Hooks

### PostToolUse: TypeScript Formatting and Linting
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c '\ninput=$(cat)\nfile_path=$(echo \"$input\" | jq -r \".tool_input.file_path // empty\")\n\nif [[ \"$file_path\" =~ \\.(ts|tsx|js|jsx)$ ]]; then\n    # Check if biome is configured\n    if [[ -f \"biome.json\" ]] || command -v biome &> /dev/null; then\n        biome check --write --unsafe \"$file_path\" 2>/dev/null && \\\n            echo \"✅ Formatted with Biome: $(basename \"$file_path\")\" >&2\n    elif command -v prettier &> /dev/null; then\n        prettier --write \"$file_path\" 2>/dev/null && \\\n            echo \"✅ Formatted with Prettier: $(basename \"$file_path\")\" >&2\n    fi\n    \n    # Run ESLint if available\n    if [[ -f \"eslint.config.js\" ]] || [[ -f \".eslintrc.*\" ]]; then\n        if command -v eslint &> /dev/null; then\n            eslint \"$file_path\" 2>/dev/null && \\\n                echo \"✅ ESLint passed: $(basename \"$file_path\")\" >&2\n        fi\n    fi\nfi'",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
```

### Stop: TypeScript Compilation Check
```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash -c '\nif [[ -f \"tsconfig.json\" ]] && command -v tsc &> /dev/null; then\n    echo \"🔍 Running TypeScript compilation check...\" >&2\n    if ! npx tsc --noEmit 2>/dev/null; then\n        echo \"❌ TypeScript compilation failed\" >&2\n        sys.exit 2\n    else\n        echo \"✅ TypeScript compilation passed\" >&2\n    fi\nelse\n    echo \"⚠️ No tsconfig.json or tsc found, skipping compilation check\" >&2\nfi'",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

## Bash Script Quality Hooks

### PostToolUse: Shell Script Linting
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c '\ninput=$(cat)\nfile_path=$(echo \"$input\" | jq -r \".tool_input.file_path // empty\")\n\nif [[ \"$file_path\" =~ \\.(sh|bash|ksh)$ ]] || [[ \"$(basename \"$file_path\")\" =~ ^\\..* ]]; then\n    if command -v shellcheck &> /dev/null; then\n        if shellcheck \"$file_path\" 2>/dev/null; then\n            echo \"✅ ShellCheck passed: $(basename \"$file_path\")\" >&2\n        else\n            echo \"⚠️ ShellCheck warnings for: $(basename \"$file_path\")\" >&2\n        fi\n    fi\nfi'",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

## Multi-Language Test Hooks

### PostToolUse: Run Targeted Tests
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, os, subprocess\nfrom pathlib import Path\n\ndef run_tests_for_file(file_path):\n    path = Path(file_path)\n    \n    # Python tests\n    if path.suffix == '.py':\n        # Look for corresponding test file\n        test_files = list(path.parent.glob(f'test_{path.name}*')) + \\\n                    list(path.parent.glob(f'{path.stem}_test.*')) + \\\n                    list(path.parent.glob('tests/**/test_*.py', recursive=True))\n        \n        if test_files:\n            # Run specific test if test file name matches\n            for test_file in test_files:\n                if path.stem in test_file.stem:\n                    subprocess.run(['uv', 'run', 'pytest', str(test_file), '-v'], \n                                 cwd=path.parent)\n                    print(f'✅ Ran tests: {test_file.name}', file=sys.stderr)\n                    return\n            \n            # Run all tests if no specific match\n            subprocess.run(['uv', 'run', 'pytest', 'tests/', '-x'], cwd=path.parent)\n            print('✅ Ran test suite', file=sys.stderr)\n    \n    # JavaScript/TypeScript tests\n    elif path.suffix in ['.ts', '.js', '.tsx', '.jsx']:\n        # Check for common test runners\n        if os.path.exists('package.json'):\n            with open('package.json') as f:\n                import json as pj\n                pkg = pj.load(f)\n                scripts = pkg.get('scripts', {})\n                \n                if 'test' in scripts:\n                    # Run only related tests if possible\n                    if 'npm test' in scripts or 'bun test' in scripts:\n                        cmd = 'bun test' if command -v bun &> /dev/null else 'npm test'\n                        subprocess.run(cmd.split(), cwd=path.parent)\n                        print('✅ Ran tests', file=sys.stderr)\n\ndata = json.load(sys.stdin)\nfile_path = data.get('tool_input', {}).get('file_path', '')\nif file_path and os.path.exists(file_path):\n    run_tests_for_file(file_path)\"",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

## Security Scanning Hooks

### PostToolUse: Security Scan for Dependencies
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c '\ninput=$(cat)\nfile_path=$(echo \"$input\" | jq -r \".tool_input.file_path // empty\")\nfilename=$(basename \"$file_path\")\n\n# Run security scan on dependency files\nif [[ \"$filename\" == \"package.json\" ]] && command -v npm &> /dev/null; then\n    echo \"🔍 Running npm audit...\" >&2\n    npm audit --audit-level=moderate 2>/dev/null || true\n    echo \"✅ Dependency check complete\" >&2\nelif [[ \"$filename\" == \"requirements.txt\" ]] && command -v pip-audit &> /dev/null; then\n    echo \"🔍 Running pip-audit...\" >&2\n    pip-audit 2>/dev/null || true\n    echo \"✅ Dependency check complete\" >&2\nelif [[ \"$filename\" == \"Cargo.toml\" ]] && command -v cargo &> /dev/null; then\n    echo \"🔍 Running cargo audit...\" >&2\n    cargo audit 2>/dev/null || true\n    echo \"✅ Dependency check complete\" >&2\nfi'",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

## Configuration-Based Hook Templates

### Quick Setup: Python Project (Complete)
Copy this to `.claude/settings.json` for a complete Python project setup:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/python-quality.sh",
            "timeout": 15
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/python-typecheck.sh",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

Create `.claude/hooks/python-quality.sh`:
```bash
#!/bin/bash
input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

if [[ "$file_path" == *.py ]]; then
    echo "🔧 Processing Python file: $(basename "$file_path")" >&2

    # Format with ruff
    if command -v uv &> /dev/null; then
        uv run ruff format "$file_path" 2>/dev/null && \
            echo "  ✓ Formatted" >&2

        uv run ruff check --fix "$file_path" 2>/dev/null && \
            echo "  ✓ Linted" >&2
    fi

    # Look for and run related tests
    test_file=$(dirname "$file_path")/test_$(basename "$file_path")
    if [[ -f "$test_file" ]] && command -v pytest &> /dev/null; then
        echo "  🧪 Running tests..." >&2
        uv run pytest "$test_file" -q 2>/dev/null && \
            echo "  ✓ Tests passed" >&2
    fi
fi

exit 0
```

Create `.claude/hooks/python-typecheck.sh`:
```bash
#!/bin/bash
if [[ -f "pyproject.toml" ]] && command -v uv &> /dev/null; then
    echo "🔍 Running type checking..." >&2
    if ! uv run ty 2>/dev/null; then
        echo "❌ Type errors found" >&2
        exit 2  # Block to fix types
    else
        echo "✅ All type checks passed" >&2
    fi
fi

exit 0
```

### Quick Setup: TypeScript Project (Complete)

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/typescript-quality.sh",
            "timeout": 15
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/typescript-build.sh",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

Create `.claude/hooks/typescript-quality.sh`:
```bash
#!/bin/bash
input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

if [[ "$file_path" =~ \.(ts|tsx|js|jsx)$ ]]; then
    echo "🔧 Processing TypeScript file: $(basename "$file_path")" >&2

    # Format with Biome
    if command -v biome &> /dev/null; then
        biome check --write --unsafe "$file_path" 2>/dev/null && \
            echo "  ✓ Formatted" >&2
    elif command -v prettier &> /dev/null; then
        prettier --write "$file_path" 2>/dev/null && \
            echo "  ✓ Formatted" >&2
    fi

    # Lint
    if command -v eslint &> /dev/null; then
        eslint "$file_path" 2>/dev/null && \
            echo "  ✓ Linted" >&2
    fi
fi

exit 0
```

Create `.claude/hooks/typescript-build.sh`:
```bash
#!/bin/bash
if [[ -f "tsconfig.json" ]] && command -v tsc &> /dev/null; then
    echo "🔍 Checking TypeScript compilation..." >&2
    if ! npx tsc --noEmit 2>/dev/null; then
        echo "❌ TypeScript compilation failed" >&2
        exit 2
    else
        echo "✅ TypeScript compilation passed" >&2
    fi

    # Run tests if configured
    if [[ -f "package.json" ]]; then
        if command -v bun &> /dev/null; then
            bun test 2>/dev/null && echo "✅ Tests passed" >&2
        elif command -v npm &> /dev/null; then
            npm test 2>/dev/null && echo "✅ Tests passed" >&2
        fi
    fi
fi

exit 0
```