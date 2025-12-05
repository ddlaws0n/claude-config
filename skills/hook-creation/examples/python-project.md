# Python Project Hook Example

Complete setup for a Python project with code quality, testing, and type checking hooks.

## Project Structure

```
my-python-project/
├── .claude/
│   ├── settings.json          # Hook configuration
│   └── hooks/
│       ├── python-quality.sh  # PostToolUse: format and lint
│       └── python-typecheck.sh # Stop: type checking
├── src/
├── tests/
├── pyproject.toml
└── requirements.txt
```

## Configuration File

### `.claude/settings.json`

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

## Hook Scripts

### `.claude/hooks/python-quality.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

# Read JSON input from Claude Code
input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

# Only process Python files
if [[ "$file_path" != *.py ]]; then
    exit 0
fi

echo "🔧 Processing Python file: $(basename "$file_path")" >&2

# Check if we're in a project with uv
if [[ ! -f "pyproject.toml" ]]; then
    echo "⚠️ No pyproject.toml found, skipping Python formatting" >&2
    exit 0
fi

# Run ruff format
if command -v uv &> /dev/null; then
    echo "  Formatting with ruff..." >&2
    if uv run ruff format "$file_path" 2>&1; then
        echo "  ✅ Formatted" >&2
    else
        echo "  ⚠️ Ruff format had issues" >&2
    fi

    # Run ruff check with fixes
    echo "  Linting with ruff..." >&2
    if uv run ruff check --fix "$file_path" 2>&1; then
        echo "  ✅ Linted" >&2
    else
        echo "  ⚠️ Ruff check found unfixable issues" >&2
    fi
else
    echo "  ❌ uv not found, skipping formatting" >&2
fi

# Run related tests if they exist
if command -v uv &> /dev/null && command -v pytest &> /dev/null; then
    # Look for test file
    dir=$(dirname "$file_path")
    base=$(basename "$file_path" .py)

    test_files=(
        "$dir/test_${base}.py"
        "$dir/tests/test_${base}.py"
        "tests/test_${base}.py"
        "tests/${base}_test.py"
    )

    for test_file in "${test_files[@]}"; do
        if [[ -f "$test_file" ]]; then
            echo "  🧪 Running tests: $test_file" >&2
            if uv run pytest "$test_file" -v 2>&1; then
                echo "  ✅ Tests passed" >&2
            else
                echo "  ❌ Tests failed" >&2
            fi
            break
        fi
    done
fi

exit 0
```

### `.claude/hooks/python-typecheck.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "🔍 Running type checking..." >&2

# Check if ty is configured
if [[ ! -f "pyproject.toml" ]] && [[ ! -f "ty.ini" ]] && [[ ! -f ".ty.ini" ]]; then
    echo "⚠️ No ty configuration found" >&2
    echo "💡 Add [tool.ty] section to pyproject.toml" >&2
    exit 0
fi

# Use uv if available, otherwise try direct ty
if command -v uv &> /dev/null; then
    echo "  Running uv run ty..." >&2
    if uv run ty . 2>&1; then
        echo "✅ Type checking passed" >&2
    else
        echo "❌ Type errors found" >&2
        echo "Please fix type errors before continuing" >&2
        exit 2  # Block to fix types
    fi
elif command -v ty &> /dev/null; then
    echo "  Running ty..." >&2
    if ty . 2>&1; then
        echo "✅ Type checking passed" >&2
    else
        echo "❌ Type errors found" >&2
        exit 2
    fi
else
    echo "❌ ty not installed" >&2
    echo "Install with: uv add --dev ty" >&2
    exit 0
fi

exit 0
```

## Setup Instructions

1. **Create the directory structure**:
```bash
mkdir -p .claude/hooks
```

2. **Create the hooks**:
```bash
# Create the settings file
cat > .claude/settings.json << 'EOF'
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
EOF

# Create the quality hook
cat > .claude/hooks/python-quality.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

if [[ "$file_path" != *.py ]]; then
    exit 0
fi

echo "🔧 Processing Python file: $(basename "$file_path")" >&2

if [[ ! -f "pyproject.toml" ]]; then
    echo "⚠️ No pyproject.toml found, skipping Python formatting" >&2
    exit 0
fi

if command -v uv &> /dev/null; then
    echo "  Formatting with ruff..." >&2
    uv run ruff format "$file_path" 2>&1 || echo "  ⚠️ Ruff format had issues" >&2

    echo "  Linting with ruff..." >&2
    uv run ruff check --fix "$file_path" 2>&1 || echo "  ⚠️ Ruff check found issues" >&2

    # Run tests
    if command -v pytest &> /dev/null; then
        for test_file in "test_$(basename "$file_path")" "tests/test_$(basename "$file_path")"; do
            if [[ -f "$test_file" ]]; then
                echo "  🧪 Running tests..." >&2
                uv run pytest "$test_file" -q 2>&1 && echo "  ✅ Tests passed" >&2 || echo "  ❌ Tests failed" >&2
                break
            fi
        done
    fi
fi

exit 0
EOF

# Create the typecheck hook
cat > .claude/hooks/python-typecheck.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

echo "🔍 Running type checking..." >&2

if [[ ! -f "pyproject.toml" ]] && [[ ! -f "ty.ini" ]]; then
    echo "⚠️ No ty configuration found" >&2
    exit 0
fi

if command -v uv &> /dev/null; then
    if uv run ty . 2>&1; then
        echo "✅ Type checking passed" >&2
    else
        echo "❌ Type errors found" >&2
        exit 2
    fi
else
    echo "❌ uv/ty not installed" >&2
fi

exit 0
EOF

# Make hooks executable
chmod +x .claude/hooks/*.sh
```

3. **Configure pyproject.toml** (if not already):
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-project"
version = "0.1.0"
dependencies = []

[tool.ruff]
line-length = 88
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "A", "C4", "DTZ", "T10"]
ignore = []

[tool.ty]
python_version = "3.13"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
addopts = "-v"
```

## Usage

Once configured:

1. **Edit a Python file** - Claude will automatically format and lint it
2. **Run tests** - Related tests will execute automatically
3. **Finish session** - MyPy type checking runs before Claude stops

## Expected Output

### When editing a file:
```
🔧 Processing Python file: main.py
  Formatting with ruff...
  ✅ Formatted
  Linting with ruff...
  ✅ Linted
  🧪 Running tests: test_main.py
  ✅ Tests passed
```

### When stopping:
```
🔍 Running type checking...
  Running uv run ty...
✅ Type checking passed
```

### If there are type errors:
```
🔍 Running type checking...
  Running uv run ty...
❌ Type errors found
Please fix type errors before continuing
```

## Troubleshooting

### Hook doesn't run
1. Check file permissions: `ls -la .claude/hooks/`
2. Verify JSON syntax: `cat .claude/settings.json | jq`
3. Restart Claude Code after changes

### Commands not found
1. Install required tools:
   ```bash
   pip install uv ruff ty pytest
   ```
2. Or add to pyproject.toml:
   ```toml
   [project.optional-dependencies]
   dev = ["ruff", "ty", "pytest"]
   ```

### Type checking always fails
1. Ensure `ty` is configured in `pyproject.toml`
2. Add `# type: ignore` for external libraries if needed
3. Install stub packages: `uv add --dev types-requests`