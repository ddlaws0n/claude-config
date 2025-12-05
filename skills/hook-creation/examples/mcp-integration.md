# MCP Tool Integration Patterns

Comprehensive guide to hooking into Model Context Protocol (MCP) tools and servers within Claude Code. This document covers tool naming conventions, common MCP servers, real-world integration patterns, and production-ready examples.

## Table of Contents

1. [Introduction to MCP Tool Hooks](#introduction-to-mcp-tool-hooks)
2. [MCP Tool Naming Conventions](#mcp-tool-naming-conventions)
3. [Common MCP Servers & Tools](#common-mcp-servers--tools)
4. [Hook Patterns by Server](#hook-patterns-by-server)
5. [Real-World Integration Examples](#real-world-integration-examples)
6. [Best Practices & Error Handling](#best-practices--error-handling)

## Introduction to MCP Tool Hooks

### What Are MCP Tools?

MCP (Model Context Protocol) tools extend Claude Code with integrations to external systems and services. Unlike built-in Claude Code tools (Read, Write, Bash, etc.), MCP tools follow a standard pattern:

```
mcp__<server>__<tool>
```

For example:
- `mcp__memory__create_entities` - Create memory entities
- `mcp__filesystem__list_files` - List files in a directory
- `mcp__github__search_repositories` - Search GitHub repositories
- `mcp__brave_search__brave_web_search` - Web search

### How MCP Hooks Work

You can create PreToolUse, PostToolUse, and Stop hooks for MCP tools just like built-in Claude Code tools:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__github__.*",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/github-validator.py"
          }
        ]
      }
    ]
  }
}
```

### Tool Matching Patterns

MCP tools use the same matcher syntax as built-in tools:

```json
{
  "matcher": "mcp__memory__.*"           // All memory server tools
}

{
  "matcher": "mcp__.*__read.*"           // All read-like tools across all servers
}

{
  "matcher": "mcp__github__create.*"     // GitHub tools starting with 'create'
}

