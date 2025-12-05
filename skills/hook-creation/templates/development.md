# Development Workflow Hook Templates

Templates for hooks that automate development workflows, manage build processes, and handle development servers.

## Development Server Management

### PreToolUse: Prevent Duplicate Dev Servers
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, os, re\nfrom pathlib import Path\nimport fcntl\n\n# Development server commands to track\nDEV_SERVER_COMMANDS = [\n    r'npm\\s+run\\s+dev',\n    r'npm\\s+start',\n    r'yarn\\s+dev',\n    r'yarn\\s+start',\n    r'pnpm\\s+dev',\n    r'pnpm\\s+start',\n    r'bun\\s+dev',\n    r'bun\\s+start',\n    r'python.*\\s+runserver',\n    r'python.*manage\\.py.*runserver',\n    r'uvicorn.*reload',\n    r'flask\\s+run',\n    r'docker-compose\\s+up',\n    r'go\\s+run',\n    r'mix\\s+phx\\.server'\n]\n\ndef is_dev_server_command(command):\n    for pattern in DEV_SERVER_COMMANDS:\n        if re.search(pattern, command, re.IGNORECASE):\n            return True\n    return False\n\ndef get_lock_file(project_dir):\n    # Create unique lock file based on project path\n    hash_val = str(abs(hash(project_dir)))[:8]\n    return f'/tmp/claude-dev-server-{hash_val}.lock'\n\ndef check_existing_server(project_dir, command):\n    lock_file = get_lock_file(project_dir)\n    \n    try:\n        with open(lock_file, 'r') as f:\n            pid = int(f.read().strip())\n            \n            # Check if process is still running\n            try:\n                os.kill(pid, 0)\n                return True, pid\n            except OSError:\n                # Process not running, clean up lock\n                os.remove(lock_file)\n                return False, None\n    except (FileNotFoundError, ValueError):\n        return False, None\n\ndef create_lock(project_dir, pid):\n    lock_file = get_lock_file(project_dir)\n    \n    try:\n        with open(lock_file, 'w') as f:\n            f.write(str(pid))\n        os.chmod(lock_file, 0o644)\n    except Exception:\n        pass  # Fail silently\n\ndata = json.load(sys.stdin)\ncommand = data.get('tool_input', {}).get('command', '')\ncwd = data.get('cwd', '')\n\nif is_dev_server_command(command):\n    existing, pid = check_existing_server(cwd, command)\n    \n    if existing:\n        print(f'❌ Development server already running (PID: {pid})', file=sys.stderr)\n        print('   Use a new terminal or stop the existing server first', file=sys.stderr)\n        sys.exit(2)  # Block the command\n    else:\n        # Create lock file to track this server\n        import time\n        create_lock(cwd, os.getpid())\n        print('🚀 Starting development server...', file=sys.stderr)\n\nsys.exit(0)\n\"",
            "timeout": 5
          }
        ]
      }
    ]
  },
  "SessionStart": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "python3 -c \"\nimport os\nfrom pathlib import Path\n\n# Clean up stale lock files\nlock_dir = Path('/tmp')\nfor lock_file in lock_dir.glob('claude-dev-server-*.lock'):\n    try:\n        with open(lock_file, 'r') as f:\n            pid = int(f.read().strip())\n        \n        # Check if process is still running\n        os.kill(pid, 0)\n    except (OSError, ValueError):\n        # Process not running or invalid PID, clean up\n        try:\n            lock_file.unlink()\n            print(f'🧹 Cleaned stale server lock: {lock_file.name}', file=sys.stderr)\n        except:\n            pass\n\nprint('✅ Development server locks checked', file=sys.stderr)\n\"",
          "timeout": 5
        }
      ]
    }
  ]
}
```

## Build and Dependency Management

### PostToolUse: Auto-install Dependencies
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c '\ninput=$(cat)\nfile_path=$(echo \"$input\" | jq -r \".tool_input.file_path // empty\")\nfilename=$(basename \"$file_path\")\n\n# Auto-install dependencies when package files are updated\nif [[ \"$filename\" == \"package.json\" ]]; then\n    echo \"📦 Package.json updated, checking dependencies...\" >&2\n    \n    # Check if node_modules exists or if lockfile changed\n    if [[ ! -d \"node_modules\" ]] || [[ \"$filename\" == \"package-lock.json\" ]] || [[ \"$filename\" == \"yarn.lock\" ]]; then\n        if command -v pnpm &> /dev/null && [[ -f \"pnpm-lock.yaml\" ]]; then\n            echo \"  Running pnpm install...\" >&2\n            pnpm install\n        elif command -v yarn &> /dev/null && [[ -f \"yarn.lock\" ]]; then\n            echo \"  Running yarn install...\" >&2\n            yarn install\n        elif command -v npm &> /dev/null; then\n            echo \"  Running npm install...\" >&2\n            npm install\n        fi\n    fi\n    \nelif [[ \"$filename\" == \"requirements.txt\" ]] || [[ \"$filename\" == \"pyproject.toml\" ]]; then\n    echo \"🐍 Python dependencies updated...\" >&2\n    if command -v uv &> /dev/null; then\n        uv sync\n    elif command -v pip &> /dev/null; then\n        pip install -r requirements.txt 2>/dev/null || true\n    fi\n    \nelif [[ \"$filename\" == \"Cargo.toml\" ]]; then\n    echo \"🦀 Rust dependencies updated...\" >&2\n    if command -v cargo &> /dev/null; then\n        cargo fetch\n    fi\n    \nelif [[ \"$filename\" == \"go.mod\" ]]; then\n    echo \"🐹 Go dependencies updated...\" >&2\n    if command -v go &> /dev/null; then\n        go mod download\n    go mod tidy\n    fi\nfi\n\nexit 0'",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

### Stop: Build Verification
```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash -c '\necho \"🔍 Running build verification...\" >&2\n\n# JavaScript/TypeScript build\nif [[ -f \"package.json\" ]]; then\n    if npm run build --silent 2>/dev/null; then\n        echo \"✅ Build succeeded\" >&2\n    else\n        echo \"❌ Build failed\" >&2\n        exit 2\n    fi\nfi\n\n# Rust build\nif [[ -f \"Cargo.toml\" ]]; then\n    if cargo check --quiet 2>/dev/null; then\n        echo \"✅ Cargo check passed\" >&2\n    else\n        echo \"❌ Cargo check failed\" >&2\n        exit 2\n    fi\nfi\n\n# Go build\nif [[ -f \"go.mod\" ]]; then\n    if go build ./... 2>/dev/null; then\n        echo \"✅ Go build passed\" >&2\n    else\n        echo \"❌ Go build failed\" >&2\n        exit 2\n    fi\nfi\n\nexit 0'",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

