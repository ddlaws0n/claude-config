# Output Styles Reference

## How Output Styles Work

Output styles directly modify Claude Code's system prompt. They completely replace the software engineering parts of the default system prompt (unless `keep-coding-instructions` is true). Use output styles for fundamental behavior changes affecting all conversations in the main thread.

## Frontmatter Fields

| Field | Required | Purpose |
|-------|----------|---------|
| `name` | No | Human-readable name (can include spaces, capitalization). Defaults to filename. |
| `description` | No | Brief description shown in UI (max 256 characters). Focus on outcomes, not implementation. |
| `keep-coding-instructions` | No | Whether to keep Claude Code's coding-related system prompt. Defaults to false. |

## Built-in Styles (Do Not Duplicate)

Claude Code has three built-in output styles that you should not recreate:

**Default**: Standard software engineering system prompt
**Explanatory**: Provides educational "Insights" while coding
**Learning**: Collaborative learn-by-doing with TODO(human) markers

You can create variations (e.g., "Advanced Teaching Mode") but not exact duplicates.

## Content Structure

Include these essential sections:

1. **Opening statement**: "You are an interactive CLI tool that helps users with..."
2. **Core capabilities reminder**: List key Claude Code capabilities that remain available
3. **Behavior modifications**: Specific instructions for different behavior
4. **Communication style**: How to interact with users
5. **Task approach**: How to approach different scenarios

Example template:
```markdown
---
name: Teaching Mode
description: Explains reasoning and implementation choices while coding
---

# Teaching Mode Instructions

You help users learn by explaining your reasoning as you code.

## Core Capabilities
You maintain all of Claude Code's core capabilities including running scripts, reading/writing files, and using all available tools.

## Teaching Approach
Before significant changes, share insights:

**💡 Insight: [Brief title]**
[Explanation of concept, pattern, or decision]

Focus on transferable knowledge and patterns.
```

## Best Practices

**Keep it focused**: Only include instructions that genuinely modify behavior. Don't repeat Claude's existing knowledge. Target under 300 lines.

**Maintain capabilities**: Don't remove core Claude Code capabilities unnecessarily. Modify HOW tasks are approached, not WHETHER they can be done.

**Clear behavior modifications**: Use concrete examples of desired behavior. Specify when to apply certain approaches. Define what to prioritize.

## When to Use Output Styles

Use when you want fundamental changes to how Claude behaves in all conversations: teaching modes, domain expert personas, communication style modifications, or adapting Claude for non-software-engineering tasks.

Do NOT use for one-off prompts (use slash commands), complex multi-file workflows (use skills), or task-specific tools with separate context (use subagents).

## Comparison to Related Features

**vs CLAUDE.md**: Output styles replace parts of system prompt; CLAUDE.md appends to it
**vs Subagents**: Output styles affect main conversation; subagents have separate context
**vs Slash Commands**: Output styles are "stored system prompts"; slash commands are "stored prompts"

## Common Patterns

**Teaching/Explanatory**: Add insights and explanations while maintaining efficiency

**Domain Expert**: Emphasize specific domain expertise, terminology, and workflows

**Communication Style**: Modify verbosity, tone, or formatting (minimal, detailed, formal)

**Workflow Style**: Follow specific methodologies (TDD, documentation-first, incremental refactoring)

## Validation Rules

- Filename should be kebab-case (style name converted: "Teaching Mode" → `teaching-mode.md`)
- Name is clear and doesn't conflict with built-in styles
- Description clearly explains behavior changes user will experience
- Instructions maintain core Claude Code capabilities
- File is in correct location (~/.claude/output-styles/ or .claude/output-styles/)

