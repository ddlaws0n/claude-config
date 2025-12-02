---
allowed-tools: Read, Bash(git:*), Bash(find:*), Bash(tree:*), Bash(head:*), Bash(ls:*)
description: Load essential context for new agent session with codebase analysis
argument-hint: [shallow|deep] [focus-area]
model: claude-haiku-4-5-20251001
---

# Prime

Bootstrap context for a new agent session by analysing the codebase structure, configuration, and recent activity.

## Parameters

- `$1` — Depth: `shallow` (default) or `deep` (includes git history analysis)
- `$2` — Focus area: optional directory or domain to prioritise (e.g., `src/api`, `tests`)

## Context

### Repository State
- Current branch: !`git branch --show-current 2>/dev/null || echo "not a git repo"`
- Uncommitted changes: !`git status --short 2>/dev/null`
- Recent commits: !`git log --oneline -5 2>/dev/null`

### Structure  
- Files tracked: !`git ls-files 2>/dev/null | head -80`
- Directory tree: !`tree -L 2 -I 'node_modules|.git|__pycache__|venv|dist|build|coverage|.next' 2>/dev/null || ls -la`

### Documentation
- Project README: @README.md
- Project memory: @CLAUDE.md
- Contributing guide: @CONTRIBUTING.md

### Configuration
- Available scripts/commands: !`head -50 package.json 2>/dev/null || head -50 pyproject.toml 2>/dev/null || head -30 Makefile 2>/dev/null || echo "No standard manifest found"`

## Instructions

1. Analyse the codebase structure and identify the tech stack
2. Read the README and any CLAUDE.md for project context
3. Note any uncommitted changes or recent development activity
4. If `$2` (focus area) is provided, examine that area in detail
5. If `$1` is `deep`, also analyse git blame on key files and review open TODOs

## Output

Provide a concise briefing covering:
- **Stack**: Languages, frameworks, key dependencies
- **Structure**: Main directories and their purposes  
- **State**: Current branch, pending changes, recent work
- **Entry points**: How to run, test, and build
- **Recommendations**: Suggested starting points based on context
