# Hook Creation Reference

Complete reference guide for Claude Code hooks, including API documentation, event types, and advanced patterns.

## Table of Contents

1. [Hook Event Types](#hook-event-types)
2. [Input/Output Formats](#inputoutput-formats)
3. [Configuration Schema](#configuration-schema)
4. [Decision Control](#decision-control)
5. [Error Handling](#error-handling)
6. [Best Practices](#best-practices)
7. [Advanced Patterns](#advanced-patterns)

## Hook Event Types

### PreToolUse
Runs before tool execution. Can block or modify tool calls.

**Common Use Cases:**
- Security validation
- Input sanitization
- Permission checks
- Command modification

**Available Matchers:**
- `Bash` - Shell commands
- `Read` - File reading
- `Write` - File writing
- `Edit` - File editing
- `Grep` - Content search
- `Glob` - File pattern matching
- `WebFetch` - Web requests
- `Task` - Subagent tasks

**Input Schema:**
```json
{
  "session_id": "string",
  "transcript_path": "string",
  "cwd": "string",
  "permission_mode": "default|plan|acceptEdits|bypassPermissions",
  "hook_event_name": "PreToolUse",
  "tool_name": "string",
  "tool_input": {
    // Tool-specific parameters
  },
  "tool_use_id": "string"
}
```

### PostToolUse
Runs after successful tool execution.

**Common Use Cases:**
- Code formatting
- File processing
- Notifications
- Logging

**Input Schema:**
```json
{
  "session_id": "string",
  "transcript_path": "string",
  "cwd": "string",
  "permission_mode": "string",
  "hook_event_name": "PostToolUse",
  "tool_name": "string",
  "tool_input": {
    // Tool-specific parameters
  },
  "tool_response": {
    // Tool response data
  },
  "tool_use_id": "string"
}
```

### Stop
Runs when Claude finishes responding.

**Common Use Cases:**
- Quality checks
- Build verification
- Comprehensive testing
- Session cleanup

**Input Schema:**
```json
{
  "session_id": "string",
  "transcript_path": "string",
  "permission_mode": "string",
  "hook_event_name": "Stop",
  "stop_hook_active": true
}
```

### SubagentStop
Runs when a subagent completes.

**Input Schema:**
```json
{
  "session_id": "string",
  "transcript_path": "string",
  "permission_mode": "string",
  "hook_event_name": "SubagentStop",
  "stop_hook_active": true
}
```

### PermissionRequest
Runs when permission dialog is shown.

**Matchers:** Same as PreToolUse

**Common Use Cases:**
- Auto-approving safe operations
- Context-aware permission decisions

### Notification
Runs for Claude Code notifications.

**Common Matchers:**
- `permission_prompt` - Permission requests
- `idle_prompt` - Waiting for input
- `auth_success` - Authentication success
- `elicitation_dialog` - MCP tool elicitation

**Input Schema:**
```json
{
  "session_id": "string",
  "transcript_path": "string",
  "cwd": "string",
  "permission_mode": "string",
  "hook_event_name": "Notification",
  "message": "string",
  "notification_type": "string"
}
```

### SessionStart
Runs at session start or resume.

**Common Matchers:**
- `startup` - Fresh start
- `resume` --resume or --continue
- `clear` - /clear command
- `compact` - After compact

**Common Use Cases:**
- Environment setup
- Dependency installation
- Context loading

### SessionEnd
Runs when session ends.

**Common Use Cases:**
- Cleanup tasks
- Session logging
- Resource release

**Input Schema:**
```json
{
  "session_id": "string",
  "transcript_path": "string",
  "cwd": "string",
  "permission_mode": "string",
  "hook_event_name": "SessionEnd",
  "reason": "clear|logout|prompt_input_exit|other"
}
```

### UserPromptSubmit
Runs when user submits a prompt.

**Common Use Cases:**
- Prompt validation
- Context injection
- Input filtering

**Input Schema:**
```json
{
  "session_id": "string",
  "transcript_path": "string",
  "cwd": "string",
  "permission_mode": "string",
  "hook_event_name": "UserPromptSubmit",
  "prompt": "string"
}
```

### PreCompact
Runs before context compaction.

**Common Matchers:**
- `manual` - /compact command
- `auto` - Automatic compaction

**Input Schema:**
```json
{
  "session_id": "string",
  "transcript_path": "string",
  "cwd": "string",
  "permission_mode": "string",
  "hook_event_name": "PreCompact",
  "matcher": "manual|auto"
}
```

## Prompt-Based Hooks

### Overview
Prompt-based hooks use the Claude LLM to make intelligent decisions about tool execution, workflow steps, and complex evaluations.

**Configuration:**
```json
{
  "type": "prompt",
  "prompt": "Your decision prompt here. Use $ARGUMENTS for dynamic context.",
  "timeout": 30,
  "systemPrompt": "Optional custom system message"
}
```

### Use Cases
- Intelligent permission decisions based on code analysis
- Workflow gate decisions (proceed/block/request approval)
- Architecture validation and design reviews
- Security assessment of operations
- Context-aware suggestion generation

### Example: Database Migration Review
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Analyze this database migration command for safety and rollback capability:\n$ARGUMENTS\n\nDecide: allow, deny, or ask for clarification.",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

## SessionStart $CLAUDE_ENV_FILE

### Overview
The `$CLAUDE_ENV_FILE` environment variable, available during SessionStart hooks, points to a temporary file where hooks can write environment variables to be injected into the session.

### Usage Pattern

**SessionStart Hook:**
```python
#!/usr/bin/env python3
import json, sys, os

data = json.load(sys.stdin)
env_file = os.getenv('CLAUDE_ENV_FILE', '')

if env_file:
    with open(env_file, 'a') as f:
        f.write('PROJECT_TYPE=python\n')
        f.write('BUILD_CMD=make build\n')
        f.write('TEST_CMD=pytest\n')

exit(0)
```

### Available in These Hooks
- `SessionStart` - Primary use case
- `PreToolUse` (limited) - May be available depending on execution context

### Common Patterns
```bash
# Detect project type and set variables
if [ -f "pyproject.toml" ]; then
    echo "PROJECT_TYPE=python" >> "$CLAUDE_ENV_FILE"
elif [ -f "package.json" ]; then
    echo "PROJECT_TYPE=nodejs" >> "$CLAUDE_ENV_FILE"
fi

# Set build tools
echo "BUILD_TOOL=$(which python || which node)" >> "$CLAUDE_ENV_FILE"
```

## CLAUDE_CODE_REMOTE - Environment Detection

### Overview
The `CLAUDE_CODE_REMOTE` environment variable indicates whether Claude Code is running locally or remotely.

### Values
- Not set or empty - Local execution
- `"true"` or `"1"` - Remote execution (SSH, container, etc.)
- Other values - Unknown environment

### Usage Example
```python
import os

is_remote = os.getenv('CLAUDE_CODE_REMOTE') in ('true', '1')

if is_remote:
    # Use network-optimized operations
    subprocess.run(['sync-cache-remote.sh'])
else:
    # Use local optimizations
    subprocess.run(['sync-cache-local.sh'])
```

### Common Patterns
```bash
# Adjust timeouts for remote
if [ "$CLAUDE_CODE_REMOTE" = "true" ]; then
    TIMEOUT=60  # Remote is slower
else
    TIMEOUT=10  # Local is faster
fi

# Use appropriate paths
if [ "$CLAUDE_CODE_REMOTE" = "true" ]; then
    CONFIG_PATH="/remote/config"
else
    CONFIG_PATH="$HOME/.config"
fi
```

## PermissionRequest with updatedInput

### Overview
PermissionRequest hooks can modify the tool input before showing the permission dialog, enabling intelligent parameter adjustment.

### Schema
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "permissionDecision": "allow|deny|ask",
    "updatedInput": {
      "parameter_name": "new_value",
      "another_param": "adjusted_value"
    }
  }
}
```

### Example: Auto-Adjust Build Parameters
```python
output = {
    "hookSpecificOutput": {
        "hookEventName": "PermissionRequest",
        "permissionDecision": "allow",
        "updatedInput": {
            "command": "npm run build -- --production",
            "description": "Modified to production mode"
        }
    }
}
```

## UserPromptSubmit with Context Injection

### Overview
UserPromptSubmit hooks can inject context into Claude's understanding via system messages and response modification.

### Full Schema
```json
{
  "session_id": "string",
  "transcript_path": "string",
  "cwd": "string",
  "permission_mode": "string",
  "hook_event_name": "UserPromptSubmit",
  "prompt": "string"
}
```

### Output Control
```json
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "injectedContext": "Relevant context about the project or task",
    "systemMessage": "Framework: React 18, Package manager: pnpm, Node: v20"
  }
}
```

### Context Injection Patterns

**Project Type Detection:**
```python
cwd = data.get('cwd', '')
context = ""

if os.path.exists(os.path.join(cwd, 'pyproject.toml')):
    context = "Python project using Poetry"
elif os.path.exists(os.path.join(cwd, 'package.json')):
    with open(os.path.join(cwd, 'package.json')) as f:
        pkg = json.load(f)
        context = f"Node.js project: {pkg.get('name')} using {pkg.get('packageManager')}"
```

**Recent Errors Injection:**
```python
error_log = os.path.expanduser('~/.claude/error_log.json')
recent_errors = []

if os.path.exists(error_log):
    with open(error_log) as f:
        recent_errors = json.load(f)[-5:]  # Last 5 errors

context = f"Recent issues: {json.dumps(recent_errors, indent=2)}"
```

**Team Standards Injection:**
```python
standards_file = os.path.join(cwd, '.claude', 'coding-standards.md')
context = ""

if os.path.exists(standards_file):
    with open(standards_file) as f:
        context = f.read()
```

## Input/Output Formats

### Reading Hook Input

**Python Example:**
```python
import json
import sys

# Read JSON from stdin
data = json.load(sys.stdin)

# Extract values
tool_name = data.get('tool_name', '')
file_path = data.get('tool_input', {}).get('file_path', '')
```

**Bash Example:**
```bash
# Read JSON input
input=$(cat)

# Extract values with jq
tool_name=$(echo "$input" | jq -r '.tool_name // empty')
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')
```

### Hook Output

#### Simple Exit Codes
```bash
# Success (continue)
exit 0

# Non-blocking warning
exit 1

# Block operation (stderr shown to Claude)
exit 2
```

#### JSON Output (exit code 0)

**Common Fields:**
```json
{
  "continue": true,  // Allow Claude to continue
  "stopReason": "string",  // Message when continue=false
  "suppressOutput": true,  // Hide stdout from transcript
  "systemMessage": "string"  // Warning to user
}
```

**PreToolUse Decision Control:**
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow|deny|ask",
    "permissionDecisionReason": "string",
    "updatedInput": {
      "field": "newValue"
    }
  }
}
```

**PostToolUse Feedback:**
```json
{
  "decision": "block",
  "reason": "Explanation for Claude",
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "Extra information"
  }
}
```

**Stop Hook Control:**
```json
{
  "decision": "block",  // or undefined to allow stopping
  "reason": "Claude must continue: explain why"
}
```

## Configuration Schema

### Settings Structure
```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "ToolPattern|*|",
        "hooks": [
          {
            "type": "command|prompt",
            "command": "string",  // For command type
            "prompt": "string",   // For prompt type
            "timeout": 30  // Optional timeout in seconds
          }
        ]
      }
    ]
  }
}
```

### Matcher Patterns

**Exact Match:**
```json
{
  "matcher": "Write"
}
```

**Multiple Tools:**
```json
{
  "matcher": "Edit|Write"
}
```

**Regex Pattern:**
```json
{
  "matcher": "Notebook.*"
}
```

**Match All:**
```json
{
  "matcher": "*"
}
```

**Empty String:**
```json
{
  "matcher": ""
}
```

### Project-Specific Scripts

Use `$CLAUDE_PROJECT_DIR` for project-relative paths:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/format.sh"
          }
        ]
      }
    ]
  }
}
```

## Decision Control

### PreToolUse Permissions

**Allow Tool:**
```python
output = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "permissionDecisionReason": "Auto-approved: Safe operation"
    }
}
print(json.dumps(output))
```

**Deny Tool:**
```python
output = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "Blocked: Dangerous operation"
    }
}
print(json.dumps(output))
```

**Ask User:**
```python
output = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": "Requires confirmation"
    }
}
print(json.dumps(output))
```

**Modify Tool Input:**
```python
output = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "updatedInput": {
            "command": "npm run lint",
            "description": "Run linter"
        }
    }
}
print(json.dumps(output))
```

### PostToolUse Feedback

**Block with Message:**
```python
output = {
    "decision": "block",
    "reason": "Code contains security issues that must be fixed"
}
print(json.dumps(output))
```

**Add Context:**
```python
output = {
    "hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": "File was formatted with ruff"
    }
}
print(json.dumps(output))
```

### Stop Hook Control

**Prevent Stopping:**
```python
output = {
    "decision": "block",
    "reason": "Type errors found. Please fix before stopping."
}
print(json.dumps(output))
```

**Continue with Warning:**
```python
output = {
    "continue": False,
    "stopReason": "Stopping with unresolved issues",
    "systemMessage": "Some issues remain but continuing anyway"
}
print(json.dumps(output))
```

## Error Handling

### Graceful Failure

**Skip Missing Tools:**
```python
import shutil

