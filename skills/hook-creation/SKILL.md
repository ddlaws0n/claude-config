---
name: hook-creation
description: Create and manage Claude Code hooks for event-driven automation. Use when you need custom hooks for code quality, security, workflow automation, or monitoring.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# Hook Creation and Management

Claude Code hooks are event-driven shell scripts that execute at lifecycle points like file edits, tool calls, and session events. Unlike slash commands, skills, and subagents which are prompt-based, hooks are executable automation that integrates with your development workflow.

## When to use hooks

Hooks are ideal for automation that should happen automatically without explicit invocation: formatting code after edits, validating before Claude stops, blocking dangerous commands, sending notifications, injecting context, or managing development servers. If the user describes something that runs "every time" or "before/after" an event, it's a hook.

## Hook event types

There are 10 hook events organized by when they execute. **PreToolUse** runs before tool execution and can block or modify tool calls. **PostToolUse** runs after successful tool execution for formatting, processing, or notifications. **Stop** and **SubagentStop** run when Claude or a subagent finishes, ideal for comprehensive quality checks. **SessionStart** and **SessionEnd** handle environment setup and cleanup. **Notification** handles custom alerts. **UserPromptSubmit** can inject context before Claude processes input. **PermissionRequest** can auto-approve trusted operations. **PreCompact** can preserve context during compaction.

## Quick reference

| Event | Runs When | Common Uses |
|-------|-----------|-------------|
| PreToolUse | Before tool execution | Security checks, input validation |
| PostToolUse | After tool success | Formatting, processing |
| Stop | Claude finishes work | Type checking, validation |
| SessionStart | Session begins | Environment setup |
| Notification | Alert triggered | Desktop/Slack notifications |
| UserPromptSubmit | User sends message | Context injection |

## Essential patterns

**Command hooks** execute shell scripts with JSON input via stdin. Exit code 0 continues normally, exit code 2 blocks execution with stderr feedback. Scripts should validate inputs, use absolute paths, and fail gracefully.

**Prompt-based hooks** use an LLM (Haiku) to make decisions, primarily for Stop/SubagentStop hooks where nuanced evaluation is needed. They return structured JSON responses with `decision` and `reason` fields.

**Configuration** goes in `settings.json` (user: `~/.claude/settings.json`, project: `.claude/settings.json`). Hooks require Claude Code restart to take effect.

## Templates and references

For implementation patterns, see:
- [REFERENCE.md](REFERENCE.md) - Complete API reference with all input/output schemas
- [CHEAT_SHEET.md](CHEAT_SHEET.md) - Quick reference and common patterns
- [templates/code-quality.md](templates/code-quality.md) - Formatters, linters, test runners
- [templates/security.md](templates/security.md) - File protection, secret detection
- [templates/prompt-based-hooks.md](templates/prompt-based-hooks.md) - LLM-powered decisions
- [templates/context-injection.md](templates/context-injection.md) - Smart context amplification

The `scripts/` directory contains reusable components for validators, formatters, and notifiers. The `examples/` directory has complete project setups for Python, TypeScript, and multi-language projects.

## Key best practices

Keep PostToolUse hooks fast (under 2 seconds) and move expensive operations like type checking to Stop hooks. Always validate and sanitize inputs from the JSON payload. Use `$CLAUDE_PROJECT_DIR` for project-relative paths. Test hooks manually with `echo '{"tool_name":"Write"}' | ./hook.sh` before adding to settings. Debug with `claude --debug` to see hook execution.

## Getting started

Create a hook script in `.claude/hooks/`, make it executable with `chmod +x`, add the hook configuration to `.claude/settings.json`, and restart Claude Code. Use the `/hooks` command to view registered hooks.