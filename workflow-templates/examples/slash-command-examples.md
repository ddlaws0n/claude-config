# Slash Command Examples

Examples of well-structured slash commands for reference.

## Example 1: Simple Review Command

**File**: `.claude/commands/review.md`

```markdown
---
description: Review this code for potential improvements
---

Review this code for:
- Security vulnerabilities
- Performance issues
- Code style violations
- Potential bugs
- Best practices adherence

Provide specific examples and actionable recommendations.
```

**Usage**: `/review`

## Example 2: Git Commit Command

**File**: `.claude/commands/commit.md`

```markdown
---
allowed-tools: Bash(git:*)
description: Create a git commit with message
---

## Context

- Current status: !`git status`
- Staged changes: !`git diff --staged`
- Recent commits: !`git log --oneline -5`

## Your task

Create a git commit following conventional commits format:
- Use present tense
- Start with type (feat/fix/docs/refactor/test/chore)
- Include scope if relevant
- Brief first line (<50 chars)
- Detailed explanation in body

Generate the commit message and execute: `git commit -m "message"`
```

**Usage**: `/commit`

## Example 3: PR Review Command with Arguments

**File**: `.claude/commands/review-pr.md`

```markdown
---
argument-hint: [pr-number] [priority]
description: Review pull request with priority level
allowed-tools: Bash(gh:*)
---

## Context

PR details: !`gh pr view $1`
PR diff: !`gh pr diff $1`

## Your task

Review PR #$1 with $2 priority.

Focus areas based on priority:
- high: Security, breaking changes, architecture
- medium: Code quality, tests, documentation
- low: Style, minor improvements

Provide:
1. Overall assessment
2. Specific issues with line references
3. Suggestions for improvement
4. Approval recommendation (approve/request changes/comment)
```

**Usage**: `/review-pr 123 high`

## Example 4: Explain Command

**File**: `.claude/commands/explain.md`

```markdown
---
description: Explain code in simple terms
---

Explain this code in simple, non-technical language:

1. What does it do overall?
2. Break down each major section
3. Explain any complex logic
4. Describe inputs and outputs
5. Note any important edge cases

Use analogies and examples to make it clear to someone without programming experience.
```

**Usage**: `/explain`

## Example 5: Optimize Command

**File**: `.claude/commands/optimize.md`

```markdown
---
description: Analyze code for performance issues
allowed-tools: Read, Grep
---

Analyze this code for performance optimization opportunities:

## Check for:
- Inefficient algorithms (O(n²) that could be O(n))
- Unnecessary loops or iterations
- Redundant computations
- Memory leaks or excessive allocations
- Database query optimization
- Caching opportunities

## Provide:
1. Current issues with performance impact estimate
2. Specific optimization recommendations
3. Code examples showing improvements
4. Trade-offs to consider

Prioritize optimizations by impact.
```

**Usage**: `/optimize`

## Example 6: Test Command with Free Arguments

**File**: `.claude/commands/test.md`

```markdown
---
argument-hint: [test description or file]
allowed-tools: Bash(npm:*), Bash(pytest:*)
description: Run tests and analyze failures
---

## Test execution

Running tests for: $ARGUMENTS

!`npm test $ARGUMENTS 2>&1 || pytest $ARGUMENTS -v 2>&1`

## Your task

1. Analyze test results above
2. Identify failures and their causes
3. Suggest fixes for each failure
4. If all pass, provide coverage recommendations
```

**Usage**: `/test src/auth` or `/test "user authentication"`

## Key patterns to notice

1. **Simple prompts**: No arguments, just focused instructions
2. **Bash execution**: Use `!` prefix with allowed-tools
3. **Structured arguments**: `$1, $2` for distinct parameters
4. **Free-form arguments**: `$ARGUMENTS` for flexible input
5. **Clear descriptions**: Help users understand purpose
6. **Context gathering**: Execute commands to get current state