## Pre-commit Style Checks

### PreToolUse: Pre-commit Validation
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c '\ninput=$(cat)\ncommand=$(echo \"$input\" | jq -r \".tool_input.command // empty\")\n\n# Block git commit if hooks would fail\nif [[ \"$command\" =~ ^git\\s+commit ]]; then\n    echo \"🔍 Running pre-commit checks...\" >&2\n    \n    # Python checks\n    if [[ -f \"pyproject.toml\" ]]; then\n        if command -v uv &> /dev/null; then\n            # Check formatting\n            if ! uv run ruff format --check . 2>/dev/null; then\n                echo \"❌ Code is not properly formatted\" >&2\n                echo \"   Run: uv run ruff format .\" >&2\n                exit 2\n            fi\n            \n            # Check linting\n            if ! uv run ruff check . 2>/dev/null; then\n                echo \"❌ Linting errors found\" >&2\n                echo \"   Run: uv run ruff check --fix .\" >&2\n                exit 2\n            fi\n        fi\n    fi\n    \n    # TypeScript checks\n    if [[ -f \"package.json\" ]]; then\n        if command -v biome &> /dev/null; then\n            if ! biome check . 2>/dev/null; then\n                echo \"❌ Biome checks failed\" >&2\n                echo \"   Run: biome check --write .\" >&2\n                exit 2\n            fi\n        fi\n        \n        # TypeScript compilation\n        if [[ -f \"tsconfig.json\" ]] && command -v tsc &> /dev/null; then\n            if ! npx tsc --noEmit 2>/dev/null; then\n                echo \"❌ TypeScript compilation failed\" >&2\n                exit 2\n            fi\n        fi\n    fi\n    \n    echo \"✅ Pre-commit checks passed\" >&2\nfi\n\nexit 0'",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

