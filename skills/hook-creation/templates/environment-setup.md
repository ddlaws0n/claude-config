# Environment Setup Hook Templates

Templates for SessionStart hooks that configure and persist environment variables across all bash commands in a Claude session using `$CLAUDE_ENV_FILE`.

## Understanding $CLAUDE_ENV_FILE

### What It Is
`$CLAUDE_ENV_FILE` is a special environment variable **only available in SessionStart hooks** that points to a session-specific file where you can persist environment variables. These variables are automatically loaded before every Bash command execution in the current session.

### Why It Matters
Without `$CLAUDE_ENV_FILE`, environment setup commands (like `nvm use`, `source .venv/bin/activate`, etc.) would only apply to that single hook execution. The next bash command would start fresh without those settings. Using `$CLAUDE_ENV_FILE` ensures:

- **Persistence**: Variables survive across multiple bash commands
- **Consistency**: Every command in the session uses the same environment
- **Efficiency**: Setup runs once during SessionStart, not repeatedly
- **Simplicity**: No need for complex wrapper scripts in every bash call

### How It Works
1. SessionStart hook writes to `$CLAUDE_ENV_FILE` (bash-compatible variable definitions)
2. Claude Code sources this file before every Bash command in the session
3. Environment variables and aliases persist across all tools
4. File is cleaned up automatically at session end

## Basic Template: Setting Individual Variables

Create a SessionStart hook to set environment variables that persist throughout the session:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash -c '\n# Session environment setup\necho \"🔧 Configuring session environment...\" >&2\n\n# Write environment variables to the session file\nif [[ -n \"$CLAUDE_ENV_FILE\" ]]; then\n    # Set NODE_ENV for all commands in this session\n    echo \"export NODE_ENV=development\" >> \"$CLAUDE_ENV_FILE\"\n    \n    # Set project-specific variables\n    echo \"export PROJECT_ROOT=$(pwd)\" >> \"$CLAUDE_ENV_FILE\"\n    echo \"export LOG_LEVEL=debug\" >> \"$CLAUDE_ENV_FILE\"\n    \n    # Add custom PATH entries\n    echo \"export PATH=\\\"$(pwd)/scripts:\\$PATH\\\"\" >> \"$CLAUDE_ENV_FILE\"\n    \n    echo \"✅ Environment configured (NODE_ENV, PROJECT_ROOT, LOG_LEVEL)\" >&2\nelse\n    echo \"⚠️ CLAUDE_ENV_FILE not available, skipping persistent setup\" >&2\nfi\n\nexit 0\n'",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

## Node Version Management with nvm