if not shutil.which('ruff'):
    print("⚠️ ruff not found, skipping formatting", file=sys.stderr)
    sys.exit(0)  # Continue gracefully
```

**Handle File Not Found:**
```python
file_path = data.get('tool_input', {}).get('file_path', '')
if not os.path.exists(file_path):
    print(f"File not found: {file_path}", file=sys.stderr)
    sys.exit(0)  # Don't block for missing files
```

### Exit Code Strategy

**Exit Code 0 - Success:**
- Operation completed successfully
- Non-critical warnings (stderr shown in verbose mode)
- JSON output processed

**Exit Code 1 - Non-blocking Error:**
- Non-critical error
- stderr shown in verbose mode
- Execution continues

**Exit Code 2 - Blocking Error:**
- Critical error that must be addressed
- stderr shown to Claude as error message
- Execution blocks

## Best Practices

### Performance

**Fast PostToolUse Hooks:**
- Keep operations under 2 seconds
- Use file-specific commands, not project-wide
- Defer expensive operations to Stop hooks

**Example: Fast File Check**
```python
# Fast: Check single file
subprocess.run(['ruff', 'check', file_path])

# Slow: Check entire project
subprocess.run(['ruff', 'check', '.'])
```

### Security

**Validate Inputs:**
```python
file_path = data.get('tool_input', {}).get('file_path', '')
if not file_path or '..' in file_path:
    sys.exit(2)  # Block suspicious paths