## Automated Testing Workflows

### PostToolUse: Smart Test Runner
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, os\nfrom pathlib import Path\nimport subprocess\nimport time\n\n# Debounce to avoid running tests too frequently\ndef should_run_tests(file_path):\n    # Simple debounce: only run tests if file was modified more than 5s ago\n    try:\n        mtime = os.path.getmtime(file_path)\n        return (time.time() - mtime) > 5\n    except:\n        return True\n\ndef find_and_run_tests(file_path):\n    path = Path(file_path)\n    \n    # Skip test files themselves (unless specifically edited)\n    if 'test' in path.name.lower():\n        return\n    \n    # Python tests\n    if path.suffix == '.py':\n        # Look for test directories\n        test_dirs = ['tests', 'test']\n        \n        for test_dir in test_dirs:\n            if Path(test_dir).exists():\n                # Try to find specific test file\n                test_patterns = [\n                    f'test_{path.stem}.py',\n                    f'{path.stem}_test.py',\n                    f'tests/**/test_{path.stem}.py',\n                    f'tests/**/{path.stem}_test.py'\n                ]\n                \n                for pattern in test_patterns:\n                    test_files = list(Path('.').glob(pattern))\n                    if test_files:\n                        test_file = test_files[0]\n                        print(f'🧪 Running tests for {path.name}...', file=sys.stderr)\n                        subprocess.run(['uv', 'run', 'pytest', str(test_file), '-v', '-x'], \n                                     capture_output=True)\n                        print(f'✅ Tests completed: {test_file.name}', file=sys.stderr)\n                        return\n                \n                # No specific test found, run related tests\n                print(f'🧪 Running related tests...', file=sys.stderr)\n                subprocess.run(['uv', 'run', 'pytest', test_dir, '-k', path.stem, '-v'], \n                             capture_output=True)\n                print(f'✅ Tests completed', file=sys.stderr)\n                return\n    \n    # JavaScript/TypeScript tests\n    elif path.suffix in ['.ts', '.js', '.tsx', '.jsx']:\n        # Check for test files\n        test_patterns = [\n            f'{path.stem}.test.{path.suffix}',\n            f'{path.stem}.spec.{path.suffix}',\n            f'**/__tests__/**/{path.stem}.*'\n        ]\n        \n        for pattern in test_patterns:\n            test_files = list(Path('.').glob(pattern))\n            if test_files:\n                test_file = test_files[0]\n                print(f'🧪 Running tests for {path.name}...', file=sys.stderr)\n                \n                # Determine test command\n                if command -v bun &> /dev/null:\n                    subprocess.run(['bun', 'test', str(test_file)], capture_output=True)\n                elif command -v npm &> /dev/null:\n                    subprocess.run(['npm', 'test', '--', str(test_file)], capture_output=True)\n                \n                print(f'✅ Tests completed: {test_file.name}', file=sys.stderr)\n                return\n\ndata = json.load(sys.stdin)\nfile_path = data.get('tool_input', {}).get('file_path', '')\n\nif file_path and os.path.exists(file_path) and should_run_tests(file_path):\n    find_and_run_tests(file_path)\n\nsys.exit(0)\n\"",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

