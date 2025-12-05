# Advanced Claude Code Tools: Hook Integration

Comprehensive guide to creating hooks for advanced Claude Code tools including NotebookEdit, WebSearch, TodoWrite, Skill, SlashCommand, and environment-aware operations. This document covers practical patterns, security considerations, and production-ready examples.

## Table of Contents

1. [NotebookEdit Hooks](#notebookedit-hooks)
2. [WebSearch Hooks](#websearch-hooks)
3. [TodoWrite Hooks](#todowrite-hooks)
4. [Skill & SlashCommand Hooks](#skill--slashcommand-hooks)
5. [BashOutput Hooks](#bashoutput-hooks)
6. [Environment-Aware Hooks (CLAUDE_CODE_REMOTE)](#environment-aware-hooks-claude_code_remote)
7. [Cross-Tool Integration](#cross-tool-integration)
8. [Best Practices](#best-practices)

## NotebookEdit Hooks

The NotebookEdit tool modifies Jupyter notebooks programmatically. Use hooks to validate, secure, and monitor notebook operations.

### PreToolUse: Validate Notebook Edits

Prevent invalid cell modifications and ensure notebook integrity:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "NotebookEdit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys\nfrom pathlib import Path\n\ndata = json.load(sys.stdin)\ntool_input = data.get('tool_input', {})\nnotebook_path = tool_input.get('notebook_path', '')\nnew_source = tool_input.get('new_source', '')\nedit_mode = tool_input.get('edit_mode', 'replace')\n\n# Validate notebook path\nif not notebook_path.endswith('.ipynb'):\n    print('❌ Invalid file: must be a .ipynb notebook', file=sys.stderr)\n    sys.exit(2)\n\n# Validate path is absolute\nif not notebook_path.startswith('/'):\n    print('❌ Notebook path must be absolute', file=sys.stderr)\n    sys.exit(2)\n\n# Validate notebook exists\nif not Path(notebook_path).exists():\n    print(f'❌ Notebook not found: {notebook_path}', file=sys.stderr)\n    sys.exit(2)\n\n# Validate source content\nif edit_mode == 'insert' or edit_mode == 'replace':\n    if not new_source or len(new_source.strip()) == 0:\n        print('❌ Cannot insert/replace with empty source', file=sys.stderr)\n        sys.exit(2)\n\n# Warn on large cells (> 1000 lines)\nlines = new_source.count('\\n')\nif lines > 1000:\n    print(f'⚠️ Warning: Cell is very large ({lines} lines)', file=sys.stderr)\n\n# Check for dangerous patterns\ndangerous_patterns = [\n    'os.system', 'subprocess', 'eval(', 'exec(',\n    '__import__', 'compile(', 'pickle.load'\n]\n\nfor pattern in dangerous_patterns:\n    if pattern in new_source and edit_mode in ['insert', 'replace']:\n        print(f'⚠️ Warning: Cell contains potentially dangerous pattern: {pattern}', file=sys.stderr)\n\nprint(f'✅ Notebook edit validated: {edit_mode} mode', file=sys.stderr)\nsys.exit(0)\n\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### PostToolUse: Auto-Format Notebook Cells

Automatically format Python code in notebook cells:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "NotebookEdit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, subprocess\nfrom pathlib import Path\n\ndata = json.load(sys.stdin)\nnotebook_path = data.get('tool_input', {}).get('notebook_path', '')\nnew_source = data.get('tool_input', {}).get('new_source', '')\ncell_type = data.get('tool_input', {}).get('cell_type', 'code')\n\nif cell_type != 'code' or not new_source:\n    sys.exit(0)\n\n# Try to format with black if available\nif not Path(notebook_path).exists():\n    sys.exit(0)\n\ntry:\n    # Format with ruff\n    if subprocess.run(['which', 'ruff'], capture_output=True).returncode == 0:\n        formatted = subprocess.run(\n            ['ruff', 'format', '-'],\n            input=new_source.encode(),\n            capture_output=True,\n            timeout=10\n        )\n        \n        if formatted.returncode == 0:\n            print('✅ Cell code formatted with ruff', file=sys.stderr)\n        else:\n            print('⚠️ Ruff formatting failed', file=sys.stderr)\nexcept Exception as e:\n    print(f'⚠️ Could not format cell: {e}', file=sys.stderr)\n\nsys.exit(0)\n\"",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
```

### Stop Hook: Validate Entire Notebook

Comprehensive notebook validation when Claude finishes:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys\nfrom pathlib import Path\n\n# This would be triggered by transcript analysis in real implementation\n# Here's a pattern for validating edited notebooks\n\ndef validate_notebook(nb_path):\n    '''Validate notebook structure and content'''\n    errors = []\n    warnings = []\n    \n    try:\n        with open(nb_path) as f:\n            nb = json.load(f)\n    except json.JSONDecodeError as e:\n        return [f'Invalid JSON: {e}'], []\n    \n    # Check notebook structure\n    if 'cells' not in nb:\n        errors.append('Missing cells array')\n    \n    if 'metadata' not in nb:\n        warnings.append('Missing notebook metadata')\n    \n    # Validate cells\n    for i, cell in enumerate(nb.get('cells', [])):\n        if 'cell_type' not in cell:\n            errors.append(f'Cell {i} missing cell_type')\n        \n        if 'source' not in cell:\n            errors.append(f'Cell {i} missing source')\n        \n        # Check for execution errors in output\n        if cell.get('cell_type') == 'code':\n            for output in cell.get('outputs', []):\n                if output.get('output_type') == 'error':\n                    errors.append(f'Cell {i} has execution error')\n    \n    return errors, warnings\n\n# Check all notebooks in project\nfor nb_file in Path('.').glob('**/*.ipynb'):\n    errors, warnings = validate_notebook(nb_file)\n    \n    if errors:\n        print(f'❌ Notebook errors in {nb_file}:', file=sys.stderr)\n        for error in errors:\n            print(f'  - {error}', file=sys.stderr)\n    \n    if warnings:\n        print(f'⚠️ Notebook warnings in {nb_file}:', file=sys.stderr)\n        for warning in warnings:\n            print(f'  - {warning}', file=sys.stderr)\n\nsys.exit(0)\n\"",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

## WebSearch Hooks

The WebSearch and WebFetch tools access external web content. Use hooks for privacy, rate limiting, and cost tracking.

### PreToolUse: Privacy & Rate Limiting

Protect user privacy and prevent API abuse:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "WebSearch|WebFetch|mcp__brave_search__.*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, os, time\nfrom pathlib import Path\nfrom urllib.parse import urlparse\n\ndata = json.load(sys.stdin)\ntool_name = data.get('tool_name', '')\ntool_input = data.get('tool_input', {})\n\n# Get query or URL\nquery = tool_input.get('query', tool_input.get('url', ''))\n\n# Privacy check: Block searches for sensitive information\nsensitive_keywords = [\n    'password', 'credit card', 'social security',\n    'private key', 'api key', 'secret token',\n    'home address', 'phone number', 'ssn',\n    'bank account', 'routing number'\n]\n\nquery_lower = query.lower()\nfor keyword in sensitive_keywords:\n    if keyword in query_lower:\n        print(f'❌ Cannot search for sensitive information: {keyword}', file=sys.stderr)\n        sys.exit(2)\n\n# Block access to blocked domains\nblocked_domains = [\n    'localhost', '127.0.0.1', '192.168',  # Local addresses\n    'internal-api', 'admin-panel',  # Internal services\n]\n\nif 'url' in tool_input:\n    parsed_url = urlparse(query)\n    for blocked in blocked_domains:\n        if blocked in parsed_url.netloc.lower():\n            print(f'❌ Cannot access blocked domain: {blocked}', file=sys.stderr)\n            sys.exit(2)\n\n# Rate limiting\nrate_file = Path(os.path.expanduser('~/.claude/search-rate.json'))\nrate_file.parent.mkdir(parents=True, exist_ok=True)\n\ncurrent_time = time.time()\nmin_ago = current_time - 60\nsearches_this_minute = 0\n\nif rate_file.exists():\n    try:\n        with open(rate_file) as f:\n            times = json.load(f)\n            searches_this_minute = sum(1 for t in times if t > min_ago)\n    except:\n        pass\n\n# Enforce rate limit (30 searches per minute)\nif searches_this_minute >= 30:\n    print(f'⚠️ Rate limit approaching: {searches_this_minute}/30 searches', file=sys.stderr)\n\nif searches_this_minute >= 45:\n    print(f'❌ Rate limit exceeded: {searches_this_minute}/30', file=sys.stderr)\n    sys.exit(2)\n\n# Log search\ntry:\n    with open(rate_file) as f:\n        times = json.load(f)\nexcept:\n    times = []\n\ntimes = [t for t in times if t > min_ago]  # Keep only recent\ntimes.append(current_time)\n\nwith open(rate_file, 'w') as f:\n    json.dump(times, f)\n\nprint(f'✅ Search allowed ({searches_this_minute + 1}/30 this minute)', file=sys.stderr)\nsys.exit(0)\n\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### PostToolUse: Log & Cache Results

Track searches and cache results for efficiency:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "WebSearch|WebFetch|mcp__brave_search__.*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, os\nfrom pathlib import Path\nimport hashlib\nfrom datetime import datetime\n\ndata = json.load(sys.stdin)\ntool_name = data.get('tool_name', '')\ntool_input = data.get('tool_input', {})\ntool_response = data.get('tool_response', {})\n\n# Extract query/URL\nquery = tool_input.get('query', tool_input.get('url', ''))\n\n# Create search log entry\nlog_entry = {\n    'timestamp': datetime.utcnow().isoformat(),\n    'tool': tool_name,\n    'query': query[:100],  # Truncate for privacy\n    'query_hash': hashlib.sha256(query.encode()).hexdigest()[:8],\n    'result_count': len(tool_response.get('results', [])),\n    'status': 'success'\n}\n\n# Log to JSONL file\nlog_file = Path(os.path.expanduser('~/.claude/search-log.jsonl'))\nlog_file.parent.mkdir(parents=True, exist_ok=True)\n\nwith open(log_file, 'a') as f:\n    f.write(json.dumps(log_entry) + '\\n')\n\n# Cache successful results\nif tool_response.get('results'):\n    cache_dir = Path(os.path.expanduser('~/.claude/search-cache'))\n    cache_dir.mkdir(parents=True, exist_ok=True)\n    \n    # Use query hash as cache key\n    cache_file = cache_dir / f'{log_entry[\"query_hash\"]}.json'\n    cache_entry = {\n        'query': query,\n        'timestamp': log_entry['timestamp'],\n        'results': tool_response.get('results', [])\n    }\n    \n    with open(cache_file, 'w') as f:\n        json.dump(cache_entry, f)\n    \n    print(f'💾 Results cached: {len(tool_response.get(\"results\", []))} items', file=sys.stderr)\n\nprint(f'📊 Search logged: {query[:50]}...', file=sys.stderr)\nsys.exit(0)\n\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

## TodoWrite Hooks

The TodoWrite tool manages task lists. Use hooks for productivity analytics and automation.

### PreToolUse: Validate Todo Structure

Ensure todos are well-formed and actionable:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "TodoWrite",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys\n\ndata = json.load(sys.stdin)\ntool_input = data.get('tool_input', {})\ntodos = tool_input.get('todos', [])\n\nif not isinstance(todos, list):\n    print('❌ todos must be an array', file=sys.stderr)\n    sys.exit(2)\n\nerrors = []\nwarnings = []\n\nfor i, todo in enumerate(todos):\n    # Validate required fields\n    if 'content' not in todo or not todo['content'].strip():\n        errors.append(f'Todo {i}: missing or empty content')\n    \n    if 'status' not in todo:\n        errors.append(f'Todo {i}: missing status field')\n    else:\n        valid_statuses = ['pending', 'in_progress', 'completed']\n        if todo['status'] not in valid_statuses:\n            errors.append(f'Todo {i}: invalid status {todo[\"status\"]}')\n    \n    # Check active form\n    if 'activeForm' not in todo or not todo['activeForm'].strip():\n        errors.append(f'Todo {i}: missing activeForm (present continuous verb)')\n    \n    # Warnings\n    content = todo.get('content', '')\n    if len(content) > 200:\n        warnings.append(f'Todo {i}: very long content ({len(content)} chars)')\n    \n    # Check if passive voice in content (should be imperative)\n    if content.lower().startswith(('is ', 'was ', 'are ', 'were ', 'being ', 'be ')):\n        warnings.append(f'Todo {i}: use imperative voice (e.g., \"Write\" not \"Writing\")')\n\nif errors:\n    for error in errors:\n        print(f'❌ {error}', file=sys.stderr)\n    sys.exit(2)\n\nif warnings:\n    for warning in warnings:\n        print(f'⚠️ {warning}', file=sys.stderr)\n\nprint(f'✅ {len(todos)} todos validated', file=sys.stderr)\nsys.exit(0)\n\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### PostToolUse: Track Todo Metrics

Analyze todo patterns for productivity insights:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "TodoWrite",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, os\nfrom pathlib import Path\nfrom datetime import datetime\nfrom collections import Counter\n\ndata = json.load(sys.stdin)\ntodos = data.get('tool_input', {}).get('todos', [])\n\n# Analyze todo metrics\nmetrics = {\n    'timestamp': datetime.utcnow().isoformat(),\n    'total_todos': len(todos),\n    'completed': sum(1 for t in todos if t.get('status') == 'completed'),\n    'in_progress': sum(1 for t in todos if t.get('status') == 'in_progress'),\n    'pending': sum(1 for t in todos if t.get('status') == 'pending'),\n    'avg_content_length': sum(len(t.get('content', '')) for t in todos) // max(1, len(todos))\n}\n\n# Extract action verbs\naction_verbs = []\nfor todo in todos:\n    content = todo.get('content', '')\n    first_word = content.split()[0] if content.split() else ''\n    if first_word:\n        action_verbs.append(first_word.lower())\n\nif action_verbs:\n    verb_counts = Counter(action_verbs)\n    metrics['top_actions'] = dict(verb_counts.most_common(3))\n\n# Log metrics\nmetrics_file = Path(os.path.expanduser('~/.claude/todo-metrics.jsonl'))\nmetrics_file.parent.mkdir(parents=True, exist_ok=True)\n\nwith open(metrics_file, 'a') as f:\n    f.write(json.dumps(metrics) + '\\n')\n\n# Print summary\ncompletion_rate = (metrics['completed'] / max(1, metrics['total_todos'])) * 100\nprint(f'📊 Todo Metrics:', file=sys.stderr)\nprint(f'  Total: {metrics[\"total_todos\"]}, Completed: {metrics[\"completed\"]} ({completion_rate:.0f}%)', file=sys.stderr)\nprint(f'  In Progress: {metrics[\"in_progress\"]}, Pending: {metrics[\"pending\"]}', file=sys.stderr)\n\nif 'top_actions' in metrics:\n    print(f'  Top Actions: {\", \".join(metrics[\"top_actions\"].keys())}', file=sys.stderr)\n\nsys.exit(0)\n\"",
            "timeout": 5\n          }\n        ]\n      }\n    ]\n  }\n}\n```\n\n### Stop Hook: Auto-Prioritization\n\nAutomatically reorganize todos based on patterns:\n\n```json\n{\n  \"hooks\": {\n    \"Stop\": [\n      {\n        \"hooks\": [\n          {\n            \"type\": \"command\",\n            \"command\": \"python3 -c \"\\\nimport json, os\nfrom pathlib import Path\n\n# This is a conceptual pattern for analyzing completed vs pending items\n# In a real implementation, this would be triggered by transcript analysis\n\nmetrics_file = Path(os.path.expanduser('~/.claude/todo-metrics.jsonl'))\n\nif not metrics_file.exists():\n    exit(0)\n\n# Read last few metrics entries\nwith open(metrics_file) as f:\n    lines = f.readlines()\n    recent = [json.loads(line) for line in lines[-5:]]\n\n# Analyze completion trend\nif len(recent) >= 2:\n    completion_trend = [m['completed'] / max(1, m['total_todos']) * 100 for m in recent]\n    recent_completion = completion_trend[-1]\n    \n    # Provide feedback\n    if recent_completion > 80:\n        print('🚀 High completion rate! Keep momentum up', file=sys.stderr)\n    elif recent_completion < 20:\n        print('⚠️ Low completion rate. Consider reducing task scope.', file=sys.stderr)\n\nexit(0)\n\\\"\",\n            \"timeout\": 10\n          }\n        ]\n      }\n    ]\n  }\n}\n```\n\n## Skill & SlashCommand Hooks\n\nHook into custom Skills and SlashCommands for usage tracking and permission control.\n\n### PreToolUse: Track Skill Usage\n\nLog when Skills and SlashCommands are invoked:\n\n```json\n{\n  \"hooks\": {\n    \"PreToolUse\": [\n      {\n        \"matcher\": \"Skill|SlashCommand\",\n        \"hooks\": [\n          {\n            \"type\": \"command\",\n            \"command\": \"python3 -c \"\nimport json, sys, os, time\nfrom pathlib import Path\nfrom datetime import datetime\n\ndata = json.load(sys.stdin)\ntool_name = data.get('tool_name', '')\ntool_input = data.get('tool_input', {})\n\n# Extract skill/command name\nskill_name = tool_input.get('skill', '') if tool_name == 'Skill' else ''\ncommand_name = tool_input.get('command', '') if tool_name == 'SlashCommand' else ''\n\nname = skill_name or command_name\nif not name:\n    sys.exit(0)\n\n# Log usage\nusage_file = Path(os.path.expanduser('~/.claude/skill-usage.jsonl'))\nusage_file.parent.mkdir(parents=True, exist_ok=True)\n\nlog_entry = {\n    'timestamp': datetime.utcnow().isoformat(),\n    'type': tool_name.lower(),\n    'name': name,\n    'input': str(tool_input)[:100]  # Truncate for privacy\n}\n\nwith open(usage_file, 'a') as f:\n    f.write(json.dumps(log_entry) + '\\n')\n\nprint(f'📝 Invoking {tool_name}: {name}', file=sys.stderr)\nsys.exit(0)\n\"",\n            \"timeout\": 5\n          }\n        ]\n      }\n    ]\n  }\n}\n```\n\n### PostToolUse: Monitor Skill Performance\n\nTrack skill execution time and success rates:\n\n```json\n{\n  \"hooks\": {\n    \"PostToolUse\": [\n      {\n        \"matcher\": \"Skill|SlashCommand\",\n        \"hooks\": [\n          {\n            \"type\": \"command\",\n            \"command\": \"python3 -c \"\nimport json, sys, os\nfrom pathlib import Path\nfrom datetime import datetime\n\ndata = json.load(sys.stdin)\ntool_name = data.get('tool_name', '')\ntool_response = data.get('tool_response', {})\n\n# Extract status from response\nsuccess = tool_response.get('success', True) if isinstance(tool_response, dict) else True\nerror = tool_response.get('error', '') if isinstance(tool_response, dict) else ''\n\n# Log performance\nperf_file = Path(os.path.expanduser('~/.claude/skill-performance.jsonl'))\nperf_file.parent.mkdir(parents=True, exist_ok=True)\n\nlog_entry = {\n    'timestamp': datetime.utcnow().isoformat(),\n    'tool': tool_name,\n    'success': success,\n    'error': error[:100] if error else None\n}\n\nwith open(perf_file, 'a') as f:\n    f.write(json.dumps(log_entry) + '\\n')\n\nif success:\n    print(f'✅ {tool_name} completed successfully', file=sys.stderr)\nelse:\n    print(f'❌ {tool_name} failed: {error[:50]}', file=sys.stderr)\n\nsys.exit(0)\n\"",\n            \"timeout\": 5\n          }\n        ]\n      }\n    ]\n  }\n}\n```\n\n## BashOutput Hooks\n\nThe BashOutput tool retrieves output from background commands. Use hooks to monitor long-running processes.\n\n### PostToolUse: Track Long-Running Operations\n\n```json\n{\n  \"hooks\": {\n    \"PostToolUse\": [\n      {\n        \"matcher\": \"BashOutput\",\n        \"hooks\": [\n          {\n            \"type\": \"command\",\n            \"command\": \"bash -c '\ninput=$(cat)\nbash_id=$(echo \"$input\" | jq -r \".tool_input.bash_id // empty\")\n\nif [ -z \"$bash_id\" ]; then\n    exit 0\nfi\n\n# Log bash output retrieval\naudit_log=\"${HOME}/.claude/bash-output.log\"\nlog_entry=$(printf \"[%s] bash_id=%s\\\\n\" \"$(date +%Y-%m-%d\\ %H:%M:%S)\" \"$bash_id\")\necho \"$log_entry\" >> \"$audit_log\"\n\necho \"🔍 Background process output retrieved\" >&2\nexit 0'",\n            \"timeout\": 5\n          }\n        ]\n      }\n    ]\n  }\n}\n```\n\n## Environment-Aware Hooks (CLAUDE_CODE_REMOTE)\n\nDetect and handle differences between Claude Code web interface and CLI environments.\n\n### Detecting Environment\n\nThe `CLAUDE_CODE_REMOTE` environment variable indicates the execution context:\n- **Not set**: Local CLI execution\n- **Set to \"true\"**: Web interface (claude.ai/code)\n\n### PreToolUse: Environment-Specific Behavior\n\n```json\n{\n  \"hooks\": {\n    \"PreToolUse\": [\n      {\n        \"matcher\": \".*\",\n        \"hooks\": [\n          {\n            \"type\": \"command\",\n            \"command\": \"python3 -c \"\nimport json, sys, os\n\ndata = json.load(sys.stdin)\ntool_name = data.get('tool_name', '')\n\n# Detect environment\nis_remote = os.getenv('CLAUDE_CODE_REMOTE', '').lower() == 'true'\n\nenvironment = 'Web Interface (claude.ai/code)' if is_remote else 'Local CLI'\n\n# Log environment-specific info\nlog_entry = {\n    'tool': tool_name,\n    'environment': environment,\n    'is_remote': is_remote\n}\n\nif is_remote:\n    # Web interface - limited file system access\n    if tool_name in ['Bash', 'Write', 'Edit']:\n        print(f'⚠️ Limited file access in web mode', file=sys.stderr)\nelse:\n    # Local CLI - full access\n    print(f'🖥️ Local CLI mode - full access', file=sys.stderr)\n\nsys.exit(0)\n\"",\n            \"timeout\": 5\n          }\n        ]\n      }\n    ]\n  }\n}\n```\n\n### PostToolUse: Environment-Specific Notifications\n\n```json\n{\n  \"hooks\": {\n    \"PostToolUse\": [\n      {\n        \"matcher\": \".*\",\n        \"hooks\": [\n          {\n            \"type\": \"command\",\n            \"command\": \"bash -c '\nif [ \"${CLAUDE_CODE_REMOTE:-}\" = \"true\" ]; then\n    # Web interface - use print-friendly format\n    input=$(cat)\n    echo \"Result (Web Mode):\" >&2\n    echo \"$input\" | jq . >&2\nelse\n    # Local CLI - can use external notifications\n    input=$(cat)\n    \n    # Check if we can send desktop notifications\n    if command -v notify-send &> /dev/null; then\n        notify-send \"Claude Code\" \"Operation completed\"\n    fi\nfi\n\nexit 0'",\n            \"timeout\": 5\n          }\n        ]\n      }\n    ]\n  }\n}\n```\n\n### Example: File Operations with Environment Detection\n\n```json\n{\n  \"hooks\": {\n    \"PostToolUse\": [\n      {\n        \"matcher\": \"Write|Edit\",\n        \"hooks\": [\n          {\n            \"type\": \"command\",\n            \"command\": \"python3 -c \"\nimport os, json, sys\n\ndata = json.load(sys.stdin)\nfile_path = data.get('tool_input', {}).get('file_path', '')\n\nis_remote = os.getenv('CLAUDE_CODE_REMOTE', '').lower() == 'true'\n\nif is_remote:\n    # Web interface\n    print(f'✅ File updated in web editor: {file_path}', file=sys.stderr)\n    # Cannot trigger external tools or file operations\nelse:\n    # Local CLI - can do more\n    print(f'✅ File written: {file_path}', file=sys.stderr)\n    \n    # Can trigger git operations\n    if 'git' in os.getenv('PATH', ''):\n        print('💡 Consider: git add && git commit', file=sys.stderr)\n\nsys.exit(0)\n\"",\n            \"timeout\": 5\n          }\n        ]\n      }\n    ]\n  }\n}\n```\n\n## Cross-Tool Integration\n\n### Example: Search → Memory → GitHub Workflow\n\nIntegrate WebSearch, Memory server, and GitHub server:\n\n```json\n{\n  \"hooks\": {\n    \"PostToolUse\": [\n      {\n        \"matcher\": \"mcp__brave_search__brave_web_search\",\n        \"hooks\": [\n          {\n            \"type\": \"command\",\n            \"command\": \"python3 << 'HOOK_EOF'\nimport json, sys\n\ndata = json.load(sys.stdin)\nquery = data.get('tool_input', {}).get('query', '')\nresults = data.get('tool_response', {}).get('results', [])\n\nif not results:\n    sys.exit(0)\n\n# Extract key information from top results\ntop_result = results[0] if results else {}\n\n# Would send to memory server for future context\nmemory_entity = {\n    'entities': [{\n        'name': f'Search Result: {query[:50]}',\n        'entity_type': 'research',\n        'observations': [\n            f'Title: {top_result.get(\"title\", \"\")}',\n            f'URL: {top_result.get(\"url\", \"\")}',\n            f'Total results: {len(results)}'\n        ]\n    }]\n}\n\nprint('💡 Research saved to memory for future reference', file=sys.stderr)\nprint(json.dumps(memory_entity), file=sys.stderr)\n\nsys.exit(0)\nHOOK_EOF\",\n            \"timeout\": 10\n          }\n        ]\n      }\n    ]\n  }\n}\n```\n\n### Example: Notebook → GitHub PR Workflow\n\nAutomatically create GitHub issues from notebook analysis:\n\n```json\n{\n  \"hooks\": {\n    \"PostToolUse\": [\n      {\n        \"matcher\": \"NotebookEdit\",\n        \"hooks\": [\n          {\n            \"type\": \"command\",\n            \"command\": \"python3 << 'HOOK_EOF'\nimport json, sys, re\n\ndata = json.load(sys.stdin)\nnotebook_path = data.get('tool_input', {}).get('notebook_path', '')\nnew_source = data.get('tool_input', {}).get('new_source', '')\n\n# Extract TODO/FIXME comments from cell\ntodos = re.findall(r'# (TODO|FIXME):\\s*(.+)', new_source)\n\nif not todos:\n    sys.exit(0)\n\nprint(f'Found {len(todos)} action items in notebook', file=sys.stderr)\n\nfor tag, description in todos:\n    # This would be sent to GitHub server to create issues\n    print(f'  [{tag}] {description}', file=sys.stderr)\n\nsys.exit(0)\nHOOK_EOF\",\n            \"timeout\": 5\n          }\n        ]\n      }\n    ]\n  }\n}\n```\n\n## Best Practices\n\n### Security Best Practices\n\n1. **Validate Environment Detection**:\n   ```bash\n   if [ \"${CLAUDE_CODE_REMOTE:-false}\" = \"true\" ]; then\n       # Web mode - restricted operations\n   else\n       # CLI mode - full access\n   fi\n   ```\n\n2. **Protect Sensitive Data in Logs**:\n   ```python\n   # Hash sensitive queries before logging\n   import hashlib\n   query_hash = hashlib.sha256(query.encode()).hexdigest()[:8]\n   log_entry = {'query_hash': query_hash}  # Don't log actual query\n   ```\n\n3. **Rate Limit External Operations**:\n   ```python\n   # Track and enforce limits\n   if operation_count > limit_per_minute:\n       print('Rate limit exceeded', file=sys.stderr)\n       sys.exit(2)  # Block\n   ```\n\n### Performance Best Practices\n\n1. **Use Fast Validation in PreToolUse**:\n   - Target timeout: 2-5 seconds\n   - Exit quickly on validation pass\n   - Block immediately on failure\n\n2. **Move Heavy Operations to Stop**:\n   ```json\n   {\n     \"hooks\": {\n       \"Stop\": [{\n         \"type\": \"command\",\n         \"command\": \"heavy-analysis.py\",\n         \"timeout\": 60\n       }]\n     }\n   }\n   ```\n\n3. **Cache Results When Possible**:\n   ```python\n   cache_file = Path(cache_dir) / f'{query_hash}.json'\n   if cache_file.exists() and not stale(cache_file):\n       return cached_result(cache_file)\n   ```\n\n### Debugging Best Practices\n\n1. **Log to Structured Formats**:\n   ```bash\n   # JSONL for easy parsing\n   echo '{\"timestamp\": \"'$(date -Iseconds)'\", \"event\": \"search\"}' >> audit.jsonl\n   ```\n\n2. **Use Consistent Emoji Indicators**:\n   - ✅ Success\n   - ❌ Error/Block\n   - ⚠️ Warning\n   - 📊 Info/Stats\n   - 🔍 Debug\n\n3. **Enable Debug Mode for Testing**:\n   ```bash\n   # Run Claude Code with debug\n   claude --debug\n   \n   # Inspect hook output\n   tail -f ~/.claude/hook-debug.log\n   ```\n\n### Configuration Best Practices\n\n1. **Use Environment Variables**:\n   ```json\n   {\n     \"command\": \"$CLAUDE_PROJECT_DIR/.claude/hooks/validate.py\",\n     \"timeout\": 10\n   }\n   ```\n\n2. **Document Hook Purpose**:\n   ```json\n   {\n     \"matcher\": \"NotebookEdit\",\n     \"description\": \"Validates notebook cells before execution\",\n     \"hooks\": [{\"type\": \"command\", \"command\": \"validate-notebook.py\"}]\n   }\n   ```\n\n3. **Test Before Deployment**:\n   ```bash\n   # Test with sample input\n   cat test-input.json | python3 my-hook.py\n   \n   # Check exit code\n   echo $?\n   ```\n\n## See Also\n\n- [MCP Integration Patterns](../examples/mcp-integration.md) - MCP tool hooking\n- [Security Templates](security.md) - Security-focused examples\n- [Code Quality Templates](code-quality.md) - Testing and formatting\n- [Hook Creation Reference](../REFERENCE.md) - Complete API reference\n