---
name: research
description: Advanced coding research specialist that conducts comprehensive investigations on technical topics
parameters:
  - name: topic
    description: The research topic or question to investigate
    required: true
    type: string
  - name: output
    description: Custom output file path (optional, defaults to docs/RESEARCH-YYYYMMDD-HHMM.md)
    required: false
    type: string
    default: ""
examples:
  - /research "React state management patterns"
  - /research "Rust async best practices" --output "docs/rust-async-research.md"
  - /research "microservice architecture patterns in Go"
---

# Research Workflow

This command invokes the Advanced Coding Research Specialist to conduct comprehensive technical research on your specified topic.

## Research Process

The research workflow follows a phased approach:

1. **Data Gathering**: Uses web search tools and available MCP servers (ref, context7, perplexity)
2. **Local Context**: Analyzes relevant files in the current codebase
3. **Preliminary Review**: Presents initial findings for your approval
4. **Final Report**: Generates structured documentation

## Output Structure

Research findings are organized into four main sections:

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

## Usage

**Basic research:**
```
/research "your topic here"
```

**Custom output location:**
```
/research "your topic" --output "path/to/custom-file.md"
```

The research specialist will automatically:
- Detect research intent and extract the core topic
- Leverage multiple sources for comprehensive coverage
- Create timestamped research documents by default
- Present findings for your review before finalizing

## Auto-triggering

This research workflow is also available as a skill that automatically triggers when research-oriented language is detected, such as:
- "Research X patterns"
- "Investigate Y best practices"
- "Analyze Z architecture"
- "Explore W evolution"

## Output Locations

- **Default**: `docs/RESEARCH-YYYYMMDD-HHMM.md`
- **Custom**: Specified with `--output` parameter
- **Multiple sessions**: Automatically creates unique timestamped files

## Tool Integration

The research workflow leverages:
- **Web Search**: Current information from online sources
- **MCP Servers**: Enhanced research through ref, context7, and perplexity (when available)
- **Local Analysis**: Repository exploration for relevant context
- **Documentation**: Official docs, RFCs, and technical specifications

---

*Ready to conduct comprehensive technical research on your coding topics.*