Use SessionStart to set up the correct Node version for the entire session:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash -c '\necho \"📦 Checking Node.js environment...\" >&2\n\nif [[ -f \".nvmrc\" ]] && [[ -s \"$HOME/.nvm/nvm.sh\" ]]; then\n    echo \"✅ Found .nvmrc, will configure nvm\" >&2\n    \n    # Write nvm initialization to session file\n    if [[ -n \"$CLAUDE_ENV_FILE\" ]]; then\n        cat >> \"$CLAUDE_ENV_FILE\" << '\"'\"'NVMEOF'\"'\"'\n# Initialize nvm for this session\nexport NVM_DIR=\"$HOME/.nvm\"\nif [[ -s \"$NVM_DIR/nvm.sh\" ]]; then\n    source \"$NVM_DIR/nvm.sh\"\n    \n    # Use version from .nvmrc\n    if [[ -f \".nvmrc\" ]]; then\n        nvm use\n    fi\nfi\nNVMEOF\n        \n        # Now source it in this shell to verify\n        export NVM_DIR=\"$HOME/.nvm\"\n        [[ -s \"$NVM_DIR/nvm.sh\" ]] && source \"$NVM_DIR/nvm.sh\"\n        \n        if [[ -f \".nvmrc\" ]]; then\n            nvm use 2>&1 | grep -E \"(Now using|v[0-9])\" && echo \"✅ Node version configured\" >&2\n        fi\n    fi\nelse\n    echo \"ℹ️ No nvm configuration needed\" >&2\nfi\n\nexit 0\n'",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
```

## Python Virtual Environment Activation

Automatically activate Python virtual environment for the session:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash -c '\necho \"🐍 Setting up Python environment...\" >&2\n\n# Detect virtual environment location\nVVENV_PATHS=(\".venv\" \"venv\" \"env\" \".env\")\nVVENV_FOUND=\"\"\n\nfor venv_path in \"${VVENV_PATHS[@]}\"; do\n    if [[ -d \"$venv_path\" ]] && [[ -f \"$venv_path/bin/activate\" ]]; then\n        VVENV_FOUND=\"$venv_path\"\n        break\n    fi\ndone\n\nif [[ -n \"$VVENV_FOUND\" ]]; then\n    echo \"✅ Found virtual environment at $VVENV_FOUND\" >&2\n    \n    if [[ -n \"$CLAUDE_ENV_FILE\" ]]; then\n        cat >> \"$CLAUDE_ENV_FILE\" << \"EOF\"\n# Activate Python virtual environment\nif [[ -f \"$VVENV_FOUND/bin/activate\" ]]; then\n    source \"$VVENV_FOUND/bin/activate\"\nfi\nEOF\n        \n        # Verify it works\n        source \"$VVENV_FOUND/bin/activate\" 2>/dev/null\n        if command -v python &> /dev/null; then\n            py_version=$(python --version 2>&1)\n            echo \"  Activated: $py_version\" >&2\n        fi\n    fi\nelse\n    if [[ -f \"requirements.txt\" ]] || [[ -f \"pyproject.toml\" ]]; then\n        echo \"⚠️ Python project detected but no virtual environment found\" >&2\n        echo \"  Consider: python3 -m venv .venv\" >&2\n    fi\nfi\n\nexit 0\n'",
            "timeout": 20
          }
        ]
      }
    ]
  }
}
```

## Custom PATH Modifications

Persistently modify PATH to include custom script directories and tools:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash -c '\necho \"🛣️  Configuring PATH...\" >&2\n\nif [[ -n \"$CLAUDE_ENV_FILE\" ]]; then\n    # Initialize PATH if not already set\n    echo \"export PATH=\\\"$PATH\\\"\" >> \"$CLAUDE_ENV_FILE\"\n    \n    # Add project scripts directory\n    if [[ -d \"scripts\" ]]; then\n        echo \"export PATH=\\\"$(pwd)/scripts:\\$PATH\\\"\" >> \"$CLAUDE_ENV_FILE\"\n        echo \"  Added project scripts/\" >&2\n    fi\n    \n    # Add local bin directory\n    if [[ -d \"local/bin\" ]]; then\n        echo \"export PATH=\\\"$(pwd)/local/bin:\\$PATH\\\"\" >> \"$CLAUDE_ENV_FILE\"\n        echo \"  Added local/bin/\" >&2\n    fi\n    \n    # Add custom tool directories\n    if [[ -d \"$HOME/.local/bin\" ]]; then\n        echo \"export PATH=\\\"$HOME/.local/bin:\\$PATH\\\"\" >> \"$CLAUDE_ENV_FILE\"\n        echo \"  Added ~/.local/bin/\" >&2\n    fi\n    \n    echo \"✅ PATH configured\" >&2\nfi\n\nexit 0\n'",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

## AWS/Cloud Tool Environment Setup

Configure AWS credentials and cloud-specific settings for the session:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash -c '\necho \"☁️  Setting up cloud environment...\" >&2\n\nif [[ -n \"$CLAUDE_ENV_FILE\" ]]; then\n    # AWS CLI configuration\n    if [[ -f \"$HOME/.aws/credentials\" ]]; then\n        # Get default profile\n        if command -v aws &> /dev/null; then\n            aws_profile=$(aws configure get profile 2>/dev/null || echo \"default\")\n            echo \"export AWS_PROFILE=\\\"$aws_profile\\\"\" >> \"$CLAUDE_ENV_FILE\"\n            echo \"  AWS_PROFILE=$aws_profile\" >&2\n        fi\n    fi\n    \n    # GCP environment\n    if [[ -f \"$HOME/.config/gcloud/properties\" ]]; then\n        echo \"export GCLOUD_PROJECT=$(gcloud config get-value project 2>/dev/null || echo \\\"\\\")\\ \" >> \"$CLAUDE_ENV_FILE\"\n        echo \"  GCP project configured\" >&2\n    fi\n    \n    # Disable interactive prompts for cloud CLIs\n    echo \"export CLOUDSDK_CORE_DISABLE_PROMPTS=True\" >> \"$CLAUDE_ENV_FILE\"\n    echo \"export TF_INPUT=false\" >> \"$CLAUDE_ENV_FILE\"\n    \n    echo \"✅ Cloud environment configured\" >&2\nfi\n\nexit 0\n'",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

