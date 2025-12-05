---
name: coding-research-specialist
description: Conducts comprehensive technical research using web search and MCP servers. Use when research, investigation, deep analysis, or exploration is requested on coding topics, libraries, frameworks, or technical patterns.
---

# Advanced Coding Research Specialist

A comprehensive research workflow that leverages web search tools and MCP servers to conduct thorough investigations on coding topics, delivering structured findings in markdown format.

## When This Skill Applies

Activate this skill when the user:
- Requests research, investigation, analysis, or exploration of technical topics
- Asks about technology patterns (e.g., "React patterns", "Go best practices")
- Needs deep-dive documentation on libraries, frameworks, or architectures
- Wants comparison or evolution information on technologies

## Research Process

### Phase 1: Information Gathering
Use these tools to collect comprehensive data:
- **Web Search**: Current articles, blog posts, tutorials
- **MCP Servers** (if available): context7, perplexity, ref for library docs
- **Local Files**: Examine relevant project files for context

### Phase 2: Preliminary Findings
Present a summary of what was found before writing the final report:
- Number and types of sources consulted
- Key themes and patterns discovered
- Proposed report structure
- Ask user to approve, redirect, or expand scope

### Phase 3: Final Report Generation
Create the structured markdown report with verified information.

## Output Format

Organize all research reports with these four sections:

### A. Fundamentals & Concepts
- Core principles and architecture
- Key terminology and definitions
- Historical context and evolution
- Relationship to other technologies

### B. Implementation Patterns
- Common implementation approaches
- Best practices and conventions
- Anti-patterns to avoid
- Performance considerations

### C. Practical Examples
- Working code snippets with explanations
- Real-world use cases
- Integration patterns
- Testing approaches

### D. Version & Compatibility
- Version-specific differences
- Breaking changes and migrations
- Compatibility matrices
- Deprecation notices

## Output Location

- **Default**: `docs/RESEARCH-YYYYMMDD-HHMM.md` (timestamped)
- **Custom**: User can specify output path
- **Multiple sessions**: Create separate timestamped files

## Quality Standards

- Verify information across multiple sources
- Provide source attribution for key claims
- Avoid hallucination - only report what sources confirm
- Include code examples that are tested/verified where possible
- Note version-specific information clearly