# Restrict to project directory
if not file_path.startswith(os.getcwd()):
    sys.exit(2)
```

**Quote Variables:**
```bash
# Bad: vulnerable to injection
rm $file_path

# Good: properly quoted
rm "$file_path"
```

### Reliability

**Fail Open:**
```python
try:
    result = subprocess.run(['format-tool', file_path])
    print("✅ Formatted", file=sys.stderr)
except FileNotFoundError:
    print("⚠️ Formatter not found", file=sys.stderr)
    sys.exit(0)  # Don't block
```

**Use Absolute Paths:**
```json
{
  "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/script.py"
}
```

### Debugging

**Structured Logging:**
```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    filename='/tmp/hooks.log'
)

logging.info(f"Processing file: {file_path}")
```

**Verbose Output:**
```python
# Info for verbose mode (ctrl+o)
print("Processing file...", file=sys.stderr)

# Debug output
if os.getenv('DEBUG'):
    print(f"Debug: {data}", file=sys.stderr)
```

## Advanced Patterns

### Multi-Stage Processing

**Pipeline Pattern:**
```python
def process_file(file_path):
    # Stage 1: Validation
    if not validate_file(file_path):
        return False

    # Stage 2: Formatting
    if not format_file(file_path):
        return False

    # Stage 3: Linting
    if not lint_file(file_path):
        return False

    return True
