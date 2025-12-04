# Coding Research Specialist

An advanced research workflow that conducts comprehensive technical investigations on coding topics, leveraging web search tools and MCP servers to deliver structured findings.

## Features

- **Multi-source Research**: Web search + MCP servers (ref, context7, perplexity)
- **Local Context**: Analyzes relevant codebase files when applicable
- **Phased Approach**: Initial research → Preliminary review → Final report
- **Structured Output**: Consistent markdown format with four main sections
- **Auto-triggering**: Automatically activates on research-oriented queries
- **Flexible Output**: Customizable file locations with timestamped defaults

## Installation

The skill is installed in `~/.claude/skills/coding-research-specialist/` and includes:

- `SKILL.md` - Main skill documentation
- `research_interface.py` - Entry point with intent detection
- `research_system.py` - Core research orchestration
- `config.json` - Skill configuration
- `README.md` - This documentation

## Usage

### Automatic Triggering

Simply ask research questions naturally:

```bash
# Examples that trigger the skill
"Research Rust async patterns and best practices"
"Investigate the evolution of state management in React"
"Analyze microservice architecture patterns for Node.js"
"Tell me about Go concurrency patterns"
"Explore GraphQL vs REST API design"
```

### Manual Invocation

Use the slash command for explicit control:

```bash
# Basic research
/research "React state management patterns"

# Custom output location
/research "Rust async best practices" --output "docs/rust-async-research.md"
```

## Output Structure

Research findings are delivered in a consistent four-section format:

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

## Output Locations

- **Default**: `docs/RESEARCH-YYYYMMDD-HHMM.md` (timestamped)
- **Custom**: Specify with `--output` parameter
- **Directory**: Automatically creates `docs/` directory if needed

## Research Process

1. **Intent Detection**: Automatically identifies research-oriented queries
2. **Topic Extraction**: Isolates the core research topic from natural language
3. **Multi-source Gathering**: Web search, MCP servers, and local file analysis
4. **Preliminary Review**: Presents initial findings for approval/redirect
5. **Final Documentation**: Generates comprehensive structured report

## Tool Integration

### Primary Tools
- **Web Search**: Current information from online sources
- **File System**: Local codebase analysis and documentation access

### Optional MCP Servers
- **ref**: Enhanced reference lookup
- **context7**: Contextual research capabilities
- **perplexity**: Advanced question answering

### Fallback Behavior
If MCP servers are unavailable, the workflow automatically falls back to web search tools to ensure research continuity.

## Configuration

The skill behavior can be modified through `config.json`:

- **Auto-triggering**: Keywords and confidence thresholds
- **Timeout Settings**: Phase-specific time limits
- **Output Formatting**: Default locations and structure
- **Tool Permissions**: Access control and scope limitations

## Examples

### Example Output Structure

```markdown
# Research Report: Rust Async Patterns

*Generated: 2025-12-04 14:30:00*

## Sources Consulted
- Web Search: Rust async patterns
- MCP Server (ref): ✅
- MCP Server (context7): ✅
- Local File: src/main.rs

## A. Fundamentals & Concepts
### Core Principles and Architecture
Rust's async system is built around the Future trait...

[Continue with structured sections...]
```

## Troubleshooting

### Skill Not Triggering
- Ensure research keywords are present in your query
- Check that the skill is properly installed in `~/.claude/skills/`
- Use the `/research` slash command for manual invocation

### Output File Issues
- Verify write permissions to the target directory
- Check that the `docs/` directory can be created
- Use absolute paths for custom output locations if needed

### MCP Server Errors
- MCP servers are optional - research continues with web search
- Check Claude Code MCP server configuration
- Server availability is logged in the research output

## Development

The skill is designed to be extensible:

- **Adding Sources**: Modify `research_system.py` to include new data sources
- **Custom Structure**: Update the markdown template in `generate_final_report()`
- **New Triggers**: Modify keyword lists in `config.json` and `research_interface.py`

## Contributing

To enhance the research specialist:

1. Fork the skill directory
2. Test changes with various research topics
3. Update documentation for new features
4. Ensure backward compatibility with existing output format

---

*This research specialist transforms technical questions into comprehensive, actionable documentation.*