{
  "matcher": "mcp__github__.*|mcp__memory__.*"  // Multiple specific servers
}
```

## MCP Tool Naming Conventions

### Standard Format

```
mcp__<server_name>__<tool_name>
```

**Rules:**
- Server names use lowercase with underscores (e.g., `brave_search`, `anthropic_docs`)
- Tool names follow the MCP server's naming convention
- Use regex in matchers for flexible matching
- Pattern matching is case-sensitive

### Common Server Naming

| Server | Pattern | Example Tools |
|--------|---------|----------------|
| Memory | `mcp__memory__*` | `create_entities`, `delete_entities`, `search` |
| Filesystem | `mcp__filesystem__*` | `read_file`, `write_file`, `list_files` |
| GitHub | `mcp__github__*` | `search_repositories`, `get_issue`, `create_issue` |
| Brave Search | `mcp__brave_search__*` | `brave_web_search`, `brave_local_search` |
| Google Drive | `mcp__google_drive__*` | `search_files`, `create_file`, `read_file` |
| Slack | `mcp__slack__*` | `send_message`, `get_channel`, `list_channels` |

## Common MCP Servers & Tools

### Memory Server (`mcp__memory__*`)

The memory server helps maintain context across sessions by storing entities and relationships.

**Available Tools:**
- `create_entities` - Create memory entities
- `delete_entities` - Delete entities
- `search` - Search entities
- `search_relationships` - Find related entities

**Input Schema:**
```json
{
  "tool_name": "mcp__memory__create_entities",
  "tool_input": {
    "entities": [
      {
        "name": "entity_name",
        "entity_type": "string",
        "observations": ["observation1", "observation2"]
      }
    ]
  }
}
```

### Filesystem Server (`mcp__filesystem__*`)

Access and modify local filesystem with security controls.

**Available Tools:**
- `read_file` - Read file contents
- `write_file` - Write to file
- `list_files` - List directory
- `create_directory` - Create directory
- `move_file` - Move/rename file
- `delete_file` - Delete file
- `get_file_stats` - Get file metadata

**Input Schema:**
```json
{
  "tool_name": "mcp__filesystem__read_file",
  "tool_input": {
    "path": "/absolute/path/to/file"
  }
}
```

### GitHub Server (`mcp__github__*`)

Interact with GitHub repositories, issues, and pull requests.

**Available Tools:**
- `search_repositories` - Find repositories
- `get_repository` - Get repo details
- `search_issues` - Find issues
- `get_issue` - Get issue details
- `create_issue` - Create new issue
- `update_issue` - Update issue
- `search_code` - Search code
- `get_pull_request` - Get PR details
- `create_pull_request` - Create PR

**Input Schema:**
```json
{
  "tool_name": "mcp__github__search_repositories",
  "tool_input": {
    "query": "search term",
    "limit": 10
  }
}
```

### Brave Search Server (`mcp__brave_search__*`)

Web search and local business search via Brave Search API.

**Available Tools:**
- `brave_web_search` - Web search
- `brave_local_search` - Local business search

**Input Schema:**
```json
{
  "tool_name": "mcp__brave_search__brave_web_search",
  "tool_input": {
    "query": "search term",
    "count": 10
  }
}
```

### Custom MCP Servers

If you've implemented custom MCP servers, the same hooking patterns apply:

```json
{
  "matcher": "mcp__myserver__.*",
  "hooks": [
    {
      "type": "command",
      "command": "~/.claude/hooks/mcp-custom-validator.py"
    }
  ]
}
```

## Hook Patterns by Server

### Memory Server Integration Hooks

#### PreToolUse: Validate Entity Creation

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__memory__create_entities",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys\nfrom pathlib import Path\n\n# Read hook input\ndata = json.load(sys.stdin)\ntool_input = data.get('tool_input', {})\nentities = tool_input.get('entities', [])\n\n# Validate entities\nfor entity in entities:\n    name = entity.get('name', '')\n    entity_type = entity.get('entity_type', '')\n    observations = entity.get('observations', [])\n    \n    # Ensure required fields\n    if not name or not entity_type:\n        print('❌ Entity missing required fields: name and entity_type', file=sys.stderr)\n        sys.exit(2)\n    \n    # Validate observation structure\n    if not isinstance(observations, list):\n        print('❌ observations must be a list', file=sys.stderr)\n        sys.exit(2)\n    \n    if any(len(obs) > 1000 for obs in observations):\n        print('⚠️ Warning: Large observation detected (> 1000 chars)', file=sys.stderr)\n\nprint(f'✅ Valid entities: {len(entities)} entity(ies)', file=sys.stderr)\nsys.exit(0)\n\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

#### PostToolUse: Log Entity Creation

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "mcp__memory__create_entities|mcp__memory__delete_entities",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c '\ninput=$(cat)\ntool_name=$(echo \"$input\" | jq -r \".tool_name\")\ntool_input=$(echo \"$input\" | jq -r \".tool_input\")\ntool_response=$(echo \"$input\" | jq -r \".tool_response // empty\")\n\n# Create audit log\naudit_dir=\"${HOME}/.claude/memory-audit\"\nmkdir -p \"$audit_dir\"\n\nlog_file=\"$audit_dir/$(date +%Y-%m-%d).log\"\nlog_entry=$(printf \"[%s] %s\\n%s\\n---\\n\" \"$(date +%H:%M:%S)\" \"$tool_name\" \"$tool_input\")\n\necho \"$log_entry\" >> \"$log_file\"\n\nif [ ! -z \"$tool_response\" ]; then\n    echo \"✅ Memory operation logged\" >&2\nfi\n\nexit 0'",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### Filesystem Server Integration Hooks

#### PreToolUse: Security & Access Control

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__filesystem__write_file|mcp__filesystem__delete_file",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, os\nfrom pathlib import Path\n\n# Read hook input\ndata = json.load(sys.stdin)\ntool_name = data.get('tool_name', '')\ntool_input = data.get('tool_input', {})\nfile_path = tool_input.get('path', '')\n\n# Security restrictions\nRESTRICTED_PATHS = [\n    '.env', '.env.local', '.env.production',\n    '.git', '.gitignore',\n    'node_modules', 'dist', 'build',\n    '/root', '/etc', '/sys', '/proc',\n    '~/.ssh', '~/.aws', '~/.kube'\n]\n\ndef is_restricted(path_str):\n    path = Path(path_str).expanduser()\n    path_str_lower = str(path).lower()\n    \n    for restricted in RESTRICTED_PATHS:\n        if restricted.startswith('/'):\n            if restricted in path_str_lower:\n                return True\n        elif path.name == restricted or restricted in path.parts:\n            return True\n    return False\n\nif is_restricted(file_path):\n    print(f'❌ Cannot modify restricted path: {file_path}', file=sys.stderr)\n    sys.exit(2)\n\n# Warn about writing large files\nif tool_name == 'mcp__filesystem__write_file':\n    content = tool_input.get('content', '')\n    if len(content) > 10_000_000:  # 10MB\n        print(f'⚠️ Warning: Writing large file ({len(content) / 1e6:.1f}MB)', file=sys.stderr)\n\nprint(f'✅ Access allowed for: {Path(file_path).name}', file=sys.stderr)\nsys.exit(0)\n\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

#### PostToolUse: Track Filesystem Changes

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "mcp__filesystem__.*",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c '\ninput=$(cat)\ntool_name=$(echo \"$input\" | jq -r \".tool_name\")\nfile_path=$(echo \"$input\" | jq -r \".tool_input.path // empty\")\n\nif [ -z \"$file_path\" ]; then\n    exit 0\nfi\n\n# Log filesystem operations\naudit_log=\"${HOME}/.claude/filesystem-audit.log\"\necho \"[$(date \\'+%Y-%m-%d %H:%M:%S\\')]\" \"$tool_name\" \"$file_path\" >> \"$audit_log\"\n\necho \"🔍 Filesystem operation logged\" >&2\nexit 0'",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### GitHub Server Integration Hooks

#### PreToolUse: Validate GitHub Operations

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__github__create_issue|mcp__github__create_pull_request",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys\n\ndata = json.load(sys.stdin)\ntool_name = data.get('tool_name', '')\ntool_input = data.get('tool_input', {})\n\n# Validate required fields\nrequired_fields = {\n    'mcp__github__create_issue': ['title', 'body', 'repo'],\n    'mcp__github__create_pull_request': ['title', 'head', 'base', 'repo']\n}\n\nif tool_name in required_fields:\n    for field in required_fields[tool_name]:\n        if field not in tool_input or not tool_input[field]:\n            print(f'❌ Missing required field: {field}', file=sys.stderr)\n            sys.exit(2)\n\n# Validate title length\ntitle = tool_input.get('title', '')\nif len(title) > 100:\n    print(f'⚠️ Warning: Title is very long ({len(title)} chars)', file=sys.stderr)\n\nif len(title) > 500:\n    print('❌ Title exceeds maximum length (500 chars)', file=sys.stderr)\n    sys.exit(2)\n\nprint(f'✅ GitHub operation validated: {tool_name}', file=sys.stderr)\nsys.exit(0)\n\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

#### PostToolUse: Track GitHub Actions

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "mcp__github__.*",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c '\ninput=$(cat)\ntool_name=$(echo \"$input\" | jq -r \".tool_name\")\ntool_response=$(echo \"$input\" | jq -r \".tool_response\")\n\n# Extract meaningful data from response\ncase \"$tool_name\" in\n    *create_issue*)\n        issue_url=$(echo \"$tool_response\" | jq -r \".url // empty\")\n        echo \"📝 Issue created: $issue_url\" >&2\n        ;;\n    *create_pull_request*)\n        pr_url=$(echo \"$tool_response\" | jq -r \".url // empty\")\n        echo \"🔀 Pull request created: $pr_url\" >&2\n        ;;\n    *)\n        echo \"✅ GitHub operation completed\" >&2\n        ;;\nesac\n\n# Log to file\naudit_log=\"${HOME}/.claude/github-audit.log\"\necho \"[$(date \\'+%Y-%m-%d %H:%M:%S\\')]\" \"$tool_name\" >> \"$audit_log\"\n\nexit 0'",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### Brave Search Server Integration Hooks

#### PreToolUse: Rate Limiting & Privacy Checks

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__brave_search__.*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, os, time\nfrom pathlib import Path\n\ndata = json.load(sys.stdin)\ntool_name = data.get('tool_name', '')\ntool_input = data.get('tool_input', {})\nquery = tool_input.get('query', '')\n\n# Rate limiting: track searches per minute\nrate_file = Path(os.path.expanduser('~/.claude/search-rate.txt'))\nrate_file.parent.mkdir(parents=True, exist_ok=True)\n\ncurrent_time = time.time()\nmin_ago = current_time - 60\n\n# Read existing searches\nsearches = []\nif rate_file.exists():\n    with open(rate_file) as f:\n        for line in f:\n            ts = float(line.strip())\n            if ts > min_ago:\n                searches.append(ts)\n\n# Check rate limit (max 10 per minute)\nif len(searches) >= 10:\n    print(f'❌ Rate limit exceeded: {len(searches)} searches in last minute', file=sys.stderr)\n    sys.exit(2)\n\n# Log this search\nwith open(rate_file, 'a') as f:\n    f.write(f'{current_time}\\n')\n\n# Privacy checks\nsensitive_patterns = [\n    'password', 'secret', 'api key', 'token',\n    'ssn', 'credit card', 'private key'\n]\n\nquery_lower = query.lower()\nfor pattern in sensitive_patterns:\n    if pattern in query_lower:\n        print(f'⚠️ Warning: Searching for sensitive information: {pattern}', file=sys.stderr)\n        break\n\nprint(f'✅ Search allowed: {len(searches) + 1}/10 searches used', file=sys.stderr)\nsys.exit(0)\n\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

#### PostToolUse: Log Search Results

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "mcp__brave_search__brave_web_search",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c '\ninput=$(cat)\ntool_input=$(echo \"$input\" | jq -r \".tool_input\")\nquery=$(echo \"$tool_input\" | jq -r \".query\")\ntool_response=$(echo \"$input\" | jq -r \".tool_response // {}\")\n\n# Extract result count\nresult_count=$(echo \"$tool_response\" | jq \".results | length // 0\")\n\n# Log search query (for analytics)\nsearch_log=\"${HOME}/.claude/search-log.jsonl\"\nlog_entry=$(printf \"{\\\"timestamp\\\": \\\"$(date -Iseconds)\\\", \\\"query\\\": \\\"$query\\\", \\\"results\\\": $result_count}\")\necho \"$log_entry\" >> \"$search_log\"\n\necho \"🔎 Found $result_count results for: $query\" >&2\nexit 0'",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

## Real-World Integration Examples

### Example 1: Memory-Based Project Context

Automatically maintain project entity memory when working with code:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 << 'HOOK_EOF'\nimport json, sys, os, re\nfrom pathlib import Path\n\ndata = json.load(sys.stdin)\nfile_path = data.get('tool_input', {}).get('file_path', '')\ncontent = data.get('tool_input', {}).get('content', '')\n\n# Only track Python files\nif not file_path.endswith('.py'):\n    sys.exit(0)\n\n# Extract functions and classes\nfunctions = re.findall(r'def\\s+(\\w+)\\s*\\(', content)\nclasses = re.findall(r'class\\s+(\\w+)\\s*[\\(:]', content)\n\nif not (functions or classes):\n    sys.exit(0)\n\n# Prepare memory update (would be sent to memory server)\nmemory_update = {\n    'entities': [\n        {\n            'name': f'File: {Path(file_path).name}',\n            'entity_type': 'python_file',\n            'observations': [\n                f'Contains {len(functions)} functions: {\", \".join(functions[:5])}',\n                f'Contains {len(classes)} classes: {\", \".join(classes[:5])}'\n            ]\n        }\n    ]\n}\n\nprint(json.dumps(memory_update), file=sys.stderr)\nprint('💾 Project context updated in memory', file=sys.stderr)\nsys.exit(0)\nHOOK_EOF",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

### Example 2: Automated Issue & PR Workflow

Create issues from code comments and track with GitHub:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 << 'HOOK_EOF'\nimport json, sys, os, re\nfrom pathlib import Path\n\ndata = json.load(sys.stdin)\nfile_path = data.get('tool_input', {}).get('file_path', '')\ncontent = data.get('tool_input', {}).get('content', '')\n\n# Find TODO/FIXME comments\npattern = r'#\\s*(TODO|FIXME):\\s*(.+)'\nmatches = re.findall(pattern, content)\n\nif not matches:\n    sys.exit(0)\n\nprint(f'Found {len(matches)} action items', file=sys.stderr)\n\nfor tag, text in matches:\n    # Log would trigger GitHub issue creation in a full setup\n    print(f'  {tag}: {text[:50]}...', file=sys.stderr)\n\nsys.exit(0)\nHOOK_EOF",
            "timeout": 5\n          }\n        ]\n      }\n    ]\n  }\n}\n```\n\n### Example 3: Search-Driven Documentation Generation\n\nAutomatically search for and document APIs:\n\n```json\n{\n  \"hooks\": {\n    \"PostToolUse\": [\n      {\n        \"matcher\": \"mcp__brave_search__brave_web_search\",\n        \"hooks\": [\n          {\n            \"type\": \"command\",\n            \"command\": \"python3 << 'HOOK_EOF'\nimport json, sys\n\ndata = json.load(sys.stdin)\ntool_input = data.get('tool_input', {})\nquery = tool_input.get('query', '')\nresponse = data.get('tool_response', {})\nresults = response.get('results', [])\n\n# Auto-generate documentation snippet\nif 'API' in query.upper() and results:\n    doc_entries = []\n    for result in results[:3]:\n        title = result.get('title', '')\n        url = result.get('url', '')\n        doc_entries.append(f'- [{title}]({url})')\n    \n    print('📚 API Documentation References:', file=sys.stderr)\n    for entry in doc_entries:\n        print(f'  {entry}', file=sys.stderr)\n\nsys.exit(0)\nHOOK_EOF\",\n            \"timeout\": 5\n          }\n        ]\n      }\n    ]\n  }\n}\n```\n\n### Example 4: Cross-Server Integration\n\nIntegrate multiple MCP servers in a workflow:\n\n```json\n{\n  \"hooks\": {\n    \"PreToolUse\": [\n      {\n        \"matcher\": \"mcp__github__create_issue\",\n        \"hooks\": [\n          {\n            \"type\": \"command\",\n            \"command\": \"python3 << 'HOOK_EOF'\nimport json, sys\n\ndata = json.load(sys.stdin)\ntool_input = data.get('tool_input', {})\ntitle = tool_input.get('title', '')\nbody = tool_input.get('body', '')\nrepo = tool_input.get('repo', '')\n\n# Validate against memory entities\nvalidation_errors = []\n\n# Check title length\nif len(title) < 5:\n    validation_errors.append('Title too short (min 5 chars)')\n\nif len(body) < 20:\n    validation_errors.append('Body too short (min 20 chars)')\n\n# Check repo format\nif '/' not in repo:\n    validation_errors.append('Repo must be in format: owner/repo')\n\nif validation_errors:\n    for error in validation_errors:\n        print(f'❌ {error}', file=sys.stderr)\n    sys.exit(2)\n\nprint(f'✅ Issue validated for {repo}', file=sys.stderr)\nsys.exit(0)\nHOOK_EOF\",\n            \"timeout\": 5\n          }\n        ]\n      }\n    ]\n  }\n}\n```\n\n## Best Practices & Error Handling\n\n### Security Considerations\n\n1. **Validate All Inputs**: Always validate tool inputs in PreToolUse hooks\n   ```python\n   # Always validate paths, queries, and user input\n   if not validate_safe_path(file_path):\n       print('❌ Invalid path', file=sys.stderr)\n       sys.exit(2)\n   ```\n\n2. **Restrict Sensitive Operations**: Block access to sensitive files/APIs\n   ```python\n   RESTRICTED_PATTERNS = ['.env', '.aws', 'secret', 'password']\n   if any(pattern in str(path) for pattern in RESTRICTED_PATTERNS):\n       sys.exit(2)  # Block operation\n   ```\n\n3. **Audit Logging**: Track all MCP operations for security\n   ```bash\n   audit_log=\"${HOME}/.claude/mcp-audit.log\"\n   echo \"[$(date)] $tool_name $tool_input\" >> \"$audit_log\"\n   ```\n\n### Performance Patterns\n\n1. **Use PreToolUse for Validation**: Fast checks before execution\n   - Typical timeout: 2-5 seconds\n   - Block immediately on validation errors\n\n2. **Use PostToolUse for Logging**: Record operations after completion\n   - Typical timeout: 5-10 seconds\n   - Non-blocking, use exit 0 always\n\n3. **Defer Heavy Operations**: Move expensive tasks to Stop hooks\n   ```json\n   {\n     \"matcher\": \"mcp__.*\",\n     \"hooks\": [\n       {\n         \"type\": \"command\",\n         \"command\": \"time_intensive_analysis.py\",\n         \"timeout\": 60\n       }\n     ]\n   }\n   ```\n\n### Error Handling Patterns\n\n#### Graceful Degradation\n```python\ntry:\n    # Try to use external resource\n    result = call_external_api()\nexcept ConnectionError:\n    # Fall back gracefully\n    print('⚠️ API unavailable, skipping', file=sys.stderr)\n    sys.exit(0)  # Allow operation to continue\n```\n\n#### Rate Limiting Backoff\n```python\nif rate_limited:\n    print('⚠️ Rate limited, retrying in 30s', file=sys.stderr)\n    time.sleep(30)\n    retry = True\n```\n\n#### Comprehensive Logging\n```bash\n# Log both success and failure\nlog_entry=$(cat <<EOF\n{\n  \"timestamp\": \"$(date -Iseconds)\",\n  \"tool\": \"$tool_name\",\n  \"status\": \"$status\",\n  \"error\": \"$error_msg\"\n}\nEOF\n)\necho \"$log_entry\" >> \"$HOME/.claude/mcp-ops.jsonl\"\n```\n\n### Testing MCP Hooks\n\n#### Test PreToolUse Hook\n```bash\n# Create test input\ncat > test-input.json <<'EOF'\n{\n  \"session_id\": \"test\",\n  \"hook_event_name\": \"PreToolUse\",\n  \"tool_name\": \"mcp__memory__create_entities\",\n  \"tool_input\": {\n    \"entities\": [\n      {\n        \"name\": \"TestEntity\",\n        \"entity_type\": \"test\",\n        \"observations\": [\"test observation\"]\n      }\n    ]\n  }\n}\nEOF\n\n# Run hook\ncat test-input.json | python3 mcp-validator.py\n```\n\n#### Test PostToolUse Hook\n```bash\ncat > test-response.json <<'EOF'\n{\n  \"session_id\": \"test\",\n  \"hook_event_name\": \"PostToolUse\",\n  \"tool_name\": \"mcp__github__create_issue\",\n  \"tool_input\": { \"title\": \"Test\", \"body\": \"Test\" },\n  \"tool_response\": { \"url\": \"https://github.com/...\", \"id\": \"123\" }\n}\nEOF\n\ncat test-response.json | bash mcp-logger.sh\n```\n\n### Configuration Best Practices\n\n1. **Use Absolute Paths**: Always use `$CLAUDE_PROJECT_DIR` or `~`\n   ```json\n   \"command\": \"$CLAUDE_PROJECT_DIR/.claude/hooks/validate.py\"\n   ```\n\n2. **Set Appropriate Timeouts**: Based on operation complexity\n   - Simple validation: 2-5 seconds\n   - Network operations: 10-30 seconds\n   - Batch operations: 30-60 seconds\n\n3. **Handle Missing Tools**: Don't fail if external tools are unavailable\n   ```bash\n   if ! command -v curl &> /dev/null; then\n       echo \"⚠️ curl not available, skipping\" >&2\n       exit 0  # Don't block\n   fi\n   ```\n\n4. **Document Hook Purpose**: Add comments for maintainability\n   ```json\n   {\n     \"matcher\": \"mcp__memory__.*\",\n     \"hooks\": [\n       {\n         \"type\": \"command\",\n         \"command\": \"validate-memory.py\",\n         \"description\": \"Validates memory entities before creation\"\n       }\n     ]\n   }\n   ```\n\n## Debugging MCP Hooks\n\n### Enable Debug Output\n```bash\n# Run Claude Code with debug logging\nclaude --debug\n\n# Check hook execution in output\n# Look for: PreToolUse hooks, PostToolUse hooks, Stop hooks\n```\n\n### Inspect Hook Input/Output\n```bash\n# Save hook input to file for inspection\nclaude_input=$(cat)\necho \"$claude_input\" > /tmp/hook-debug.json\n\n# Process with your hook\necho \"$claude_input\" | python3 your-hook.py\n```\n\n### Common Issues & Solutions\n\n**Hook Not Running**\n- Check syntax: `jq . .claude/settings.json`\n- Verify matcher pattern\n- Restart Claude Code after config changes\n\n**Hook Blocking Operations Unexpectedly**\n- Check exit code: should be 0 to allow, 2 to block\n- Review stderr output with `claude --debug`\n- Reduce timeout if hook is taking too long\n\n**Performance Issues**\n- Move to Stop hook if taking > 2 seconds\n- Reduce JSON parsing overhead in hot loops\n- Cache external API responses when possible\n\n## See Also\n\n- [Hook Creation Reference](../REFERENCE.md) - Complete API reference\n- [Security Templates](../templates/security.md) - Security-focused examples\n- [Development Templates](../templates/development.md) - Workflow automation\n