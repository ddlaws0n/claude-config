# Claude Code Configuration

A production-grade configuration for Claude Code with intelligent hook system, custom subagents, and workflow automation for code quality, development server management, and workspace tracking.

## Overview

This configuration provides automated code quality enforcement, development server management, and build tracking through Claude Code's hook system. All hooks are designed to be fail-safe, performant, and non-blocking for smooth development workflow.

## Hook System Architecture

### PostToolUse Hooks (Fast Feedback)
Run immediately after file edits/writes to provide quick feedback:

- **`code_quality.py`** - Format, lint, and test individual files
  - Python: ruff format/lint, pytest
  - TypeScript: biome format/lint, bun test
  - Bash: shellcheck
  - Markdown: prettier (with regex fallback)
  - **Performance**: Runs only on edited file, no project-wide checks
  - **Test targeting**: Only runs tests for the specific test file being edited

- **`post_tool_use_tracker.sh`** - Track edited files and discover build commands
  - Detects monorepo workspace structure
  - Logs affected repositories per session
  - Discovers build/typecheck commands for batch execution
  - Creates session-based cache in `.claude/tsc-cache/`

### PreToolUse Hooks (Prevention)
Run before tool execution to prevent issues:

- **`duplicate_process_blocker.py`** - Prevent duplicate dev servers
  - Uses PID-based atomic file locking
  - Automatically cleans stale locks (process no longer running)
  - Prevents multiple `npm run dev`, `bun dev`, etc. simultaneously
  - Configurable patterns and timeout via environment variables

### Stop Hooks (Comprehensive Checks)
Run when agent finishes to ensure code quality:

- **`code_quality_typecheck.py`** - Project-wide type checking
  - TypeScript: Runs `tsc --noEmit` on entire project
  - Python: Runs `mypy` on project
  - Only runs when agent completes work (not on every edit)
  - 5-minute timeout for large projects
  - Blocks agent from stopping if type errors found

### SessionStart Hooks (Cleanup)
Run once per session for initialization:

- **`duplicate_process_blocker.py --cleanup`** - Clean stale locks
  - Removes locks from crashed/terminated processes
  - Runs only once at session start (not on every command)
  - Prevents lock file accumulation in `/tmp`

## Hook Design Principles

### Performance Optimization
- **Fast feedback**: Format/lint run immediately on edits (< 1s typically)
- **Deferred comprehensive checks**: Typecheck only runs when agent finishes
- **Targeted execution**: Tests run only for specific edited files
- **Minimal I/O**: Lock cleanup runs once per session, not per command

### Fail-Safe Operation
- **Graceful degradation**: Missing tools are skipped with warnings
- **Non-blocking**: Tool failures provide feedback but don't crash hooks
- **Exit code 0 on errors**: Hooks fail open to prevent workflow disruption
- **Timeout protection**: All hooks have reasonable timeouts

### Security & Validation
- **Path traversal prevention**: All file paths validated
- **Bounded operations**: Cache directories validated before creation
- **Input sanitization**: JSON input validated before processing
- **Atomic operations**: File locking uses atomic operations

## Configuration

### Settings Location
`/Users/dlawson/.claude/settings.glm.json`

