---
name: workflow-creation
description: Creates Claude Code workflow components including slash commands, skills, subagents, and output styles. Provides best practices, validation rules, and examples for each workflow type. Use when generating, reviewing, or troubleshooting custom workflows.
---

# Workflow Creation Reference

This skill provides comprehensive guidance for creating Claude Code workflow components. Each component type serves a distinct purpose and follows specific patterns.

## Quick Reference

**Slash Commands** are user-invoked prompts stored as single markdown files. Use for quick, frequently-used prompts that fit in one file. Location: `~/.claude/commands/` (personal) or `.claude/commands/` (project).

**Skills** are model-invoked capabilities with progressive disclosure. Use for complex workflows requiring multiple files, scripts, or reference materials. Location: `~/.claude/skills/` (personal) or `.claude/skills/` (project).

**Subagents** are specialized AI assistants with separate context windows. Use for task-specific workflows benefiting from isolation (code review, debugging, analysis). Location: `~/.claude/agents/` (personal) or `.claude/agents/` (project).

**Output Styles** modify Claude Code's system prompt for persistent behavior changes. Use for system-wide behavior modifications affecting all interactions. Location: `~/.claude/output-styles/` (personal) or `.claude/output-styles/` (project).

## Choosing the Right Type

When the user wants automatic discovery based on context, use a Skill. When they want explicit invocation via `/command`, use a Slash Command. When they need specialized expertise with separate context, use a Subagent. When they want fundamental behavior changes affecting all conversations, use an Output Style.

Consider combinations when primary components need supporting tools, or when workflows have multiple phases requiring different behaviors.

## Detailed References

For comprehensive patterns, examples, and validation rules, see the specialized reference files:

- [Slash Commands Reference](slash-commands-reference.md) - Frontmatter fields, argument handling, bash execution, file references
- [Skills Reference](skills-reference.md) - Progressive disclosure, allowed-tools, multi-file structure, description requirements
- [Subagents Reference](subagents-reference.md) - Tool configuration, model selection, proactive invocation, system prompts
- [Output Styles Reference](output-styles-reference.md) - Behavior modifications, frontmatter, built-in styles to avoid

## Validation Checklist

Before finalizing any component, verify:

1. **Names** use lowercase letters, numbers, and hyphens only (max 64 characters for skills/subagents)
2. **Descriptions** clearly explain what it does AND when to use it
3. **File locations** match the intended scope (personal vs project)
4. **Frontmatter** uses only documented fields for the component type
5. **Content** follows prompting best practices (flowing prose, not excessive lists)

## Common Patterns

**Progressive Disclosure**: Keep main files concise, link to detailed references. Claude loads additional files only when needed.

**Argument Handling**: Use `$ARGUMENTS` for free-form input, `$1`, `$2`, `$3` for structured parameters with distinct roles.

**Tool Restrictions**: Use `allowed-tools` to limit capabilities for security-sensitive workflows or read-only operations.

**Proactive Invocation**: Include phrases like "use PROACTIVELY" or "MUST BE USED" in subagent descriptions for automatic triggering.

