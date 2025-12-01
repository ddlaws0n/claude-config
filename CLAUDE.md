# CLAUDE Configuration Repository

**Memory file for Claude Code (claude.ai/code) when working in this configuration directory.**

## Overview

This is the personal Claude Code configuration directory (`~/.claude`) that manages settings, plugins, hooks, and session data. This file serves as persistent memory to maintain context across different Claude Code sessions and provide consistent assistance.

## Repository Purpose

- **Configuration Management**: Central location for Claude Code settings and preferences
- **Plugin Ecosystem**: Marketplace and custom plugin management
- **Automation**: Production-grade hook system for code quality, dev server management, and workspace tracking
- **Session Persistence**: Todo history and session data storage
- **Quality Enforcement**: Automated formatting, linting, and type checking across multiple languages

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
├── README.md                  # Hook system documentation
├── AGENTS.md                  # Custom subagent registry
├── hooks/                     # Custom automation scripts
│   ├── code_quality.py        # PostToolUse: fast format/lint/test
│   ├── code_quality_typecheck.py  # Stop: comprehensive typecheck
│   ├── duplicate_process_blocker.py  # PreToolUse: prevent duplicate servers
│   ├── post_tool_use_tracker.sh    # PostToolUse: track edits & builds
│   └── utils/
│       └── sound_mappings.json     # Audio feedback configuration
├── agents/                    # Custom subagent definitions
├── commands/                  # Slash command definitions
├── skills/                    # Agent skills
├── docs/                      # Comprehensive guides and references
├── plugins/                   # Plugin management
│   ├── known_marketplaces.json
│   └── installed_plugins.json
├── todos/                     # Session history
├── plans/                     # Planning mode outputs
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

The hook system is organized by execution timing for optimal performance:

**PostToolUse Hooks** (Fast Feedback on Every Edit):
- `code_quality.py` - Format, lint, and test individual files
  - Python: ruff format/lint, pytest (file-specific)
  - TypeScript: biome format/lint, bun test (file-specific)
  - Bash: shellcheck
  - Markdown: prettier with regex fallback
  - **Performance**: Runs only on edited file (~1s typical)

- `post_tool_use_tracker.sh` - Track workspace changes
  - Detects monorepo structure (packages/, apps/, etc.)
  - Logs affected repositories per session
  - Discovers build/typecheck commands for later batch execution
  - Creates session cache in `.claude/tsc-cache/`

**PreToolUse Hooks** (Prevention Before Execution):
- `duplicate_process_blocker.py` - Prevent duplicate dev servers
  - PID-based atomic file locking in `/tmp`
  - Prevents multiple `npm run dev`, `bun dev`, etc.
  - Auto-cleans stale locks (dead processes)
  - Configurable via environment variables

**Stop Hooks** (Comprehensive Checks When Agent Finishes):
- `code_quality_typecheck.py` - Project-wide type checking
  - TypeScript: `tsc --noEmit` on entire project
  - Python: `mypy` on project
  - 5-minute timeout for large projects
  - **Performance**: Only runs when agent completes work, not on every edit
  - Blocks agent from stopping if type errors found

**SessionStart Hooks** (One-Time Initialization):
- `duplicate_process_blocker.py --cleanup` - Clean stale locks
  - Removes orphaned lock files from crashed processes
  - Runs once per session instead of on every command
  - Prevents lock file accumulation

**Hook Design Principles**:
- **Fail-Safe**: Missing tools are skipped gracefully, unexpected errors exit 0
- **Performance**: Fast operations on edits, slow operations deferred to Stop hook
- **Targeted**: Tests run only for specific edited files, not entire suite
- **Secure**: Path traversal prevention, input validation, atomic operations
- **Observable**: Consistent emoji logging (⚠️, ❌, ✅, 🔍) for easy debugging

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

## Recent Improvements (2025-12-01)

### Critical Fixes Applied
1. **Filename Mismatch**: Fixed `post_tool_tracker.sh` → `post_tool_use_tracker.sh` in settings
2. **Path Resolution**: Converted tilde paths (`~/`) to absolute paths for reliability
3. **Error Handling**: Fixed incomplete error handling in code_quality.py that caused Python tracebacks

### Performance Optimizations Applied
1. **Typecheck Separation**: Moved from PostToolUse to Stop hook
   - **Before**: TypeScript tsc ran on every file edit (10-60s delay)
   - **After**: Fast format/lint on edits, comprehensive typecheck when agent finishes

2. **Lock Cleanup**: Moved from every Bash command to SessionStart
   - **Before**: Directory scan on every command (unnecessary I/O)
   - **After**: One-time cleanup at session start

3. **Test Targeting**: Already optimized (confirmed)
   - Tests run only for specific edited files
   - No full suite execution on file edits