```

### Conditional Logic

**Project-Specific Logic:**
```python
def get_project_type(cwd):
    if os.path.exists('package.json'):
        return 'nodejs'
    elif os.path.exists('pyproject.toml'):
        return 'python'
    elif os.path.exists('Cargo.toml'):
        return 'rust'
    return 'unknown'

project_type = get_project_type(data.get('cwd', ''))
```

**Tool Availability Detection:**
```python
formatters = []
if shutil.which('ruff'):
    formatters.append('ruff')
if shutil.which('biome'):
    formatters.append('biome')
if shutil.which('prettier'):
    formatters.append('prettier')

# Use first available formatter
if formatters:
    formatter = formatters[0]
```

### State Management

**Simple File-based State:**
```python
def get_state_file():
    return os.path.expanduser('~/.claude/hook_state.json')

def load_state():
    try:
        with open(get_state_file()) as f:
            return json.load(f)
    except:
        return {}

def save_state(state):
    with open(get_state_file(), 'w') as f:
        json.dump(state, f)

# Usage
state = load_state()
state['last_run'] = datetime.now().isoformat()
save_state(state)
```

### Caching

**Debounce Pattern:**
```python
def should_process(file_path, delay=5):
    cache_file = f"/tmp/.claude_debounce_{os.path.basename(file_path)}"

    if os.path.exists(cache_file):
        mtime = os.path.getmtime(cache_file)
        if time.time() - mtime < delay:
            return False

    open(cache_file, 'w').close()
    return True
