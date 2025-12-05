---
description: Create new slash commands or review existing ones for best practices compliance
argument-hint: create [command-name] | review [command-path or pattern]
model: claude-sonnet-4-5-20250929
allowed-tools: Read, Write, Grep, Glob
---

Manage slash commands with best practices from the official documentation and recent audit findings.

## Operation Mode

Action: $1 (either "create" or "review")
Target: $2 (command name for creation, or file path/pattern for review)

## For CREATE Mode

When creating a new slash command, gather requirements interactively and generate a command file following these standards:

**Frontmatter Best Practices:**
- Use only documented fields: `description`, `argument-hint`, `model`, `allowed-tools`, `disable-model-invocation`
- Never use custom fields like `agent:`, `name:`, `parameters:`, or `examples:`
- Set `description` to a clear, concise summary (appears in `/help`)
- Use `argument-hint` to show expected arguments: `[required] [optional]`
- Specify `model` only for cost optimization (haiku for simple tasks, sonnet for complex reasoning)
- Add `allowed-tools` only if command uses `!` bash execution or needs tool restrictions
- Set `disable-model-invocation: true` for destructive operations (push, delete, deploy)

**Content Best Practices (from prompting docs):**
- Write in flowing prose using complete paragraphs and sentences
- Avoid numbered lists and bullet points unless presenting truly discrete items
- Use standard paragraph breaks for organization
- Reserve markdown for inline code, code blocks, and simple headings only
- Avoid excessive bold and italics
- Keep commands concise (aim for 10-20 lines of actual instruction)
- Be explicit with instructions rather than vague
- Add context to explain why behaviors are important

**Argument Handling:**
- Use `$ARGUMENTS` to capture all arguments as a single string
- Use `$1`, `$2`, `$3` for distinct positional parameters
- Prefer positional arguments when you have specific parameter roles
- Document argument usage clearly in the command body

**Bash Execution:**
- Use `!` prefix for bash commands: `!git status`
- Must include `allowed-tools: Bash(command:*)` in frontmatter
- Output is included in command context before execution

**Subagent Delegation:**
- If delegating to a subagent, state it clearly in the command body
- Don't add `allowed-tools` for the subagent's tools (subagent has its own permissions)
- Keep delegation commands simple since they just invoke the subagent

Ask clarifying questions about the command's purpose, expected arguments, whether it delegates to a subagent, whether it needs bash execution, and whether it should be prevented from autonomous invocation. Then generate the command file in the appropriate location (`.claude/commands/` for project, `~/.claude/commands/` for personal).

## For REVIEW Mode

When reviewing existing slash commands, analyze them against the standards above and provide:

**Audit Checklist:**
- Frontmatter validity (only documented fields, no custom fields)
- Argument handling (positional vs $ARGUMENTS, proper usage)
- Content style (flowing prose vs excessive lists/bullets)
- Length and verbosity (concise vs over-explained)
- Model specification (appropriate or unnecessary)
- Tool permissions (correct for bash execution, not redundant for subagents)
- Safety controls (disable-model-invocation for destructive ops)

**Review Process:**
Read the specified command file(s) using the target pattern. For each command, identify issues with specific line references, explain why each issue matters per the documentation, provide concrete fix recommendations with example code, and note what the command does well. Prioritize issues as critical (breaks functionality), high (violates best practices significantly), medium (style improvements), or low (minor optimizations).

If reviewing multiple commands, provide a summary table showing compliance across all commands and highlight patterns of issues.

## Reference Documentation

This command is informed by:
- `docs/slash-commands.md` - Official slash command documentation
- `docs/prompting-best-practices.md` - Claude 4.x prompting guidelines
- `docs/models.md` - Model selection guidance
- Recent audit findings from 2025-12-05 conversation

Apply these standards rigorously to ensure all slash commands are functional, maintainable, and follow Anthropic's documented best practices.

