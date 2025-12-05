---
name: hook-creation
description: Create and manage Claude Code hooks with templates for code quality, security, development workflow, monitoring, and notifications. Use when you need to create custom hooks, set up automation workflows, or enhance Claude Code's behavior with custom automation.
---

# Hook Creation and Management

Comprehensive templates and examples for creating Claude Code hooks across all major use cases.

## Quick start

1. **Create a basic PostToolUse hook** (runs after file edits):
```bash
# Create a hook to format Python files after editing
mkdir -p .claude/hooks
cat > .claude/hooks/python-formatter.sh << 'EOF'
#!/bin/bash
# Read JSON input from stdin
input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

# Only process Python files
if [[ "$file_path" == *.py ]]; then
    # Format with black (if available)
    if command -v black &> /dev/null; then
        black "$file_path"
        echo "✅ Formatted Python file: $file_path" >&2
    fi
fi

exit 0
EOF

chmod +x .claude/hooks/python-formatter.sh
```

2. **Add the hook to settings**:
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/python-formatter.sh"
          }
        ]
      }
    ]
  }
}
```

3. **Test the hook** by editing a Python file.

## Hook Event Types and Use Cases

### PreToolUse Hooks
- **Purpose**: Run before tool execution, can block or modify tool calls
- **Common uses**: Security checks, input validation, permission management

### PostToolUse Hooks
- **Purpose**: Run after successful tool execution
- **Common uses**: Code formatting, file processing, notifications

### Stop/SubagentStop Hooks
- **Purpose**: Run when Claude or subagent finishes
- **Common uses**: Quality checks, cleanup, validation

### SessionStart/SessionEnd Hooks
- **Purpose**: Run at session start or end
- **Common uses**: Environment setup, cleanup, logging

### Notification Hooks
- **Purpose**: Handle Claude Code notifications
- **Common uses**: Custom alerts, desktop notifications

## Hook Templates

### Code Quality & Testing Templates

See [templates/code-quality.md](templates/code-quality.md) for:
- Language-specific formatters
- Linters and static analysis
- Test runners
- Security scanners

### Security & Safety Templates

See [templates/security.md](templates/security.md) for:
- File protection rules
- Secret detection
- Access control
- Audit logging

### Development Workflow Templates

See [templates/development.md](templates/development.md) for:
- Pre-commit checks
- Build automation
- Dependency management
- Development server management

### Monitoring & Notification Templates

See [templates/monitoring.md](templates/monitoring.md) for:
- Desktop notifications
- Slack/Discord alerts
- Logging and metrics
- Progress tracking

### Advanced Integration Templates

See the following templates for sophisticated use cases:
- [templates/prompt-based-hooks.md](templates/prompt-based-hooks.md) - LLM-powered decision making
- [templates/environment-setup.md](templates/environment-setup.md) - Dynamic environment configuration
- [templates/context-injection.md](templates/context-injection.md) - Smart context amplification
- [templates/workflow-automation.md](templates/workflow-automation.md) - End-to-end automation
- [templates/intelligence-amplifiers.md](templates/intelligence-amplifiers.md) - AI enhancement patterns
- [templates/advanced-tools.md](templates/advanced-tools.md) - Complex tool integration

### MCP & External Integration

See [examples/mcp-integration.md](examples/mcp-integration.md) for:
- MCP tool pattern matching
- External service integration
- Plugin hook coordination

## Working Examples

### Example 1: Python Project Hook Setup
```bash
# Quick setup for Python projects
cp templates/python-project.json .claude/hooks-config.json
```

See [examples/python-project.md](examples/python-project.md) for complete setup.

### Example 2: TypeScript/Node.js Hook Setup
```bash
# Quick setup for TypeScript projects
cp templates/typescript-project.json .claude/hooks-config.json
```

See [examples/typescript-project.md](examples/typescript-project.md) for complete setup.

### Example 3: Multi-language Project
See [examples/multi-language.md](examples/multi-language.md) for handling projects with multiple languages.

## Script Library

The `scripts/` directory contains reusable hook components:

- [scripts/validators.py](scripts/validators.py) - Common validation functions
- [scripts/formatters.py](scripts/formatters.py) - Language formatters
- [scripts/notifiers.py](scripts/notifiers.py) - Notification helpers
- [scripts/utils.py](scripts/utils.py) - General utilities

## Creative Use Cases

### Prompt-Based Hooks for Intelligent Decisions

Use LLM-powered hooks to make sophisticated decisions about code changes, design patterns, and workflow execution:

```json
{
  "type": "prompt",
  "prompt": "Should this database migration proceed? Analyze the schema changes and consider rollback safety: $ARGUMENTS",
  "timeout": 30
}
```

See [templates/prompt-based-hooks.md](templates/prompt-based-hooks.md) for complete patterns.

### Context Injection for Making Claude Smarter

Automatically inject relevant context into Claude's understanding based on the current task:

- Detect project type and inject framework-specific guidelines
- Include recent error patterns to guide better solutions
- Inject team coding standards and conventions
- Provide codebase architecture context

See [templates/context-injection.md](templates/context-injection.md) for implementation.

### Session Analytics and Insights

Track, analyze, and report on development patterns:

- Session duration and productivity metrics
- Hook execution frequency and performance
- File change patterns and hotspots
- Tool usage statistics

See [templates/monitoring.md](templates/monitoring.md) for tracking patterns.

### Workflow Automation Beyond Code Quality

Orchestrate complex multi-step workflows:

- Automated code review and approval flows
- Deployment pipelines with approval gates
- Documentation generation and updates
- Cross-project synchronization

See [templates/workflow-automation.md](templates/workflow-automation.md) for examples.

### Intelligence Amplifiers

Enhance Claude's capabilities using hooks as intelligence multipliers:

- Real-time static analysis and design checks
- Automatic architecture decision validation
- Pattern-based suggestion injection
- Performance and security guardrails

See [templates/intelligence-amplifiers.md](templates/intelligence-amplifiers.md) for patterns.

## Best Practices

### Security
- Always validate and sanitize inputs
- Use absolute paths in scripts
- Avoid executing user-provided code directly

### Performance
- Keep PostToolUse hooks fast (under 2 seconds)
- Move expensive operations to Stop hooks
- Use proper tool matching to avoid unnecessary executions

### Reliability
- Make scripts fail gracefully with exit code 0 for non-critical errors
- Use exit code 2 to block tool execution
- Log errors to stderr for debugging

### Debugging
- Use `claude --debug` to see hook execution details
- Test hooks manually with JSON input
- Check permissions with `ls -la .claude/hooks/`

## Configuration Management

### Settings Locations
- User: `~/.claude/settings.json`
- Project: `.claude/settings.json`
- Local: `.claude/settings.local.json` (not committed)

### Hook Priority
1. Enterprise managed policy (highest)
2. User settings
3. Project settings
4. Local settings (lowest)

### Testing Hooks
```bash
# Test hook with sample input
echo '{"tool_name": "Write", "tool_input": {"file_path": "test.py"}}' | \
  .claude/hooks/python-formatter.sh