## Docker Environment and Container Setup

Configure Docker settings and container runtime environment:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash -c '\necho \"🐳 Configuring Docker environment...\" >&2\n\nif [[ -n \"$CLAUDE_ENV_FILE\" ]]; then\n    # Check if Docker is available\n    if command -v docker &> /dev/null; then\n        # Set Docker buildkit for better builds\n        echo \"export DOCKER_BUILDKIT=1\" >> \"$CLAUDE_ENV_FILE\"\n        echo \"export BUILDKIT_PROGRESS=plain\" >> \"$CLAUDE_ENV_FILE\"\n        \n        # Get Docker context\n        if command -v docker context &> /dev/null; then\n            context=$(docker context show 2>/dev/null || echo \"default\")\n            echo \"export DOCKER_CONTEXT=\\\"$context\\\"\" >> \"$CLAUDE_ENV_FILE\"\n            echo \"  Docker context: $context\" >&2\n        fi\n        \n        echo \"✅ Docker environment ready\" >&2\n    else\n        echo \"⚠️ Docker not available\" >&2\n    fi\nfi\n\nexit 0\n'",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

## Complete Monorepo Environment Setup

Advanced example setting up multiple tools for a monorepo project:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash -c '\necho \"🚀 Initializing monorepo environment...\" >&2\nset -e\n\nif [[ -z \"$CLAUDE_ENV_FILE\" ]]; then\n    echo \"❌ CLAUDE_ENV_FILE not available\" >&2\n    exit 1\nfi\n\n# Detect monorepo type\necho \"🔍 Detecting project structure...\" >&2\n\nif [[ -f \"pnpm-workspace.yaml\" ]]; then\n    echo \"  pnpm monorepo detected\" >&2\n    echo \"export MONOREPO_TYPE=pnpm\" >> \"$CLAUDE_ENV_FILE\"\n    echo \"export PACKAGE_MANAGER=pnpm\" >> \"$CLAUDE_ENV_FILE\"\nelif [[ -f \"lerna.json\" ]]; then\n    echo \"  Lerna monorepo detected\" >&2\n    echo \"export MONOREPO_TYPE=lerna\" >> \"$CLAUDE_ENV_FILE\"\n    echo \"export PACKAGE_MANAGER=npm\" >> \"$CLAUDE_ENV_FILE\"\nelif [[ -f \"turbo.json\" ]]; then\n    echo \"  Turbo monorepo detected\" >&2\n    echo \"export MONOREPO_TYPE=turbo\" >> \"$CLAUDE_ENV_FILE\"\n    echo \"export PACKAGE_MANAGER=npm\" >> \"$CLAUDE_ENV_FILE\"\nfi\n\n# Node version setup\nif [[ -f \".nvmrc\" ]]; then\n    echo \"  Setting up Node version...\" >&2\n    cat >> \"$CLAUDE_ENV_FILE\" << '\"'\"'NVMEOF'\"'\"'\nexport NVM_DIR=\"$HOME/.nvm\"\n[[ -s \"$NVM_DIR/nvm.sh\" ]] && source \"$NVM_DIR/nvm.sh\"\n[[ -f \".nvmrc\" ]] && nvm use\nNVMEOF\nfi\n\n# Build cache setup\nif [[ ! -d \".build-cache\" ]]; then\n    mkdir -p \".build-cache\" 2>/dev/null || true\nfi\necho \"export BUILD_CACHE_DIR=\\\"$(pwd)/.build-cache\\\"\" >> \"$CLAUDE_ENV_FILE\"\n\n# Package manager aliases\ncat >> \"$CLAUDE_ENV_FILE\" << '\"'\"'ALIASEOF'\"'\"'\nalias pn=\"pnpm\"\nalias pm=\"pnpm\"\nalias pr=\"pnpm run\"\nalias prb=\"pnpm run build\"\nalias prt=\"pnpm run test\"\nALIASEOF\n\necho \"✅ Monorepo environment initialized\" >&2\nexit 0\n'",
            "timeout": 20
          }
        ]
      }
    ]
  }
}
```

## Environment-Specific Configuration

Load different environment variables based on detected environment or configuration:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash -c '\necho \"🎯 Loading environment-specific configuration...\" >&2\n\nif [[ -z \"$CLAUDE_ENV_FILE\" ]]; then\n    exit 1\nfi\n\n# Determine environment\nENV=\"development\"\nif [[ -f \".env.production\" ]]; then\n    ENV=\"production\"\nelif [[ -f \".env.staging\" ]]; then\n    ENV=\"staging\"\nelif [[ -f \".env.test\" ]]; then\n    ENV=\"test\"\nfi\n\necho \"export ENVIRONMENT=\\\"$ENV\\\"\" >> \"$CLAUDE_ENV_FILE\"\necho \"  Environment: $ENV\" >&2\n\n# Load environment-specific file\nif [[ -f \".env.$ENV\" ]]; then\n    echo \"  Loading .env.$ENV\" >&2\n    # Safely export vars from .env file (avoiding secrets)\n    grep -v \"^#\" \".env.$ENV\" | grep \"^[^=]*=\" | while IFS=\"=\" read -r key value; do\n        # Skip sensitive variables\n        if [[ ! \"$key\" =~ ^(SECRET|PASSWORD|TOKEN|KEY|CREDENTIAL) ]]; then\n            echo \"export $key=\\\"$value\\\"\" >> \"$CLAUDE_ENV_FILE\"\n        fi\n    done 2>/dev/null || true\nfi\n\n# Load generic .env\nif [[ -f \".env\" ]] && [[ \"$ENV\" != \"production\" ]]; then\n    echo \"  Loading .env\" >&2\n    grep -v \"^#\" \".env\" | grep \"^[^=]*=\" | while IFS=\"=\" read -r key value; do\n        if [[ ! \"$key\" =~ ^(SECRET|PASSWORD|TOKEN|KEY|CREDENTIAL) ]]; then\n            echo \"export $key=\\\"$value\\\"\" >> \"$CLAUDE_ENV_FILE\"\n        fi\n    done 2>/dev/null || true\nfi\n\necho \"✅ Environment configuration loaded\" >&2\nexit 0\n'",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
```

