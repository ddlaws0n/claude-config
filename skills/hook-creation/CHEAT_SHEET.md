# Hook Creation Cheat Sheet

Quick reference for common hook patterns and commands.

## Quick Start Commands

### Create Basic Hook Structure
```bash
mkdir -p .claude/hooks

# Create settings.json
cat > .claude/settings.json << 'EOF'
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/hook.sh",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
EOF

# Create hook script
cat > .claude/hooks/hook.sh << 'EOF'
#!/bin/bash
input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')
echo "Processing: $file_path" >&2
exit 0
EOF

chmod +x .claude/hooks/hook.sh
```

## Common Hook Patterns

### 1. Python File Processing
```bash
#!/bin/bash
input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

if [[ "$file_path" == *.py ]]; then
    echo "🐍 Processing Python: $(basename "$file_path")" >&2
    uv run ruff format "$file_path" && echo "  ✓ Formatted" >&2
    uv run ruff check --fix "$file_path" && echo "  ✓ Linted" >&2
fi

exit 0
```

### 2. TypeScript/JavaScript Processing
```bash
#!/bin/bash
input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

if [[ "$file_path" =~ \.(ts|tsx|js|jsx)$ ]]; then
    echo "🟨 Processing TypeScript: $(basename "$file_path")" >&2

    if command -v biome &> /dev/null; then
        biome check --write --unsafe "$file_path" 2>&1 && echo "  ✓ Formatted" >&2
    elif command -v prettier &> /dev/null; then
        prettier --write "$file_path" 2>&1 && echo "  ✓ Formatted" >&2
    fi
fi

exit 0
```

### 3. Security Check
```python
#!/usr/bin/env python3
import json, sys, os

SENSITIVE_FILES = ['.env', 'secrets.', '.aws/', '.kube/', 'id_rsa', '*.key']

data = json.load(sys.stdin)
file_path = data.get('tool_input', {}).get('file_path', '')

for pattern in SENSITIVE_FILES:
    if pattern in file_path or file_path.endswith(pattern.replace('*', '')):
        print(f'❌ Access denied to sensitive file: {file_path}', file=sys.stderr)
        sys.exit(2)

exit 0
```

### 4. File Protection
```python
#!/usr/bin/env python3
import json, sys, os
from pathlib import Path

data = json.load(sys.stdin)
command = data.get('tool_input', {}).get('command', '')

# Dangerous commands
dangerous = ['rm -rf /', 'rm -rf /*', ':(){ :|:& };:']

for dangerous_cmd in dangerous:
    if dangerous_cmd in command:
        print(f'❌ Dangerous command blocked: {command[:50]}...', file=sys.stderr)
        sys.exit(2)

exit 0
```

### 5. Test Runner
```python
#!/usr/bin/env python3
import json, sys, subprocess
from pathlib import Path

data = json.load(sys.stdin)
file_path = data.get('tool_input', {}).get('file_path', '')

if file_path.endswith('.py'):
    base = Path(file_path).stem
    test_file = f"test_{base}.py"

    if Path(test_file).exists():
        print(f"🧪 Running tests for {base}...", file=sys.stderr)
        result = subprocess.run(['pytest', test_file, '-v'], capture_output=True, text=True)
        if result.returncode == 0:
            print("  ✓ Tests passed", file=sys.stderr)

exit 0
```

### 6. Notification Hook
```bash
#!/bin/bash
input=$(cat)
message=$(echo "$input" | jq -r '.message // empty')

if [[ "$OSTYPE" == "darwin"* ]]; then
    osascript -e "display notification \"$message\" with title \"Claude Code\""
elif command -v notify-send &> /dev/null; then
    notify-send "Claude Code" "$message"
fi

exit 0
```

### 7. Metrics Logger
```python
#!/usr/bin/env python3
import json, sys, os
from datetime import datetime

data = json.load(sys.stdin)
tool_name = data.get('tool_name', '')

# Log to daily file
log_dir = os.path.expanduser('~/.claude/logs')
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, f'activity-{datetime.now().strftime("%Y-%m-%d")}.jsonl')

with open(log_file, 'a') as f:
    json.dump({
        'timestamp': datetime.now().isoformat(),
        'tool': tool_name
    }, f)
    f.write('\n')

exit 0
```

## Configuration Templates

### Python Project Setup
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/python-format.sh",
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
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/python-test.sh",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

### TypeScript Project Setup
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/ts-format.sh",
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
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/ts-compile.sh",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

### Security Setup
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/security-check.sh",
            "timeout": 5
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/secret-scan.sh",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

## Common Commands

### Testing Hooks
```bash
# Test hook with sample input
echo '{"tool_name": "Write", "tool_input": {"file_path": "test.py"}}' | .claude/hooks/hook.sh

# Check hook permissions
ls -la .claude/hooks/

# Validate JSON
cat .claude/settings.json | jq .
```

### Debugging
```bash
# Run Claude with debug output
claude --debug

# Check hooks configuration
/hooks

# View hook logs
tail -f ~/.claude/hooks.log
```

### File Operations
```python
# Read file safely
with open(file_path, 'r') as f:
    content = f.read()

# Write file safely
with open(file_path, 'w') as f:
    f.write(content)

# Check file exists
if os.path.exists(file_path):
    # Process file
```

## Command Mapping