### Current Hook Configuration
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "/Users/dlawson/.claude/hooks/duplicate_process_blocker.py"
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
            "command": "/Users/dlawson/.claude/hooks/code_quality.py",
            "timeout": 120
          },
          {
            "type": "command",
            "command": "/Users/dlawson/.claude/hooks/post_tool_use_tracker.sh",
            "timeout": 30
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/Users/dlawson/.claude/hooks/code_quality_typecheck.py",
            "timeout": 300
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/Users/dlawson/.claude/hooks/duplicate_process_blocker.py --cleanup"
          }
        ]
      }
    ]
  }
}
```

### Environment Variables

#### Duplicate Process Blocker
- `CLAUDE_DEV_SERVER_BLOCKER_ENABLED` - Enable/disable blocker (default: true)
- `CLAUDE_DEV_SERVER_TIMEOUT` - Lock timeout in minutes (default: 5)
- `CLAUDE_DEV_SERVER_LOCK_DIR` - Lock directory (default: /tmp)
- `CLAUDE_DEV_SERVER_PATTERNS` - Additional patterns (colon-separated)

#### Common Variables
- `CLAUDE_PROJECT_DIR` - Project root (injected by Claude Code)
- `CLAUDE_ENV_FILE` - Environment persistence file (SessionStart only)
- `CLAUDE_CODE_REMOTE` - Remote execution indicator

## File Structure

```
~/.claude/
├── settings.glm.json           # Main configuration
├── CLAUDE.md                   # Memory file for Claude Code
├── README.md                   # This file
├── hooks/
│   ├── code_quality.py         # PostToolUse: format/lint/test
│   ├── code_quality_typecheck.py  # Stop: comprehensive typecheck
│   ├── duplicate_process_blocker.py  # PreToolUse: prevent duplicate servers
│   ├── post_tool_use_tracker.sh     # PostToolUse: track edits & builds
│   └── utils/
│       └── sound_mappings.json      # Audio feedback configuration
├── plugins/                    # Plugin system
├── todos/                      # Session history
└── plans/                      # Planning mode outputs
```

## Tool Requirements

### Python Hooks
All Python hooks use `uv run --script` with inline dependencies:
- Python 3.13+
- uv (for script execution)

### Code Quality Tools
**Python projects:**
- `ruff` - Format and lint
- `mypy` - Type checking
- `pytest` - Testing

**TypeScript/JavaScript projects:**
- `biome` - Format and lint
- `tsc` - Type checking (via bun)
- `bun` - Package manager and test runner

**Bash scripts:**
- `shellcheck` - Linting

**Markdown:**
- `prettier` - Formatting (optional, has regex fallback)

**Workspace tracking:**
- `jq` - JSON processing (required for post_tool_use_tracker.sh)

## Usage Examples

### Managing Duplicate Process Locks

**Check active locks:**
```bash
/Users/dlawson/.claude/hooks/duplicate_process_blocker.py --status
```

**Manual cleanup:**
```bash
/Users/dlawson/.claude/hooks/duplicate_process_blocker.py --cleanup
```

### Understanding Hook Execution

**Enable debug output:**
```bash
claude --debug
```

**View hook execution in real-time:**
Press `Ctrl+O` in Claude Code to toggle verbose mode and see hook output.

### Testing Hook Changes

After modifying hooks:
1. **Restart Claude Code** - Hook configuration is captured at session startup
2. Edit a file to trigger PostToolUse hooks
3. Let agent finish to trigger Stop hooks
4. Check `claude --debug` output for execution details

## Troubleshooting

### Hooks Not Running

**Check hook registration:**
```bash
/hooks
```
This Claude Code command shows all registered hooks.

**Validate configuration:**
Ensure settings.glm.json has valid JSON syntax:
```bash
cat ~/.claude/settings.glm.json | jq .
```

**Check permissions:**
```bash
ls -la ~/.claude/hooks/
# All .py and .sh files should be executable
chmod +x ~/.claude/hooks/*.py ~/.claude/hooks/*.sh
```

### Common Issues

**"Command not found" errors:**
- Install missing tools (ruff, biome, etc.)
- Hooks will skip missing tools gracefully

**Slow hook execution:**
- Check timeout settings in settings.glm.json
- Consider disabling project-wide typecheck for large projects
- Use `claude --debug` to see which hooks are slow

**Type checking fails:**
- Ensure tsconfig.json exists for TypeScript projects
- Check mypy configuration for Python projects
- Type errors will block the Stop hook (by design)

**Lock files accumulating:**
- SessionStart hook should clean these automatically
- Manual cleanup: `~/.claude/hooks/duplicate_process_blocker.py --cleanup`
- Check lock directory: `ls -la /tmp/claude-dev-server-*.lock`

### Hook Output

**Exit codes:**
- `0` - Success (stdout shown in verbose mode only)
- `2` - Blocking error (stderr fed back to Claude)
- Other - Non-blocking error (stderr shown in verbose mode)

**JSON output:**
Hooks can return structured JSON to stdout for advanced control. See hooks.md for details.

## Resources

For more information:
- **CLAUDE.md** - Detailed project memory and architecture decisions
- **AGENTS.md** - Registry of custom subagents and workflows
- **hooks.md** - Complete hook reference documentation
- **commands/*** - Available slash commands
- **agents/*** - Custom subagent definitions
- **skills/*** - Complex multi-file capabilities

## Recent Changes (2025-12-01)

### Critical Fixes
- ✅ Fixed filename mismatch in settings (post_tool_tracker.sh → post_tool_use_tracker.sh)
- ✅ Converted tilde paths to absolute paths for reliability
- ✅ Fixed error handling in code_quality.py to prevent tracebacks

### Performance Improvements
- ✅ Separated typecheck to Stop hook (was running on every edit)
- ✅ Moved lock cleanup to SessionStart (was running on every Bash command)
- ✅ Test execution targets specific files only

### Code Quality
- ✅ Removed hardcoded error ignores
- ✅ Added consistent emoji logging across all hooks
- ✅ Improved documentation and inline comments

## Development Guidelines

### Adding New Language Support

1. **Update COMMANDS dict** in `code_quality.py`:
```python
"rust": {
    "format": ["cargo", "fmt"],
    "lint": ["cargo", "clippy"],
    "test": ["cargo", "test"],
}
```

2. **Add handler function**:
```python
def handle_rust(path: Path, rel_path: str, project_dir: str, errors: list[str]):
    # Format
    run_step("fmt", COMMANDS["rust"]["format"] + [rel_path], project_dir)
    # Lint
    success, out, is_real = run_step(
        "lint", COMMANDS["rust"]["lint"] + [rel_path], project_dir
    )
    if not success and is_real:
        errors.append(out)
```

3. **Add file extension mapping** in main():
```python
elif suffix == ".rs":
    handle_rust(full_path, rel_path, project_dir, errors)
```

### Hook Best Practices

- **Always use absolute paths** in settings.glm.json
- **Set appropriate timeouts** (PostToolUse: 30-120s, Stop: 300s)
- **Fail open** - Exit 0 on unexpected errors to avoid blocking
- **Log to stderr** for debugging (`claude --debug`)
- **Use emoji indicators** for consistency (⚠️, ❌, ✅, 🔍)
- **Validate inputs** before processing
- **Handle missing tools gracefully**

### Testing Hooks Locally

**Simulate PostToolUse event:**
```bash
echo '{
  "hook_event_name": "PostToolUse",
  "tool_name": "Write",
  "tool_input": {"file_path": "/path/to/test.py"},
  "tool_response": {"success": true},
  "cwd": "/path/to/project",
  "session_id": "test"
}' | CLAUDE_PROJECT_DIR=/path/to/project /Users/dlawson/.claude/hooks/code_quality.py
```

**Simulate Stop event:**
```bash
echo '{
  "hook_event_name": "Stop",
  "stop_hook_active": false,
  "cwd": "/path/to/project",
  "session_id": "test"
}' | CLAUDE_PROJECT_DIR=/path/to/project /Users/dlawson/.claude/hooks/code_quality_typecheck.py
```

## Resources

- **Official Documentation**: [hooks.md](hooks.md) - Complete Claude Code hooks reference
- **Hook Examples**: See individual hook files for inline documentation
- **Claude Code Settings**: [JSON Schema](https://json.schemastore.org/claude-code-settings.json)

## License

Private configuration repository for personal use.
