---
description: Conduct comprehensive technical research and create structured documentation
argument-hint: [topic] [output-path (optional)]
model: model: claude-haiku-4-5-20251001
---

Conduct comprehensive technical research on the specified topic: $1

Save the research report to: $2 (if not provided, use `docs/RESEARCH-YYYYMMDD-HHMM.md` with current timestamp)

Use web search tools and available MCP servers (ref, context7, perplexity) to gather data from multiple sources. Analyze relevant files in the current codebase for context. Present preliminary findings for approval before generating the final structured report.

Organize the research report into four sections: fundamentals and concepts (core principles, architecture, terminology, historical context), implementation patterns (common approaches, best practices, anti-patterns, performance considerations), practical examples (working code snippets, real-world use cases, integration patterns, testing approaches), and version compatibility (version-specific differences, breaking changes, deprecation notices, compatibility matrices).

Create timestamped files for multiple research sessions to maintain history. Verify information across multiple sources and provide grounded, hallucination-free answers based on actual documentation and code.