```

### Parallel Execution

**Non-blocking Operations:**
```python
import subprocess
import threading

def run_in_background(cmd):
    def worker():
        subprocess.run(cmd, capture_output=True)
    thread = threading.Thread(target=worker)
    thread.start()
    return thread

# Run tests in background
if file_path.endswith('.py'):
    run_in_background(['pytest', 'tests/'])
```

### Integration Patterns

**MCP Tool Support:**
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__.*__write.*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 validate-mcp-write.py"
          }
        ]
      }
    ]
  }
}
```

**Plugin Integration:**
```python
# Check for plugin hooks
plugin_dir = os.getenv('CLAUDE_PLUGIN_ROOT')
if plugin_dir:
    script_path = os.path.join(plugin_dir, 'hooks', 'format.py')
    if os.path.exists(script_path):
        subprocess.run(['python3', script_path])
```

## Tool-Specific Patterns

### Bash Command Processing
```python
command = data.get('tool_input', {}).get('command', '')

# Security check
if 'rm -rf /' in command.lower():
    sys.exit(2)

# Extract flags
args = command.split()
if '--force' in args:
    print("⚠️ Using --force flag", file=sys.stderr)
```

### File Operations
```python
file_path = data.get('tool_input', {}).get('file_path', '')

# Check file type
if file_path.endswith('.py'):
    handle_python_file(file_path)
elif file_path.endswith('.js'):
    handle_javascript_file(file_path)
```

### Web Operations
```python
url = data.get('tool_input', {}).get('url', '')

# Validate URL
if not url.startswith('https://'):
    print("❌ Only HTTPS URLs allowed", file=sys.stderr)
    sys.exit(2)
```

### Notebook Operations (NotebookEdit)
```python
notebook_path = data.get('tool_input', {}).get('notebook_path', '')
cell_type = data.get('tool_input', {}).get('cell_type', 'code')

# Validate notebook
if not notebook_path.endswith('.ipynb'):
    print("❌ Only Jupyter notebooks supported", file=sys.stderr)
    sys.exit(2)

# React to cell type
if cell_type == 'code':
    print("📓 Code cell edit detected", file=sys.stderr)
elif cell_type == 'markdown':
    print("📝 Markdown cell edit detected", file=sys.stderr)
```

