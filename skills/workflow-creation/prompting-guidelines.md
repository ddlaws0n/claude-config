# Prompting Guidelines for Workflow Components

These guidelines apply to all workflow component content: slash commands, skill instructions, subagent system prompts, and output style instructions.

## Core Principles

**Write in flowing prose** rather than fragmenting information into isolated bullet points and numbered lists. Your goal is readable, flowing text that guides the reader naturally through ideas. Lists should be reserved for genuinely parallel items like configuration options or step sequences where order matters.

**Be concise**. Only add context Claude doesn't already have. Challenge every paragraph: "Does Claude really need this?" Assume Claude is smart and knows common concepts. A 50-line command can often be reduced to 10 lines without losing effectiveness.

**Front-load critical information**. Put the most important instructions early in the content. Claude's attention is strongest at the beginning.

**Use clear, direct language**. Avoid hedging words like "perhaps" or "might want to consider." State instructions definitively.

## Effective Patterns

**Conditional workflows** handle different scenarios clearly:
"If the request involves breaking changes, summarize impact and ask for confirmation before proceeding. For non-breaking changes, implement directly and explain what was done."

**Feedback loops** ensure quality:
"After making changes, run the test suite. If tests fail, analyze the failure, fix the issue, and re-run. Continue until all tests pass."

**Templates** provide structure when needed:
"Format commit messages as: type(scope): description. Types include feat, fix, docs, refactor, test."

## Anti-Patterns to Avoid

**Excessive structure**: Don't create elaborate hierarchies of numbered steps with sub-bullets when prose would be clearer.

**Redundant context**: Don't explain what git is or how markdown works. Claude knows these things.

**Vague instructions**: "Be helpful" or "Write good code" provide no actionable guidance.

**Over-constraining**: Unless the task is fragile, allow Claude flexibility to choose the best approach.

## Model-Specific Considerations

**Sonnet**: Best for most tasks. Balanced reasoning and efficiency. Good for orchestration and analysis.

**Haiku**: Use for simple, well-defined tasks. Fast and cost-effective. Avoid for complex reasoning or ambiguous requirements.

**Opus**: Reserve for deep analysis, complex architecture decisions, or tasks requiring maximum reasoning capability.

When writing for haiku, be more explicit and structured. When writing for sonnet or opus, you can rely more on Claude's judgment and use flowing prose.

## Extended Thinking

Include thinking trigger phrases for complex decisions:
- "Think carefully about..."
- "Analyze step by step..."
- "Consider the implications..."

These phrases activate extended thinking mode, useful for architectural decisions, security reviews, or complex debugging.

## Writing Component Descriptions

Descriptions are critical for discoverability (skills, subagents) and clarity (slash commands, output styles).

**Include what it does AND when to use it**:
"Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction."

**Write in third person for skills and subagents**:
Good: "Analyzes code for security vulnerabilities"
Bad: "I can help you find security issues"

**Be specific about triggers**:
Good: "Use when reviewing PRs, checking code quality, or preparing for code review"
Bad: "For code stuff"