## Docker and Container Management

### PreToolUse: Docker Safety Checks
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c '\ninput=$(cat)\ncommand=$(echo \"$input\" | jq -r \".tool_input.command // empty\")\n\n# Docker safety checks\nif [[ \"$command\" =~ docker ]]; then\n    # Block docker rm -f without container name\n    if [[ \"$command\" =~ docker\\s+rm\\s+-f\\s*$ ]]; then\n        echo \"❌ Dangerous: docker rm -f without container name\" >&2\n        echo \"   Please specify container name explicitly\" >&2\n        exit 2\n    fi\n    \n    # Warn about docker run with privileged mode\n    if [[ \"$command\" =~ --privileged ]]; then\n        echo \"⚠️ Warning: Running with --privileged mode\" >&2\n    fi\n    \n    # Check for bind mounts to sensitive directories\n    if [[ \"$command\" =~ -v\\s+/.*:\\s+/(etc|root|home) ]]; then\n        echo \"⚠️ Warning: Mounting sensitive system directory\" >&2\n    fi\n    \n    # Suggest .dockerignore if missing\n    if [[ \"$command\" =~ docker\\s+build ]]; then\n        if [[ ! -f .dockerignore ]]; then\n            echo \"💡 Consider creating a .dockerignore file\" >&2\n        fi\n    fi\nfi\n\nexit 0'",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### PostToolUse: Docker Compose Service Management
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c '\ninput=$(cat)\nfile_path=$(echo \"$input\" | jq -r \".tool_input.file_path // empty\")\nfilename=$(basename \"$file_path\")\n\n# Docker Compose file updated\nif [[ \"$filename\" == \"docker-compose.yml\" ]] || [[ \"$filename\" == \"docker-compose.yaml\" ]]; then\n    echo \"🐳 Docker Compose configuration updated...\" >&2\n    \n    # Check if services are running\n    if command -v docker-compose &> /dev/null; then\n        running_services=$(docker-compose ps -q 2>/dev/null | wc -l)\n        if [[ $running_services -gt 0 ]]; then\n            echo \"  ℹ️ Services are currently running\" >&2\n            echo \"  💡 Consider: docker-compose up -d --force-recreate\" >&2\n        fi\n    fi\nfi\n\nexit 0'",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

## Complete Development Workflow Setup

### All-in-One Development Hooks
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/dev-precheck.sh",
            "timeout": 10
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/dev-postprocess.sh",
            "timeout": 20
          }
        ]
      },
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/deps-install.sh",
            "timeout": 60
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/build-verify.sh",
            "timeout": 60
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/dev-init.sh",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

Create `.claude/hooks/dev-precheck.sh`:
```bash
#!/bin/bash
# Development pre-check hook
input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // empty')

# Prevent duplicate dev servers
if [[ "$command" =~ (npm run dev|yarn dev|pnpm dev|bun dev|python.*runserver) ]]; then
    # Check for existing dev server
    if pgrep -f "runserver\|webpack.*dev\|vite.*dev" > /dev/null; then
        echo "❌ Development server already running" >&2
        exit 2
    fi
fi

# Git commit pre-checks
if [[ "$command" =~ ^git\ commit ]]; then
    # Run pre-commit hooks
    if [[ -f ".pre-commit-config.yaml" ]] && command -v pre-commit &> /dev/null; then
        pre-commit run --all-files
    fi
fi

exit 0
```