### Web Search Operations
```python
query = data.get('tool_input', {}).get('query', '')

# Log searches for analytics
with open('~/.claude/searches.log', 'a') as f:
    f.write(f"{datetime.now().isoformat()} - {query}\n")
```

### Todo List Operations (TodoWrite)
```python
todos = data.get('tool_input', {}).get('todos', [])

# Audit changes
for todo in todos:
    status = todo.get('status')
    content = todo.get('content')
    print(f"📌 Todo status change: {content} -> {status}", file=sys.stderr)
```

### Skill Invocation Operations
```python
skill_name = data.get('tool_input', {}).get('skill', '')

# Control skill usage
if skill_name == 'dangerous-skill':
    print("⚠️ Dangerous skill requested - requires approval", file=sys.stderr)
    # Potentially block with exit 2
```

## MCP Tool Integration

### Naming Patterns for MCP Tools

MCP (Model Context Protocol) tools follow a specific naming convention. Matchers can target them with regex patterns:

**Standard Pattern:**
```
mcp__[source]__[tool_name]
```

**Examples:**
```
mcp__context7__resolve-library-id
mcp__brave-search__brave_web_search
mcp__brave-search__brave_local_search
```

### Matcher Configuration for MCP Tools

**Match All MCP Tools:**
```json
{
  "matcher": "mcp__.*"
}
```

**Match Specific Source:**
```json
{
  "matcher": "mcp__brave-search__.*"
}
```

**Match Specific Tool:**
```json
{
  "matcher": "mcp__brave-search__brave_web_search"
}
```

### Hook Example: Audit MCP Tool Usage
```python
tool_name = data.get('tool_name', '')

if tool_name.startswith('mcp__'):
    source, tool = tool_name.replace('mcp__', '').split('__', 1)

    with open('~/.claude/mcp_audit.log', 'a') as f:
        f.write(f"{datetime.now()} - {source}: {tool}\n")
```

### Hook Example: Rate Limit MCP Calls
```python
tool_name = data.get('tool_name', '')

if tool_name.startswith('mcp__brave-search__'):
    # Check call frequency
    cache_file = '/tmp/mcp_search_calls'

    if os.path.exists(cache_file):
        last_call = os.path.getmtime(cache_file)
        if time.time() - last_call < 2:  # Minimum 2 seconds between searches
            print("⚠️ Rate limit: Wait before next search", file=sys.stderr)
            sys.exit(2)

    # Update last call time
    open(cache_file, 'w').close()
```

## Advanced Tool Matchers

### Comprehensive Tool Reference

The following tools are available for matching in hooks:

| Tool | PreToolUse | PostToolUse | Matcher Example |
|------|-----------|-----------|-----------------|
| Bash | ✓ | ✓ | `Bash` |
| Read | ✓ | ✓ | `Read` |
| Write | ✓ | ✓ | `Write` |
| Edit | ✓ | ✓ | `Edit` |
| Glob | ✓ | ✓ | `Glob` |
| Grep | ✓ | ✓ | `Grep` |
| WebFetch | ✓ | ✓ | `WebFetch` |
| WebSearch | ✓ | ✓ | `WebSearch` |
| NotebookEdit | ✓ | ✓ | `NotebookEdit` |
| TodoWrite | ✓ | ✓ | `TodoWrite` |
| Skill | ✓ | ✓ | `Skill` |
| SlashCommand | ✓ | ✓ | `SlashCommand` |
| MCP Tools | ✓ | ✓ | `mcp__[source]__[tool]` |

### Regex Pattern Examples

**Match All File Operations:**
```json
{
  "matcher": "(Read|Write|Edit|Glob)"
}
```

**Match All Search Operations:**
```json
{
  "matcher": "(Grep|WebSearch|WebFetch)"
}
```

**Match All Interactive Operations:**
```json
{
  "matcher": "(Skill|SlashCommand|TodoWrite)"
}
```

**Match File Edits Only:**
```json
{
  "matcher": "Edit|NotebookEdit"
}
```

This reference provides comprehensive documentation for creating Claude Code hooks with all the necessary patterns, configurations, and best practices.