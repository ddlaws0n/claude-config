# Subagents Reference

## Frontmatter Fields

| Field | Required | Purpose |
|-------|----------|---------|
| `name` | Yes | Unique identifier using lowercase letters and hyphens |
| `description` | Yes | Natural language description of purpose and when to invoke |
| `tools` | No | Comma-separated list of tools. If omitted, inherits all tools from main thread |
| `model` | No | Model to use: sonnet, opus, haiku, or inherit. Defaults to configured subagent model |
| `permissionMode` | No | Permission handling: default, acceptEdits, bypassPermissions, plan, ignore |
| `skills` | No | Comma-separated skill names to auto-load into subagent context |

## Tool Configuration

**Option 1: Omit tools field** - Subagent inherits all tools from main thread including MCP tools. Best for general-purpose subagents needing full capabilities.

**Option 2: Specify tools** - Restricts subagent to listed tools only. Good for focused or security-sensitive workflows.

Available tools: Read, Write, Edit, Grep, Glob, Bash, Task, WebFetch, WebSearch, AskUserQuestion, and MCP tools.

Example restricted access:
```yaml
tools: Read, Grep, Glob, Bash
```

## Model Selection

Choose based on task complexity:

**sonnet** (default): Balanced performance for most tasks
**opus**: Maximum reasoning for complex architecture decisions and deep analysis
**haiku**: Fast and economical for simple structured tasks
**inherit**: Match main conversation's model

## Proactive Invocation

To trigger automatic use, include phrases in the description like:
- "use PROACTIVELY"
- "MUST BE USED"
- "Use immediately after..."

Example: "Expert code review specialist. Proactively reviews code for quality, security, and maintainability. Use immediately after writing or modifying code."

## System Prompt Best Practices

The system prompt should define the subagent's role, provide specific instructions, include numbered workflows, add checklists for complex processes, specify constraints, and give examples of good vs bad approaches.

Structure your prompt:
```markdown
# Subagent Name

You are [role and expertise].

When invoked:
1. First action
2. Second action
3. Continue process

For each task:
- What to provide
- How to format
- What to avoid

Final guidance or constraints.
```

## Subagent Chaining

Subagents can use the Task tool to invoke other subagents. This enables orchestration patterns where a coordinator subagent delegates to specialized workers. However, keep chains shallow (2 levels maximum) to avoid context fragmentation.

## Common Patterns

**Read-only analyzer**: `tools: Read, Grep, Glob, Bash` - Analysis without modifications (code review, documentation analysis)

**Code modifier**: `tools: Read, Write, Edit, Grep, Glob, Bash` - Makes code changes (refactoring, bug fixing)

**Command runner**: `tools: Bash, Read` - Executes commands and interprets results (test runner, build system)

**Comprehensive assistant**: Omit tools field - General-purpose help with full tool access

## Using Skills in Subagents

The `skills` field auto-loads skills into the subagent's context:

```yaml
---
name: code-reviewer
description: Reviews code for quality and security
skills: workflow-creation, security-guidelines
---
```

Skills are loaded automatically when the subagent starts, providing additional context without cluttering the system prompt.

## Validation Rules

- Name uses lowercase letters and hyphens only
- Description explains what it does and when to use it
- Tools are appropriate for the task (or omitted for full access)
- Model choice matches task complexity
- System prompt is detailed and focused on one area of expertise
- File is in correct location (~/.claude/agents/ or .claude/agents/)