Create `.claude/hooks/dev-postprocess.sh`:
```bash
#!/bin/bash
# Development post-processing hook
input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')
filename=$(basename "$file_path")

# Language-specific post-processing
case "${filename##*.}" in
    py)
        echo "🐍 Processing Python file..." >&2
        if command -v uv &> /dev/null; then
            uv run ruff format "$file_path" 2>/dev/null
            uv run ruff check --fix "$file_path" 2>/dev/null
        fi
        ;;
    ts|tsx|js|jsx)
        echo "🟨 Processing TypeScript/JavaScript file..." >&2
        if command -v biome &> /dev/null; then
            biome check --write --unsafe "$file_path" 2>/dev/null
        elif command -v prettier &> /dev/null; then
            prettier --write "$file_path" 2>/dev/null
        fi
        ;;
    sh|bash)
        echo "📜 Processing shell script..." >&2
        if command -v shellcheck &> /dev/null; then
            shellcheck "$file_path" 2>/dev/null
        fi
        ;;
esac

exit 0
```

Create `.claude/hooks/deps-install.sh`:
```bash
#!/bin/bash
# Dependency installation hook
input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')
filename=$(basename "$file_path")

# Install dependencies when package files change
case "$filename" in
    package.json|pnpm-lock.yaml|yarn.lock|package-lock.json)
        echo "📦 Installing Node.js dependencies..." >&2
        if command -v pnpm &> /dev/null && [[ -f "pnpm-lock.yaml" ]]; then
            pnpm install
        elif command -v yarn &> /dev/null && [[ -f "yarn.lock" ]]; then
            yarn install
        else
            npm install
        fi
        ;;
    requirements.txt|pyproject.toml|poetry.lock)
        echo "🐍 Installing Python dependencies..." >&2
        if command -v uv &> /dev/null; then
            uv sync
        elif command -v poetry &> /dev/null && [[ -f "pyproject.toml" ]]; then
            poetry install
        else
            pip install -r requirements.txt 2>/dev/null || true
        fi
        ;;
    Cargo.toml|Cargo.lock)
        echo "🦀 Updating Rust dependencies..." >&2
        cargo fetch
        ;;
    go.mod|go.sum)
        echo "🐹 Updating Go dependencies..." >&2
        go mod download
        go mod tidy
        ;;
esac

exit 0
```

Create `.claude/hooks/build-verify.sh`:
```bash
#!/bin/bash
# Build verification hook
echo "🔍 Verifying build..." >&2

# Try to build based on detected project type
if [[ -f "package.json" ]]; then
    npm run build --silent && echo "✅ Build successful" >&2
elif [[ -f "Cargo.toml" ]]; then
    cargo check --quiet && echo "✅ Cargo check passed" >&2
elif [[ -f "go.mod" ]]; then
    go build ./... && echo "✅ Go build passed" >&2
elif [[ -f "pyproject.toml" ]] && grep -q "build-system" pyproject.toml; then
    uv build --quiet 2>/dev/null && echo "✅ Python build passed" >&2
else
    echo "ℹ️ No build configuration detected" >&2
fi

exit 0
```

Create `.claude/hooks/dev-init.sh`:
```bash
#!/bin/bash
# Development environment initialization
echo "🚀 Initializing development environment..." >&2

# Check for required tools
check_tool() {
    if ! command -v "$1" &> /dev/null; then
        echo "  ⚠️ $1 not installed" >&2
    else
        echo "  ✅ $1 available" >&2
    fi
}

# Check common development tools
if [[ -f "package.json" ]]; then
    check_tool "node"
    check_tool "npm"
    check_tool "bun"
    check_tool "biome"
elif [[ -f "pyproject.toml" ]]; then
    check_tool "python3"
    check_tool "uv"
    check_tool "ty"
fi

# Set up environment
if [[ -f ".env.example" ]] && [[ ! -f ".env" ]]; then
    echo "💡 Consider copying .env.example to .env" >&2
fi

# Check git status
if git rev-parse --git-dir > /dev/null 2>&1; then
    if [[ -n $(git status --porcelain 2>/dev/null) ]]; then
        echo "📝 Git repository has uncommitted changes" >&2
    fi
fi

echo "✅ Development environment ready" >&2
exit 0
```