```

## Advanced Features

### JSON Output Control
Hooks can return structured JSON for advanced control:
```python
output = {
    "continue": True,  # Allow Claude to continue
    "systemMessage": "Warning message",
    "suppressOutput": True
}
print(json.dumps(output))
```

### PreToolUse Decision Control
```python
# Allow/deny tool execution
output = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",  # or "deny" or "ask"
        "permissionDecisionReason": "Reason for decision",
        "updatedInput": {"modified": "parameter"}
    }
}
```

### Prompt-Based Hooks
For complex decisions requiring LLM evaluation:
```json
{
  "type": "prompt",
  "prompt": "Evaluate if this operation should proceed: $ARGUMENTS",
  "timeout": 30
}
```

## Reference Materials

- [REFERENCE.md](REFERENCE.md) - Complete API reference
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions
- [CHEAT_SHEET.md](CHEAT_SHEET.md) - Quick reference

## Quick Reference

```bash
# Create new hook directory
mkdir -p .claude/hooks

# Make script executable
chmod +x .claude/hooks/script.py

# Add to settings (use /hooks command in Claude)
# Or edit .claude/settings.json

# Test with debug
claude --debug

# View current hooks
/hooks

# Remove problematic hook
# Edit settings.json and restart Claude
```

Remember: Settings changes require Claude Code restart to take effect.