---
description: Conduct comprehensive technical research and create structured documentation
argument-hint: [topic] [output-path (optional)]
model: claude-haiku-4-5-20251001
allowed-tools: Read, Grep, Glob, Bash, WebFetch, WebSearch
---

# Technical Research Task

**Topic**: $1
**Output**: $2 (default: `docs/RESEARCH-YYYYMMDD-HHMM.md` with current timestamp)

## Research Process

1. **Gather information** from multiple sources:
   - Web search for current documentation and articles
   - MCP servers if available (context7, perplexity, ref)
   - Local codebase files for project context

2. **Present preliminary findings** for approval before final report

3. **Generate structured report** with these sections:
   - **A. Fundamentals & Concepts**: Core principles, architecture, terminology, historical context
   - **B. Implementation Patterns**: Common approaches, best practices, anti-patterns, performance
   - **C. Practical Examples**: Working code snippets, real-world use cases, integration, testing
   - **D. Version & Compatibility**: Version differences, breaking changes, deprecation notices

## Requirements

- Verify information across multiple sources
- Provide grounded, hallucination-free answers based on actual documentation
- Create timestamped files to maintain research history
- Include source attribution in the report