## Rust/Cargo Environment Setup

Configure Rust toolchain and Cargo settings for the session:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash -c '\necho \"🦀 Setting up Rust environment...\" >&2\n\nif [[ -n \"$CLAUDE_ENV_FILE\" ]] && command -v rustup &> /dev/null; then\n    # Check for rust-toolchain.toml or .rust-version\n    if [[ -f \"rust-toolchain.toml\" ]] || [[ -f \".rust-version\" ]]; then\n        echo \"  rustup toolchain override detected\" >&2\n        \n        # Let rustup handle the override for new shells\n        cat >> \"$CLAUDE_ENV_FILE\" << \"EOF\"\n# Rust toolchain will be set by rustup override\nif command -v rustup &> /dev/null; then\n    rustup override show > /dev/null 2>&1 || true\nfi\nEOF\n    fi\n    \n    # Cargo optimization flags\n    echo \"export CARGO_BUILD_JOBS=4\" >> \"$CLAUDE_ENV_FILE\"\n    echo \"export CARGO_INCREMENTAL=1\" >> \"$CLAUDE_ENV_FILE\"\n    \n    rust_version=$(rustc --version 2>/dev/null | awk '\"'\"'{print $2}'\"'\"')\n    echo \"  Rust version: $rust_version\" >&2\n    echo \"✅ Rust environment configured\" >&2\nelse\n    echo \"ℹ️ Rust toolchain not available\" >&2\nfi\n\nexit 0\n'",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
```

## Go Environment Setup

Configure Go workspace and development environment:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash -c '\necho \"🐹 Setting up Go environment...\" >&2\n\nif [[ -n \"$CLAUDE_ENV_FILE\" ]] && command -v go &> /dev/null; then\n    # Set GOPATH\n    gopath=$(go env GOPATH)\n    echo \"export GOPATH=\\\"$gopath\\\"\" >> \"$CLAUDE_ENV_FILE\"\n    \n    # Add GOPATH/bin to PATH if needed\n    echo \"export PATH=\\\"$gopath/bin:\\$PATH\\\"\" >> \"$CLAUDE_ENV_FILE\"\n    \n    # Enable Go module mode (for go 1.11+)\n    echo \"export GO111MODULE=on\" >> \"$CLAUDE_ENV_FILE\"\n    \n    # Optional: Setup go linting tools cache\n    echo \"export GOLANGCI_LINT_CACHE=\\\"$(pwd)/.golangci-cache\\\"\" >> \"$CLAUDE_ENV_FILE\"\n    \n    go_version=$(go version | awk '\"'\"'{print $3}'\"'\"')\n    echo \"  Go version: $go_version\" >&2\n    echo \"✅ Go environment configured\" >&2\nelse\n    echo \"ℹ️ Go not available\" >&2\nfi\n\nexit 0\n'",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

## Real-World Pattern: Multi-Language Full Stack

Complete example for a full-stack application with multiple language runtimes:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 << 'PYEOF'\nimport json\nimport os\nimport subprocess\nimport sys\nfrom pathlib import Path\n\nenv_file = os.environ.get('CLAUDE_ENV_FILE')\nif not env_file:\n    sys.exit(1)\n\nprint('🛠️  Setting up full-stack development environment...', file=sys.stderr)\n\nenv_exports = []\n\n# Detect and setup Node.js\nif Path('.nvmrc').exists() or Path('package.json').exists():\n    print('  📦 Node.js project detected', file=sys.stderr)\n    \n    nvm_init = '''\nexport NVM_DIR=\"$HOME/.nvm\"\nif [[ -s \"$NVM_DIR/nvm.sh\" ]]; then\n    source \"$NVM_DIR/nvm.sh\"\n    [[ -f \".nvmrc\" ]] && nvm use\nfi\n'''\n    env_exports.append(nvm_init)\n    \n    # Detect package manager\n    if Path('pnpm-lock.yaml').exists():\n        env_exports.append('export PACKAGE_MANAGER=pnpm')\n    elif Path('yarn.lock').exists():\n        env_exports.append('export PACKAGE_MANAGER=yarn')\n    else:\n        env_exports.append('export PACKAGE_MANAGER=npm')\n\n# Detect and setup Python\nif Path('.python-version').exists() or Path('pyproject.toml').exists():\n    print('  🐍 Python project detected', file=sys.stderr)\n    \n    venv_paths = ['.venv', 'venv', 'env']\n    venv_found = None\n    for vpath in venv_paths:\n        if Path(f'{vpath}/bin/activate').exists():\n            venv_found = vpath\n            break\n    \n    if venv_found:\n        env_exports.append(f'source {venv_found}/bin/activate')\n    \n    # pyenv support\n    if Path(f'{os.path.expanduser(\"~\")}/.pyenv/shims').exists():\n        env_exports.append('export PATH=\"$HOME/.pyenv/shims:$PATH\"')\n        env_exports.append('[[ -s \"$HOME/.pyenv/init\" ]] && eval \"$(pyenv init -)\"')\n\n# Detect and setup Rust\nif Path('Cargo.toml').exists():\n    print('  🦀 Rust project detected', file=sys.stderr)\n    \n    rustup_init = '''\nif [[ -s \"$HOME/.cargo/env\" ]]; then\n    source \"$HOME/.cargo/env\"\nfi\n'''\n    env_exports.append(rustup_init)\n    env_exports.append('export CARGO_BUILD_JOBS=4')\n\n# Detect and setup Go\nif Path('go.mod').exists():\n    print('  🐹 Go project detected', file=sys.stderr)\n    \n    try:\n        result = subprocess.run(['go', 'env', 'GOPATH'], \n                              capture_output=True, text=True, timeout=5)\n        if result.returncode == 0:\n            gopath = result.stdout.strip()\n            env_exports.append(f'export GOPATH=\"{gopath}\"')\n            env_exports.append(f'export PATH=\"{gopath}/bin:$PATH\"')\n    except:\n        pass\n\n# Common exports\nenv_exports.extend([\n    f'export PROJECT_ROOT=\"{os.getcwd()}\"',\n    'export DOCKER_BUILDKIT=1',\n])\n\n# Write all exports to the session file\nwith open(env_file, 'a') as f:\n    for export_line in env_exports:\n        f.write(export_line + '\\n')\n\nprint('✅ Multi-language environment configured', file=sys.stderr)\nsys.exit(0)\nPYEOF",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

## Best Practices

### 1. Always Check for $CLAUDE_ENV_FILE
```bash
if [[ -z \"$CLAUDE_ENV_FILE\" ]]; then
    echo \"❌ CLAUDE_ENV_FILE not available (SessionStart only)\" >&2
    exit 1
fi
```

### 2. Use Absolute Paths
```bash
# Good
echo \"export PATH=\\\"$(pwd)/bin:\\$PATH\\\"\" >> \"$CLAUDE_ENV_FILE\"

# Bad - won't work if paths change
echo \"export MY_VAR=./relative/path\" >> \"$CLAUDE_ENV_FILE\"
```

### 3. Handle Missing Tools Gracefully
```bash
if command -v nvm &> /dev/null; then
    # Setup nvm
else
    echo \"⚠️ nvm not found, skipping Node version setup\" >&2
fi
```

### 4. Provide Clear Feedback
```bash
echo \"✅ PostgreSQL environment configured\" >&2
echo \"  PGHOST=localhost\" >&2
echo \"  PGPORT=5432\" >&2
```

### 5. Quote Variable Expansions Properly
```bash
# When writing to env file, double-quote to allow $VAR expansion later
echo \"export PATH=\\\"\\$HOME/.local/bin:\\$PATH\\\"\" >> \"$CLAUDE_ENV_FILE\"

# This expands $HOME now (wrong in env file)
echo \"export MY_PATH=$HOME/bin\" >> \"$CLAUDE_ENV_FILE\"
```

### 6. Test Environment Persistence
After creating a SessionStart hook with environment setup:

```bash
# In Claude Code's terminal, verify variables persist:
echo $NODE_ENV
cd /tmp  # Change directory to different location
echo $PROJECT_ROOT  # Should still be set from SessionStart
```

## Troubleshooting

### Environment Variables Not Persisting
- **Issue**: Variables set in SessionStart hook don't appear in bash commands
- **Cause**: Hook might not be configured in settings.json, or `$CLAUDE_ENV_FILE` not being used
- **Fix**: Verify hook is in `SessionStart` section, check file is being written to

### $CLAUDE_ENV_FILE Not Found
- **Issue**: `CLAUDE_ENV_FILE` is empty or undefined
- **Cause**: Not running in SessionStart hook, or running in wrong context
- **Fix**: `$CLAUDE_ENV_FILE` only available in SessionStart hooks; use PostToolUse for other scenarios

### Sourcing Virtual Environments
- **Issue**: Virtual environment activation doesn't persist
- **Cause**: Source command doesn't apply across shell invocations
- **Fix**: Write activation command to `$CLAUDE_ENV_FILE` instead of running directly

### PATH Modifications Not Working
- **Issue**: Added directories not found in subsequent commands
- **Cause**: PATH syntax error or not properly escaped
- **Fix**: Use `echo \"export PATH=\\\"new:\\$PATH\\\"\"` format (note the escaped `$`)

### Tool Commands Not Found
- **Issue**: Tools installed but not available in later commands
- **Cause**: Tool's activation script not sourced in env file
- **Fix**: Include activation script in `$CLAUDE_ENV_FILE` (e.g., nvm.sh, pyenv init)

## Performance Considerations

- **SessionStart runs once**: Setup overhead is paid only at session start
- **File size matters**: Keep env file under 100KB; too many variables can slow startup
- **Source carefully**: Only source necessary scripts; avoid sourcing entire home rc files
- **Lazy loading**: For expensive setups, defer initialization until needed in hooks