| Event | When to Use | Common Matchers | Hook Types |
|-------|-------------|-----------------|-----------|
| `PreToolUse` | Before tool execution | Tool-specific (`Bash`, `Write`) | command, prompt |
| `PostToolUse` | After tool execution | Tool-specific (`Edit`, `Write`) | command |
| `Stop` | When Claude finishes | No matcher needed | command |
| `SubagentStop` | Subagent finishes | No matcher needed | command |
| `Notification` | Claude notifications | `permission_prompt`, `idle_prompt` | command |
| `PermissionRequest` | Permission dialog shown | Tool-specific (`Bash`, `Write`) | command, prompt |
| `SessionStart` | Session starts | `startup`, `resume`, `clear`, `compact` | command |
| `SessionEnd` | Session ends | No matcher needed | command |
| `UserPromptSubmit` | User submits prompt | No matcher needed | command, prompt |
| `PreCompact` | Before context compaction | `manual`, `auto` | command |

## Advanced Features Quick Reference

### Prompt-Based Hooks
```json
{
  "type": "prompt",
  "prompt": "Your evaluation prompt here with $ARGUMENTS for context",
  "timeout": 30,
  "systemPrompt": "Optional system message"
}
```

### SessionStart Environment Variables ($CLAUDE_ENV_FILE)
```bash
# In SessionStart hook:
echo "PROJECT_TYPE=python" >> "$CLAUDE_ENV_FILE"
echo "BUILD_CMD=make build" >> "$CLAUDE_ENV_FILE"
echo "TEST_CMD=pytest" >> "$CLAUDE_ENV_FILE"
```

### Environment Detection (CLAUDE_CODE_REMOTE)
```bash
if [ "$CLAUDE_CODE_REMOTE" = "true" ]; then
    # Running remotely (SSH, container, etc.)
    TIMEOUT=60
else
    # Running locally
    TIMEOUT=10
fi
```

### PermissionRequest with Input Modification
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "permissionDecision": "allow",
    "updatedInput": {
      "command": "npm run build -- --production",
      "description": "Modified for production"
    }
  }
}
```

### UserPromptSubmit Context Injection
```json
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "injectedContext": "Relevant project context",
    "systemMessage": "Framework: React 18, Node: v20"
  }
}
```

### PreCompact Event Handling
```python
if data.get('matcher') == 'manual':
    print("Manual compact requested", file=sys.stderr)
elif data.get('matcher') == 'auto':
    print("Automatic compact triggered", file=sys.stderr)
```

## Exit Codes

| Code | Meaning | Use Case |
|------|---------|----------|
| `0` | Success | Operation completed, continue |
| `1` | Warning | Non-critical error, continue |
| `2` | Block | Critical error, stop operation |

## Quick Reference

### Input Extraction
```bash
# Bash
input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name // empty')
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

# Python
import json, sys
data = json.load(sys.stdin)
tool_name = data.get('tool_name', '')
file_path = data.get('tool_input', {}).get('file_path', '')
```

### Output Formats
```python
# Simple success
print("✅ Operation complete", file=sys.stderr)
sys.exit(0)

# Block with error
print("❌ Operation failed", file=sys.stderr)
sys.exit(2)

# JSON output
output = {
    "decision": "block",
    "reason": "Must fix issues"
}
print(json.dumps(output))
sys.exit(0)
```

### Tool Detection
```python
# File extension to language
ext = Path(file_path).suffix.lower()
if ext == '.py':
    # Python
elif ext in ['.ts', '.js']:
    # TypeScript/JavaScript
```

### Tool-Specific Operations

**NotebookEdit Operations:**
```python
notebook_path = data.get('tool_input', {}).get('notebook_path', '')
cell_type = data.get('tool_input', {}).get('cell_type', 'code')

# React to Jupyter notebook edits
if cell_type == 'code':
    print("🔧 Code cell modified", file=sys.stderr)
```

**TodoWrite Operations:**
```python
todos = data.get('tool_input', {}).get('todos', [])

# Track todo changes
for todo in todos:
    if todo.get('status') == 'completed':
        print(f"✅ Task complete: {todo.get('content')}", file=sys.stderr)
```

**WebSearch Operations:**
```python
query = data.get('tool_input', {}).get('query', '')

# Log searches
with open('~/.claude/searches.log', 'a') as f:
    f.write(f"{datetime.now().isoformat()} - {query}\n")
```

**MCP Tool Operations:**
```python
tool_name = data.get('tool_name', '')

if tool_name.startswith('mcp__'):
    # Extract MCP source and tool
    source, tool = tool_name.replace('mcp__', '').split('__', 1)
    print(f"MCP: {source}/{tool}", file=sys.stderr)
```

### Environment Variables
```bash
# Project directory
echo "$CLAUDE_PROJECT_DIR"

# Plugin directory (in plugins)
echo "$CLAUDE_PLUGIN_ROOT"

# Session file (SessionStart only)
echo "$CLAUDE_ENV_FILE"
```

## Troubleshooting

### Hook Not Running
1. Check syntax: `cat .claude/settings.json | jq`
2. Check permissions: `ls -la .claude/hooks/`
3. Restart Claude Code
4. Use `claude --debug`

### Command Not Found
1. Use absolute paths
2. Check `PATH`: `echo $PATH`
3. Install missing tools

### Hook Too Slow
1. Move to Stop hook if comprehensive
2. Use tool matching to avoid unnecessary runs
3. Add timeouts in configuration

### Permissions Issues
```bash
# Make executable
chmod +x .claude/hooks/script.sh

# Check ownership
ls -la .claude/hooks/
```

### JSON Errors
```bash
# Validate JSON
cat .claude/settings.json | jq .

# Format JSON
cat .claude/settings.json | jq . > temp.json && mv temp.json .claude/settings.json
```