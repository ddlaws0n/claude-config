# Advanced Coding Research Specialist

A comprehensive research workflow that leverages web search tools and MCP servers to conduct thorough investigations on coding topics, delivering structured findings in markdown format.

## Auto-triggering

This skill automatically triggers when research-oriented keywords are detected:
- "research", "investigate", "analyze", "explore"
- Technology pattern queries (e.g., "React patterns", "Go best practices")
- Deep-dive requests on technical topics

## How to Use

### Automatic Triggering
Simply ask a research question:
- "Research Rust async patterns and best practices"
- "Investigate the evolution of state management in React"
- "Analyze microservice architecture patterns for Node.js"

### Manual Invocation
Use the slash command: `/research [topic] --output [custom-file.md]`

## Output Format

Research findings are delivered in a structured markdown format with these sections:

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

- Default: `docs/RESEARCH-YYYYMMDD-HHMM.md` (e.g., `docs/RESEARCH-20250412-1430.md`)
- Custom: Specify with `--output` flag in slash command
- Multiple sessions: Creates timestamped files automatically

## Tool Integration

The workflow leverages:
- **Web Search**: Up-to-date information from the web
- **MCP Servers**: ref, context7, perplexity (when available)
- **Local Analysis**: Repository exploration and code examination
- **Documentation**: Official docs, RFCs, and specifications

## Phased Approach

1. **Initial Research**: Comprehensive data gathering from multiple sources
2. **Preliminary Findings**: Presents initial discoveries for review
3. **Direction Approval**: User can approve, redirect, or expand research scope
4. **Final Report**: Complete structured documentation

---

*This skill specializes in turning complex technical questions into actionable research documentation.*