### Code Quality Improvements
- Removed hardcoded error ignores (was masking tool failures)
- Added consistent emoji logging across all hooks
- Improved inline documentation and comments

## Common Issues & Solutions

### Hook-Related Issues

**Hooks Not Executing:**
- Run `/hooks` in Claude Code to verify registration
- Check `ls -la ~/.claude/hooks/` for execute permissions
- Validate JSON syntax: `cat ~/.claude/settings.glm.json | jq .`
- **Important**: Restart Claude Code after hook changes (config captured at startup)

**Slow Hook Performance:**
- PostToolUse hooks taking > 2s: Check which tool is slow with `claude --debug`
- TypeScript projects: Ensure Stop hook is running typecheck, not PostToolUse
- Large test suites: Verify tests run only for edited file, not entire suite
- Use `Ctrl+O` in Claude Code to see hook execution times

**Type Checking Failures:**
- TypeScript: Ensure `tsconfig.json` exists in project root
- Python: Check mypy configuration in `pyproject.toml`
- Type errors will block Stop hook (this is by design for code quality)
- Override: Manually stop Claude if needed, fix types later

**Lock Files Accumulating:**
- Should be cleaned automatically by SessionStart hook
- Manual cleanup: `/Users/dlawson/.claude/hooks/duplicate_process_blocker.py --cleanup`
- Check locks: `ls -la /tmp/claude-dev-server-*.lock`
- Stale locks indicate crashed dev servers

**"Command not found" Errors:**
- Install missing tools: `uv`, `ruff`, `mypy`, `biome`, `bun`, `shellcheck`, `jq`
- Hooks are designed to skip gracefully, but will log warnings
- Check hook output with `claude --debug` for specifics

### Plugin-Related Issues

**Plugins Not Loading:**
- Check `installed_plugins.json` and marketplace connectivity
- Verify plugin paths and Git commit SHAs
- Run `/plugins` to see loaded plugins

### Configuration Issues

**Settings Changes Not Applied:**
- **Hook changes require Claude Code restart** (config snapshot at startup)
- Validate JSON syntax and schema compliance
- Check for external modifications warning in Claude Code
- Review changes via `/hooks` menu before applying

## Important Patterns & Best Practices

### Hook Development
When modifying or creating hooks for this system:

1. **Path Handling**:
   - Always use absolute paths in `settings.glm.json` (never `~/`)
   - Use `$CLAUDE_PROJECT_DIR` for project-relative paths in scripts
   - Validate paths to prevent traversal attacks

2. **Error Handling**:
   - Exit 0 on unexpected errors (fail open)
   - Exit 2 to block with stderr feedback to Claude
   - Skip missing tools gracefully with warnings
   - Return structured JSON for advanced control

3. **Performance**:
   - PostToolUse: Fast operations only (< 2s typical)
   - Stop: Comprehensive checks (can be slower)
   - SessionStart: One-time initialization
   - Avoid expensive operations on every command

4. **Logging**:
   - Use stderr for debug output (`claude --debug`)
   - Consistent emoji indicators: ⚠️ (warning), ❌ (error), ✅ (success), 🔍 (info)
   - Include context in messages (file paths, tool names)

5. **Testing**:
   - Test hooks manually with JSON input before deployment
   - Verify hooks don't block workflow unexpectedly
   - Check execution time with `claude --debug`
   - Restart Claude Code after changes

### Configuration Management

**Settings File Precedence**:
1. Enterprise managed policy settings (highest)
2. `~/.claude/settings.json` (user settings)
3. `.claude/settings.json` (project settings)
4. `.claude/settings.local.json` (local, not committed)

**Hook Configuration Lifecycle**:
1. Settings read at Claude Code startup
2. Hook snapshot captured for session
3. External changes trigger warning
4. Changes reviewed via `/hooks` menu
5. Restart required for changes to take effect

**Important**: Never modify settings while Claude Code is running without restart

### Tool Requirements

**Required for all hooks**:
- Python 3.13+ with `uv` (script execution)
- `jq` (JSON processing in bash hooks)

**Language-specific tools** (gracefully skipped if missing):
- Python: `ruff`, `mypy`, `pytest`
- TypeScript: `biome`, `bun`, `tsc`
- Bash: `shellcheck`
- Markdown: `prettier` (has regex fallback)

## Security Considerations

- **API Tokens**: Store sensitive tokens in environment, not configuration files
- **Hook Permissions**: Limit hook file system access to necessary directories
- **Plugin Sources**: Only install plugins from trusted marketplaces
- **Configuration Exposure**: Avoid committing sensitive configuration to version control
- **Hook Execution**: All hooks run with user's permissions - review before enabling
- **Path Validation**: All file paths validated for traversal attacks
- **Atomic Operations**: File locking uses atomic operations to prevent race conditions
