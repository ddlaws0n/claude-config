# Slash Commands Reference

## Frontmatter Fields

| Field | Purpose | Default |
|-------|---------|---------|
| `allowed-tools` | Tools the command can use | Inherits from conversation |
| `argument-hint` | Expected arguments shown in autocomplete | None |
| `description` | Brief description of the command | First line of content |
| `model` | Model string (sonnet, opus, haiku, or full name) | Inherits from conversation |
| `disable-model-invocation` | Prevents SlashCommand tool from calling this | false |

## Argument Handling

**$ARGUMENTS** captures everything passed to the command as a single string. Use for commands that treat all input as one thing (commit messages, search queries).

**$1, $2, $3...** access specific arguments by position. Use for structured commands with distinct parameter roles (PR number, priority, assignee).

Example with positional arguments:
```markdown
---
argument-hint: [pr-number] [priority] [assignee]
description: Review pull request
---

Review PR #$1 with priority $2 and assign to $3. Focus on security, performance, and code style.
```

## Bash Command Execution

Execute commands before the prompt runs using `!` prefix. Output is included in context. Requires `allowed-tools` with specific Bash commands.

```markdown
---
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)
description: Create a git commit
---

Current status: !`git status`
Current diff: !`git diff HEAD`

Based on the above changes, create a single git commit.
```

## File References

Include file contents using `@` prefix:
```markdown
Review the implementation in @src/utils/helpers.js
Compare @src/old-version.js with @src/new-version.js
```

## Thinking Mode

Include extended thinking keywords to trigger deeper reasoning:
```markdown
Think carefully about the implications of this architectural decision...
```

## Best Practices

Write content in flowing prose paragraphs rather than numbered lists or bullet points. Keep commands focused on one task. Use `disable-model-invocation: true` for destructive operations requiring explicit user control. Provide clear `argument-hint` values that show expected input format.

## Common Patterns

**Context-gathering command**:
```markdown
---
description: Analyze test failures
allowed-tools: Bash(npm:*), Bash(pytest:*)
---

Test results: !`npm test 2>&1`

Analyze these test failures and suggest fixes.
```

**Simple prompt with no arguments**:
```markdown
---
description: Review code for potential improvements
---

Review this code for security vulnerabilities, performance issues, code style violations, and potential bugs.
```

**Structured arguments with defaults**:
```markdown
---
argument-hint: [file-path] [format]
description: Generate documentation
---

Generate documentation for $1 in $2 format. If no format specified, use markdown.
```

## Validation Rules

- Filename becomes command name (without .md extension)
- Filename should be kebab-case (lowercase with hyphens)
- `argument-hint` should match actual argument usage in content
- `allowed-tools` must include any tools used by bash commands
- Do not use invalid frontmatter fields (agent, parameters, examples are not supported)

