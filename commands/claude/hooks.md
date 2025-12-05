---
description: Create new hooks or review existing ones for best practices and security compliance
argument-hint: create [hook-name] | review [settings-file or hook-path]
model: claude-sonnet-4-5-20250929
---

Manage Claude Code hooks with comprehensive security, performance, and best practices guidance.

## Operation Mode

Action: $1 (either "create" or "review")
Target: $2 (hook identifier for creation, or settings file path for review)

## For CREATE Mode

When creating a new hook, delegate to the hook-development-expert agent for specialized guidance. This approach minimizes context loading while providing expert-level assistance.

**Delegation Instructions:**
I'll use the hook-development-expert agent to help you create a new hook. This specialized agent has deep knowledge of:
- Hook event types and their use cases (PreToolUse, PostToolUse, SessionStart, etc.)
- Security best practices and input validation
- Performance optimization strategies
- Error handling and exit code patterns
- Hook configuration in settings.json

The agent will guide you through:
1. **Hook Event Selection**: Choosing the right event based on your needs
2. **Matcher Configuration**: Setting up tool-specific or global hooks
3. **Script Development**: Writing secure, performant hook scripts
4. **Settings Integration**: Properly configuring hooks in settings.json
5. **Testing Strategy**: How to test hooks safely before deployment

**Key Considerations for Hook Development:**
- **Security**: Hooks execute with your user permissions - validate all inputs
- **Performance**: Fast operations in PostToolUse, heavy operations in Stop hooks
- **Error Handling**: Exit codes control whether actions are blocked
- **Atomic Operations**: Use proper file locking and cleanup
- **Path Safety**: Prevent directory traversal attacks
- **Tool Availability**: Handle missing tools gracefully

## For REVIEW Mode

When reviewing existing hooks, analyze them for security, performance, and compliance with best practices:

**Security Audit Checklist:**
- Input validation and sanitization (especially for file paths)
- Path traversal prevention (checking for `..` in paths)
- Command injection防护 (proper quoting of shell variables)
- File permissions and access controls
- Sensitive file handling (avoiding .env, .git/, keys)
- Atomic operations for file locking
- Cleanup of temporary files and locks

**Performance Review Checklist:**
- Appropriate hook event usage (fast vs slow operations)
- Timeout configurations for long-running operations
- Parallel execution considerations
- Resource usage patterns (disk I/O, network calls)
- Deduplication of identical hook commands
- Proper use of environment variables ($CLAUDE_PROJECT_DIR)

**Configuration Compliance:**
- Valid JSON structure in settings.json
- Proper matcher patterns for tool targeting
- Correct hook type specification ("command" vs "prompt")
- Appropriate timeout settings
- Integration with Claude Code's hook lifecycle

**Error Handling Review:**
- Exit code usage (0 for success, 2 to block, others for non-blocking)
- Stderr vs stdout usage patterns
- Graceful degradation when tools are missing
- JSON output format for advanced control
- Logging and debug output considerations

**Review Process:**
Examine the specified settings.json or hook configuration. For each hook found, provide specific line references, explain security implications, performance impact, and recommendations. Prioritize issues as critical (security vulnerability), high (performance problem), medium (best practices violation), or low (minor optimization).

## Hook Expert Delegation

For both create and review operations, I'll leverage the hook-development-expert agent which has:
- Deep knowledge of hook security patterns
- Experience with performance optimization
- Understanding of Claude Code's hook lifecycle
- Access to comprehensive hook documentation
- Expertise in script development for various languages

This specialized approach ensures you get expert guidance while keeping the slash command lightweight and focused.

## Reference Documentation

This command is informed by:
- `@/Users/dlawson/.claude/docs/hooks.md` - Getting started with hooks
- `@/Users/dlawson/.claude/docs/hooks-reference.md` - Comprehensive hook reference
- `@/Users/dlawson/.claude/docs/prompting-best-practices.md` - Claude 4.x prompting guidelines

All hook development follows Anthropic's security best practices and performance guidelines to ensure safe, efficient automation.

