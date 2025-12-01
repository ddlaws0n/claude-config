# CLAUDE Configuration Repository

**Memory file for Claude Code (claude.ai/code) when working in this configuration directory.**

## Overview

This is the personal Claude Code configuration directory (`~/.claude`) that manages settings, plugins, hooks, and session data. This file serves as persistent memory to maintain context across different Claude Code sessions and provide consistent assistance.

## Repository Purpose

- **Configuration Management**: Central location for Claude Code settings and preferences
- **Plugin Ecosystem**: Marketplace and custom plugin management
- **Automation**: Custom hooks and scripts for enhanced workflow
- **Session Persistence**: Todo history and session data storage

## Tech Stack & Dependencies

- **Configuration Format**: JSON for settings, Python for custom hooks
- **Plugin Sources**: GitHub-based marketplaces
- **Status Line**: Node.js/bun-based external command
- **Hook System**: Python scripts with JSON input/output
- **Package Managers**: npm/bun for external tools

## Architecture

### Directory Structure
```
~/.claude/
├── settings.glm.json           # Main configuration file
├── CLAUDE.md                  # This memory file
├── hooks/                     # Custom automation scripts
│   └── formatter              # Markdown formatting hook
├── plugins/                   # Plugin management
│   ├── known_marketplaces.json
│   └── installed_plugins.json
├── todos/                     # Session history
└── plugins/marketplaces/      # Installed plugin repositories
```

### Configuration System

#### Core Settings (`settings.glm.json`)
- **Model Configuration**: Uses "haiku" for faster response times
- **API Configuration**: Custom endpoint with extended timeout (3000s)
- **Permissions**: Bypass mode with WebFetch allowed, additional directory access
- **Hooks**: PostToolUse automation for markdown formatting
- **Status Line**: External `ccstatusline` command with custom padding
- **Telemetry**: Disabled for privacy

#### Plugin Architecture
The plugin system supports multiple marketplaces:

1. **claude-code-plugins** (Official)
   - Source: `anthropics/claude-code`
   - Contains: commit-commands, pr-review-toolkit, agent-sdk-dev, etc.

2. **anthropic-agent-skills** (Official)
   - Source: `anthropics/skills`
   - Contains: Official agent skills and capabilities

3. **superpowers-dev** (Third-party)
   - Source: `obra/superpowers`
   - Contains: Enhanced development capabilities

#### Custom Hooks System

**Markdown Formatter Hook** (`hooks/formatter`)
- **Trigger**: PostToolUse events for Edit/Write operations
- **Target**: Markdown files (`.md`, `.mdx`)
- **Functionality**:
  - Auto-detects programming languages in code blocks
  - Adds missing language tags to code fences
  - Fixes excessive blank lines in content
  - Preserves code content while improving formatting

**Language Detection Support**:
- JSON (structure validation)
- Python (function/class patterns)
- JavaScript (ES6+ syntax)
- Bash (shell script patterns)
- SQL (query patterns)
- Fallback to "text"

## Common Development Tasks

### Configuration Management
- **Reload Settings**: Restart Claude Code after modifying `settings.glm.json`
- **Plugin Updates**: Use Claude Code's built-in plugin management system
- **Hook Development**: Create scripts in `hooks/` that handle JSON stdin/stdout

### Plugin Operations
- **Install Plugins**: Through Claude Code's plugin marketplace interface
- **Update Plugins**: Automatic or manual updates via plugin system
- **Plugin Development**: Follow marketplace structure in `plugins/marketplaces/`

### Maintenance
- **Cleanup Session Data**: Periodically clean `todos/` directory
- **Hook Testing**: Test hooks with sample JSON input/output
- **Configuration Backup**: Backup `settings.glm.json` before major changes

## Development Standards

### Hook Development
- Scripts must be executable (`chmod +x`)
- Accept JSON input via stdin
- Handle errors gracefully with proper exit codes
- Provide informative output for debugging

### Configuration Best Practices
- Use absolute paths for external commands
- Set appropriate timeouts for API operations
- Configure permissions following principle of least privilege
- Test configuration changes in non-production environments

### File Organization
- Keep configuration files in JSON format with proper schema validation
- Maintain consistent naming conventions across plugins
- Document custom integrations and their purposes
- Version control important configuration files

## Environment Variables & External Dependencies

### Required for External Tools
- **Node.js/Bun**: For status line command (`ccstatusline`)
- **Python 3.13+**: For custom hook scripts
- **UV**: Python script runner (configured in hook shebang)

### API Configuration
- `ANTHROPIC_AUTH_TOKEN`: Authentication token
- `ANTHROPIC_BASE_URL`: Custom API endpoint
- `API_TIMEOUT_MS`: Request timeout configuration

## Common Issues & Solutions

### Hook Failures
- **Issue**: Hooks not executing after file operations
- **Solution**: Verify script permissions and JSON input handling
- **Debug**: Test hooks manually with sample JSON input

### Plugin Loading
- **Issue**: Plugins not appearing in commands
- **Solution**: Check `installed_plugins.json` and marketplace connectivity
- **Debug**: Verify plugin paths and Git commit SHAs

### Configuration Not Applied
- **Issue**: Settings changes not taking effect
- **Solution**: Restart Claude Code completely
- **Debug**: Validate JSON syntax and schema compliance

## Security Considerations

- **API Tokens**: Store sensitive tokens in environment, not configuration files
- **Hook Permissions**: Limit hook file system access to necessary directories
- **Plugin Sources**: Only install plugins from trusted marketplaces
- **Configuration Exposure**: Avoid committing sensitive configuration to version control
