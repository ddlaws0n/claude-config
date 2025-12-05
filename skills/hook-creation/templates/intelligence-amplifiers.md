# Intelligence Amplifiers: Beyond Code Quality

Templates for hooks that expand Claude's capabilities beyond traditional code quality. These examples show how hooks can make Claude smarter, more aware, and more productive through context injection, analytics, learning, and intelligent automation.

> **Philosophy**: Code quality hooks enforce standards. Intelligence amplifiers help Claude *think better*. They inject context, build knowledge graphs, track patterns, and automate discovery.

---

## 1. Session Analytics & Insights

Transform raw activity into actionable insights. Track patterns, identify bottlenecks, and learn from your coding behavior.

### PostToolUse: Real-Time Session Intelligence

Track which tools you use most, how long tasks take, and identify productivity patterns in real-time.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, os, time\nfrom datetime import datetime\nfrom pathlib import Path\nfrom collections import defaultdict\n\n# Initialize analytics\nanalytics_dir = os.path.expanduser('~/.claude/analytics')\nos.makedirs(analytics_dir, exist_ok=True)\n\ndata = json.load(sys.stdin)\ntool_name = data.get('tool_name', '')\ntimestamp = datetime.now()\nsession_id = os.getenv('CLAUDE_SESSION_ID', 'unknown')\n\n# Load session analytics\nsession_file = os.path.join(analytics_dir, f'{session_id}.json')\n\ntry:\n    with open(session_file, 'r') as f:\n        session = json.load(f)\nexcept:\n    session = {\n        'start_time': timestamp.isoformat(),\n        'tools': defaultdict(int),\n        'file_edits': defaultdict(int),\n        'languages': defaultdict(int),\n        'tool_times': defaultdict(float),\n        'last_tools': [],\n        'operations_count': 0\n    }\n\n# Track tool usage\nsession['tools'][tool_name] = session['tools'].get(tool_name, 0) + 1\nsession['last_tools'].append({'tool': tool_name, 'time': timestamp.isoformat()})\nsession['last_tools'] = session['last_tools'][-10:]  # Keep last 10\nsession['operations_count'] = session['operations_count'] + 1\n\n# Track file edits and language usage\nif tool_name in ['Write', 'Edit']:\n    file_path = data.get('tool_input', {}).get('file_path', '')\n    if file_path:\n        filename = os.path.basename(file_path)\n        session['file_edits'][filename] = session['file_edits'].get(filename, 0) + 1\n        \n        ext = Path(file_path).suffix.lower()\n        if ext:\n            session['languages'][ext] = session['languages'].get(ext, 0) + 1\n\n# Calculate session duration\nstart = datetime.fromisoformat(session['start_time'])\nelapsed = (timestamp - start).total_seconds() / 60\n\n# Detect productivity patterns\nop_count = session['operations_count']\nops_per_minute = op_count / max(elapsed, 1)\n\ninsights = []\nif ops_per_minute > 5:\n    insights.append('🚀 High velocity session')\nif len(set(session['tools'].keys())) > 5:\n    insights.append('🔄 Diverse tool usage')\nif session['languages']:\n    top_lang = max(session['languages'].items(), key=lambda x: x[1])[0]\n    insights.append(f'📝 Focus: {top_lang}')\n\n# Print insights every 10 operations\nif op_count % 10 == 0:\n    print(f'📊 Session: {int(elapsed)}m, {op_count} ops @ {ops_per_minute:.1f} ops/min', file=sys.stderr)\n    for insight in insights:\n        print(f'  {insight}', file=sys.stderr)\n\n# Convert defaultdicts to dicts for JSON serialization\nsession_serializable = {\n    k: dict(v) if isinstance(v, defaultdict) else v \n    for k, v in session.items()\n}\n\nwith open(session_file, 'w') as f:\n    json.dump(session_serializable, f, indent=2)\n\nsys.exit(0)\n\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### Stop: Session Intelligence Report

Generate a comprehensive report of your session with actionable insights and trends.

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, os\nfrom datetime import datetime\nfrom pathlib import Path\n\nanalytics_dir = os.path.expanduser('~/.claude/analytics')\nsession_id = os.getenv('CLAUDE_SESSION_ID', 'unknown')\nsession_file = os.path.join(analytics_dir, f'{session_id}.json')\n\nif not os.path.exists(session_file):\n    sys.exit(0)\n\nwith open(session_file, 'r') as f:\n    session = json.load(f)\n\nstart = datetime.fromisoformat(session['start_time'])\nelapsed = (datetime.now() - start).total_seconds() / 60\n\nprint('\\n📈 SESSION INTELLIGENCE REPORT', file=sys.stderr)\nprint('=' * 50, file=sys.stderr)\n\nprint(f'\\n⏱️ Duration: {int(elapsed)} minutes', file=sys.stderr)\nprint(f'📊 Total Operations: {session[\\\"operations_count\\\"]}', file=sys.stderr)\nif elapsed > 0:\n    print(f'⚡ Velocity: {session[\\\"operations_count\\\"]/elapsed:.1f} ops/min', file=sys.stderr)\n\nif session['tools']:\n    print(f'\\n🔧 Tools Used (Top 5):', file=sys.stderr)\n    sorted_tools = sorted(session['tools'].items(), key=lambda x: x[1], reverse=True)\n    for tool, count in sorted_tools[:5]:\n        print(f'  {tool}: {count}', file=sys.stderr)\n\nif session['languages']:\n    print(f'\\n📝 Languages Edited:', file=sys.stderr)\n    sorted_langs = sorted(session['languages'].items(), key=lambda x: x[1], reverse=True)\n    for lang, count in sorted_langs:\n        print(f'  {lang}: {count} files', file=sys.stderr)\n\nif session['file_edits']:\n    print(f'\\n🎯 Most Edited Files:', file=sys.stderr)\n    sorted_files = sorted(session['file_edits'].items(), key=lambda x: x[1], reverse=True)[:5]\n    for filename, count in sorted_files:\n        print(f'  {filename}: {count} edits', file=sys.stderr)\n\n# Cleanup\nos.remove(session_file)\n\nprint('\\n✅ Report complete', file=sys.stderr)\nsys.exit(0)\n\"",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

### Historical Trend Analysis

Track productivity metrics over time and identify your peak coding windows.

```json
{
  "hooks": {
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, os\nfrom datetime import datetime, timedelta\nfrom pathlib import Path\n\nmetrics_dir = os.path.expanduser('~/.claude/metrics')\nos.makedirs(metrics_dir, exist_ok=True)\n\n# Get session analytics\nanalytics_dir = os.path.expanduser('~/.claude/analytics')\nsession_id = os.getenv('CLAUDE_SESSION_ID', 'unknown')\nsession_file = os.path.join(analytics_dir, f'{session_id}.json')\n\nif not os.path.exists(session_file):\n    sys.exit(0)\n\nwith open(session_file, 'r') as f:\n    session = json.load(f)\n\n# Create daily summary\ntoday = datetime.now().strftime('%Y-%m-%d')\nmetrics_file = os.path.join(metrics_dir, 'trends.json')\n\ntry:\n    with open(metrics_file, 'r') as f:\n        trends = json.load(f)\nexcept:\n    trends = {'daily': {}, 'weekly': {}}\n\n# Store today's metrics\nstart = datetime.fromisoformat(session['start_time'])\nelapsed = (datetime.now() - start).total_seconds() / 60\n\ntrends['daily'][today] = {\n    'duration_minutes': int(elapsed),\n    'operations': session['operations_count'],\n    'velocity': session['operations_count'] / max(elapsed, 1),\n    'top_language': max(session['languages'].items(), key=lambda x: x[1])[0] if session['languages'] else None,\n    'files_modified': len(session['file_edits']),\n    'timestamp': datetime.now().isoformat()\n}\n\n# Keep only last 30 days\nkeep_days = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')\ndaily_copy = {k: v for k, v in trends['daily'].items() if k >= keep_days}\ntrends['daily'] = daily_copy\n\nwith open(metrics_file, 'w') as f:\n    json.dump(trends, f, indent=2)\n\n# Print weekly summary\nprint(f'📅 Weekly Productivity:', file=sys.stderr)\nweek_ago = datetime.now() - timedelta(days=7)\nweek_stats = {\n    'days': 0,\n    'total_ops': 0,\n    'total_minutes': 0,\n    'avg_velocity': 0\n}\n\nfor day_str, metrics in trends['daily'].items():\n    day_date = datetime.strptime(day_str, '%Y-%m-%d')\n    if day_date >= week_ago:\n        week_stats['days'] += 1\n        week_stats['total_ops'] += metrics['operations']\n        week_stats['total_minutes'] += metrics['duration_minutes']\n\nif week_stats['days'] > 0:\n    week_stats['avg_velocity'] = week_stats['total_ops'] / max(week_stats['total_minutes'], 1)\n    print(f'  Days active: {week_stats[\\\"days\\\"]}', file=sys.stderr)\n    print(f'  Total ops: {week_stats[\\\"total_ops\\\"]}', file=sys.stderr)\n    print(f'  Avg velocity: {week_stats[\\\"avg_velocity\\\"]:.1f} ops/min', file=sys.stderr)\n\nsys.exit(0)\n\"",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

### API Cost Tracking

Monitor your Claude API usage and estimate costs in real-time.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, os\nfrom datetime import datetime\n\n# Pricing (adjust for your plan)\npricing = {\n    'claude-opus-4-5': {'input': 0.015, 'output': 0.06},  # per 1K tokens\n    'claude-sonnet': {'input': 0.003, 'output': 0.015},\n    'claude-haiku': {'input': 0.0008, 'output': 0.004}\n}\n\ndata = json.load(sys.stdin)\ncost_dir = os.path.expanduser('~/.claude/costs')\nos.makedirs(cost_dir, exist_ok=True)\n\n# Extract token usage from response if available\nresponse = data.get('tool_response', {})\nmodel = os.getenv('CLAUDE_MODEL', 'claude-opus-4-5')\n\n# Estimate based on tool usage (conservative estimate)\ntool_name = data.get('tool_name', '')\nestimated_tokens = {\n    'Read': 500,    # Approximate tokens for file reads\n    'Write': 1000,  # Content size + context\n    'Edit': 800,\n    'Bash': 300,\n    'Grep': 400\n}\n\nif model in pricing and tool_name in estimated_tokens:\n    input_tokens = estimated_tokens.get(tool_name, 0)\n    output_tokens = int(input_tokens * 0.5)  # Estimate output\n    \n    rates = pricing.get(model, pricing['claude-opus-4-5'])\n    estimated_cost = (\n        (input_tokens / 1000) * rates['input'] +\n        (output_tokens / 1000) * rates['output']\n    )\n    \n    # Track cost\n    today = datetime.now().strftime('%Y-%m-%d')\n    cost_file = os.path.join(cost_dir, f'costs-{today}.json')\n    \n    try:\n        with open(cost_file, 'r') as f:\n            daily_costs = json.load(f)\n    except:\n        daily_costs = {'total': 0.0, 'operations': 0, 'by_tool': {}}\n    \n    daily_costs['total'] += estimated_cost\n    daily_costs['operations'] += 1\n    if tool_name not in daily_costs['by_tool']:\n        daily_costs['by_tool'][tool_name] = {'count': 0, 'cost': 0.0}\n    daily_costs['by_tool'][tool_name]['count'] += 1\n    daily_costs['by_tool'][tool_name]['cost'] += estimated_cost\n    \n    with open(cost_file, 'w') as f:\n        json.dump(daily_costs, f, indent=2)\n    \n    # Alert if daily cost exceeds threshold\n    if daily_costs['total'] > 1.0:  # $1 threshold\n        print(f'💰 Daily cost: ${daily_costs[\\\"total\\\"]:.2f}', file=sys.stderr)\n\nsys.exit(0)\n\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

---

## 2. Knowledge Graph & Context Building

Build semantic understanding of your codebase. Track relationships, dependencies, and patterns.

### PostToolUse: Symbol Index Builder

Maintain a real-time index of functions, classes, imports, and exports across your codebase.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, os, re\nfrom pathlib import Path\n\ndata = json.load(sys.stdin)\nfile_path = data.get('tool_input', {}).get('file_path', '')\n\nif not file_path or not os.path.exists(file_path):\n    sys.exit(0)\n\n# Initialize symbol index\nindex_dir = os.path.expanduser('~/.claude/symbol-index')\nos.makedirs(index_dir, exist_ok=True)\nindex_file = os.path.join(index_dir, 'index.json')\n\ntry:\n    with open(index_file, 'r') as f:\n        index = json.load(f)\nexcept:\n    index = {'symbols': {}, 'imports': {}, 'exports': {}, 'files': {}}\n\n# Read file and extract symbols\nwith open(file_path, 'r', encoding='utf-8', errors='ignore') as f:\n    content = f.read()\n\nfile_symbols = {'functions': [], 'classes': [], 'imports': [], 'exports': []}\nreg_extensions = ['.py', '.ts', '.js', '.tsx', '.jsx']\n\nif any(file_path.endswith(ext) for ext in reg_extensions):\n    is_python = file_path.endswith('.py')\n    \n    # Extract function definitions\n    if is_python:\n        pattern = r'^def\\s+(\\w+)\\s*\\('\n    else:\n        pattern = r'(?:function|const|async)\\s+(\\w+)\\s*(?:\\(|=)'\n    \n    for match in re.finditer(pattern, content, re.MULTILINE):\n        file_symbols['functions'].append(match.group(1))\n    \n    # Extract class definitions\n    if is_python:\n        pattern = r'^class\\s+(\\w+)'\n    else:\n        pattern = r'(?:class|interface|type)\\s+(\\w+)'\n    \n    for match in re.finditer(pattern, content, re.MULTILINE):\n        file_symbols['classes'].append(match.group(1))\n    \n    # Extract imports\n    if is_python:\n        pattern = r'(?:from\\s+[\\w.]+\\s+)?import\\s+([\\w, ]+)'\n    else:\n        pattern = r'(?:import|from)\\s+[\\w./]+\\s+(?:import\\s+)?([\\w, {}*]+)'\n    \n    for match in re.finditer(pattern, content):\n        imports = match.group(1).split(',')\n        file_symbols['imports'].extend([imp.strip() for imp in imports])\n\n# Update index\nindex['files'][file_path] = {\n    'symbols': file_symbols,\n    'updated': datetime.now().isoformat()\n}\n\n# Aggregate symbols\nfor symbol_type in ['functions', 'classes']:\n    for symbol in file_symbols[symbol_type]:\n        if symbol not in index['symbols']:\n            index['symbols'][symbol] = []\n        if file_path not in index['symbols'][symbol]:\n            index['symbols'][symbol].append(file_path)\n\nwith open(index_file, 'w') as f:\n    json.dump(index, f, indent=2)\n\nprint(f'🔍 Indexed {len(file_symbols[\\\"functions\\\"])} functions, {len(file_symbols[\\\"classes\\\"])} classes', file=sys.stderr)\n\nsys.exit(0)\n\"",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

### Codebase Relationship Mapper

Build a graph of file dependencies and relationships.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, os, re\nfrom pathlib import Path\nfrom datetime import datetime\n\ndata = json.load(sys.stdin)\nfile_path = data.get('tool_input', {}).get('file_path', '')\n\nif not file_path or not os.path.exists(file_path):\n    sys.exit(0)\n\n# Initialize relationship graph\ngraph_dir = os.path.expanduser('~/.claude/relationships')\nos.makedirs(graph_dir, exist_ok=True)\ngraph_file = os.path.join(graph_dir, 'graph.json')\n\ntry:\n    with open(graph_file, 'r') as f:\n        graph = json.load(f)\nexcept:\n    graph = {'files': {}, 'imports': {}, 'changes': []}\n\n# Read file and extract imports/dependencies\nwith open(file_path, 'r', encoding='utf-8', errors='ignore') as f:\n    lines = f.readlines()\n\ndependencies = {'imports': [], 'imports_from': {}}\n\n# Python imports\nfor line in lines:\n    if line.strip().startswith(('import ', 'from ')):\n        # Extract module name\n        match = re.search(r'(?:from|import)\\s+([\\w./-]+)', line)\n        if match:\n            module = match.group(1)\n            dependencies['imports'].append(module)\n            \n            # Track from-imports separately\n            if 'from' in line:\n                match_from = re.search(r'from\\s+([\\w./-]+)\\s+import\\s+(.+)', line)\n                if match_from:\n                    module, items = match_from.groups()\n                    if module not in dependencies['imports_from']:\n                        dependencies['imports_from'][module] = []\n                    dependencies['imports_from'][module].extend(\n                        [item.strip() for item in items.split(',')]\n                    )\n\n# Update graph\nif file_path not in graph['files']:\n    graph['files'][file_path] = {'imports': [], 'imported_by': [], 'last_change': None}\n\ngraph['files'][file_path]['imports'] = dependencies['imports']\ngraph['files'][file_path]['last_change'] = datetime.now().isoformat()\n\n# Log change for impact analysis\ngraph['changes'].append({\n    'file': file_path,\n    'timestamp': datetime.now().isoformat(),\n    'new_imports': dependencies['imports']\n})\n\n# Keep only recent changes (last 100)\nif len(graph['changes']) > 100:\n    graph['changes'] = graph['changes'][-100:]\n\nwith open(graph_file, 'w') as f:\n    json.dump(graph, f, indent=2)\n\nprint(f'📊 Updated relationships: {len(dependencies[\\\"imports\\\"])} imports tracked', file=sys.stderr)\n\nsys.exit(0)\n\"",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

### Change Impact Analysis

Predict which files might be affected by your changes.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, os\nfrom pathlib import Path\n\ndata = json.load(sys.stdin)\nfile_path = data.get('tool_input', {}).get('file_path', '')\n\nif not file_path:\n    sys.exit(0)\n\n# Load relationship graph\ngraph_dir = os.path.expanduser('~/.claude/relationships')\ngraph_file = os.path.join(graph_dir, 'graph.json')\n\nif not os.path.exists(graph_file):\n    sys.exit(0)\n\nwith open(graph_file, 'r') as f:\n    graph = json.load(f)\n\n# Extract module name from file path\nmodule_name = os.path.basename(file_path).replace('.py', '')\n\n# Find files that import this file\nimpacted = []\nfor file, meta in graph['files'].items():\n    for imp in meta.get('imports', []):\n        if module_name in imp or file_path in imp:\n            impacted.append(file)\n\nif impacted and len(impacted) <= 10:\n    print(f'⚠️ Impact analysis: {len(impacted)} files may be affected', file=sys.stderr)\n    for file in impacted[:5]:\n        print(f'  • {os.path.basename(file)}', file=sys.stderr)\n    if len(impacted) > 5:\n        print(f'  ... and {len(impacted) - 5} more', file=sys.stderr)\nelif len(impacted) > 10:\n    print(f'🔴 High impact: {len(impacted)} files may be affected', file=sys.stderr)\n    print('  Consider running tests to verify changes', file=sys.stderr)\n\nsys.exit(0)\n\"",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

---

## 3. Intelligent Assistance

Make Claude smarter by providing just-in-time context and suggestions.

### PostToolUse: API Documentation Auto-Fetcher

When you import a new library, automatically fetch and index its documentation.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, os, re, subprocess\nfrom pathlib import Path\n\ndata = json.load(sys.stdin)\nfile_path = data.get('tool_input', {}).get('file_path', '')\n\nif not file_path or not file_path.endswith('.py'):\n    sys.exit(0)\n\n# Extract new imports\nwith open(file_path, 'r', errors='ignore') as f:\n    content = f.read()\n\npattern = r'(?:from|import)\\s+([\\w.]+)'\nnew_imports = [match.group(1) for match in re.finditer(pattern, content)]\n\n# Common packages with good documentation\ndocs_available = {\n    'fastapi': 'https://fastapi.tiangolo.com/',\n    'django': 'https://docs.djangoproject.com/',\n    'requests': 'https://requests.readthedocs.io/',\n    'numpy': 'https://numpy.org/doc/',\n    'pandas': 'https://pandas.pydata.org/docs/',\n    'sqlalchemy': 'https://docs.sqlalchemy.org/',\n    'pydantic': 'https://docs.pydantic.dev/',\n    'pytest': 'https://docs.pytest.org/',\n    'click': 'https://click.palletsprojects.com/'\n}\n\n# Check for new library imports\nfor imp in new_imports:\n    base_package = imp.split('.')[0]\n    if base_package in docs_available and not imp.startswith('_'):\n        # Store for context injection\n        docs_dir = os.path.expanduser('~/.claude/library-docs')\n        os.makedirs(docs_dir, exist_ok=True)\n        \n        doc_file = os.path.join(docs_dir, f'{base_package}.txt')\n        if not os.path.exists(doc_file):\n            print(f'📚 Found {base_package}, docs: {docs_available[base_package]}', file=sys.stderr)\n            print(f'  💡 Reference these docs when working with {base_package}', file=sys.stderr)\n\nsys.exit(0)\n\"",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

### Similar Code Pattern Detector

Find and suggest similar implementations in your codebase.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, os, re\nfrom pathlib import Path\nfrom difflib import SequenceMatcher\n\ndata = json.load(sys.stdin)\nfile_path = data.get('tool_input', {}).get('file_path', '')\nnew_content = data.get('tool_input', {}).get('content', '')\n\nif not file_path or not new_content or len(new_content) < 100:\n    sys.exit(0)\n\n# Extract function definitions from new content\nfunctions = re.findall(r'def\\s+(\\w+).*?(?=def|class|$)', new_content, re.DOTALL)\n\nif not functions:\n    sys.exit(0)\n\n# Search for similar patterns in codebase\nsimilar_count = 0\nproject_root = os.path.dirname(file_path)\n\nfor py_file in Path(project_root).rglob('*.py'):\n    if py_file == Path(file_path):\n        continue\n    \n    try:\n        with open(py_file, 'r', errors='ignore') as f:\n            existing = f.read()\n    except:\n        continue\n    \n    # Calculate similarity\n    for func in functions:\n        if func in existing:\n            # Found similar implementation\n            matcher = SequenceMatcher(None, new_content, existing)\n            similarity = matcher.ratio()\n            \n            if similarity > 0.7 and similar_count < 3:\n                print(f'🔄 Similar code found in {py_file.name}', file=sys.stderr)\n                similar_count += 1\n\nif similar_count > 0:\n    print(f'  💡 Consider refactoring to reduce duplication', file=sys.stderr)\n\nsys.exit(0)\n\"",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

### Error Pattern Recognition

Learn from past errors and suggest fixes for similar issues.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, os\nfrom datetime import datetime\nfrom pathlib import Path\n\ndata = json.load(sys.stdin)\nresponse = data.get('tool_response', {})\ncommand = data.get('tool_input', {}).get('command', '')\n\n# Check if command had errors\nif response.get('success', True):\n    sys.exit(0)\n\nerror_log_dir = os.path.expanduser('~/.claude/error-patterns')\nos.makedirs(error_log_dir, exist_ok=True)\n\nerror_patterns_file = os.path.join(error_log_dir, 'patterns.json')\n\ntry:\n    with open(error_patterns_file, 'r') as f:\n        patterns = json.load(f)\nexcept:\n    patterns = {}\n\n# Extract error type\nerror_output = response.get('stderr', '') or response.get('stdout', '')\nerror_type = 'unknown'\n\nif 'TypeError' in error_output:\n    error_type = 'TypeError'\nelif 'AttributeError' in error_output:\n    error_type = 'AttributeError'\nelif 'ImportError' in error_output:\n    error_type = 'ImportError'\nelif 'not found' in error_output.lower():\n    error_type = 'NotFound'\nelif 'permission denied' in error_output.lower():\n    error_type = 'PermissionDenied'\n\n# Track pattern\nif error_type not in patterns:\n    patterns[error_type] = {'count': 0, 'last_seen': None, 'commands': []}\n\npatterns[error_type]['count'] += 1\npatterns[error_type]['last_seen'] = datetime.now().isoformat()\nif command not in patterns[error_type]['commands']:\n    patterns[error_type]['commands'].append(command)\n\nwith open(error_patterns_file, 'w') as f:\n    json.dump(patterns, f, indent=2)\n\n# Suggest fix if this is a repeat error\nif patterns[error_type]['count'] > 1:\n    print(f'⚠️ Repeat error: {error_type}', file=sys.stderr)\n    print(f'  This error occurred {patterns[error_type][\\\"count\\\"]} times', file=sys.stderr)\n    print(f'  💡 Consider documenting the fix', file=sys.stderr)\n\nsys.exit(0)\n\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

---

## 4. Team Collaboration

Share knowledge and maintain consistency across teams.

### PostToolUse: Code Review Flags

Automatically flag common issues before PR review.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, os, re\nfrom pathlib import Path\n\ndata = json.load(sys.stdin)\nfile_path = data.get('tool_input', {}).get('file_path', '')\nnew_content = data.get('tool_input', {}).get('content', '')\n\nif not file_path:\n    sys.exit(0)\n\nflags = []\n\n# Check for common code review issues\nif 'TODO' in new_content or 'FIXME' in new_content:\n    count = new_content.count('TODO') + new_content.count('FIXME')\n    flags.append(f'📝 {count} TODO/FIXME comments')\n\nif re.search(r'print\\(', new_content) and file_path.endswith('.py'):\n    count = len(re.findall(r'print\\(', new_content))\n    flags.append(f'🖨️  {count} print statements (use logging)')\n\nif 'import *' in new_content:\n    flags.append('⚠️ Wildcard imports detected')\n\nif re.search(r'except\\s*:', new_content):\n    flags.append('⚠️ Bare except clause detected')\n\nif len(new_content) > 1000 and file_path.endswith('.py'):\n    flags.append('📏 Large function/file (consider splitting)')\n\nif not re.search(r'\\\"\\\"\\"|\\'\\'\\'\\'', new_content) and file_path.endswith('.py'):\n    flags.append('📚 Missing docstring')\n\nif flags:\n    print(f'🚩 Code review flags ({len(flags)}):', file=sys.stderr)\n    for flag in flags:\n        print(f'  {flag}', file=sys.stderr)\n\nsys.exit(0)\n\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### Onboarding Context Generator

Provide new team members with codebase overview automatically.

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, os\nfrom pathlib import Path\n\n# Check if this is a new session (first hook run)\nproject_dir = os.getcwd()\ncontext_dir = os.path.expanduser('~/.claude/project-context')\nos.makedirs(context_dir, exist_ok=True)\n\nproject_id = project_dir.replace('/', '_')\ncontext_file = os.path.join(context_dir, f'{project_id}.json')\n\n# If context doesn't exist, generate it\nif not os.path.exists(context_file):\n    # Analyze project structure\n    context = {\n        'project_root': project_dir,\n        'structure': {},\n        'key_files': [],\n        'languages': set(),\n        'dependencies': []\n    }\n    \n    # Analyze directory structure\n    try:\n        for root, dirs, files in os.walk(project_dir):\n            # Skip hidden and common non-essential directories\n            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', '.venv']]\n            \n            rel_path = os.path.relpath(root, project_dir)\n            if rel_path != '.':\n                level = rel_path.count(os.sep)\n                if level < 3:  # Only show 3 levels deep\n                    context['structure'][rel_path] = len(files)\n            \n            # Track key files\n            for file in files[:10]:  # Sample first 10 files\n                ext = Path(file).suffix\n                if ext:\n                    context['languages'].add(ext)\n                \n                if file in ['README.md', 'setup.py', 'package.json', 'tsconfig.json']:\n                    context['key_files'].append(file)\n    except:\n        pass\n    \n    # Convert set to list for JSON\n    context['languages'] = list(context['languages'])\n    \n    with open(context_file, 'w') as f:\n        json.dump(context, f, indent=2)\n    \n    print(f'👋 New project context generated', file=sys.stderr)\n    print(f'  Languages: {\\\", \\\".join(context[\\\"languages\\\"])}', file=sys.stderr)\n    print(f'  Key files identified', file=sys.stderr)\n\nsys.exit(0)\n\"",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

---

## 5. Advanced Context Injection Patterns

### Stop: Smart Context Aggregator

Compile relevant context at session end for better future interactions.

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, os\nfrom datetime import datetime\nfrom pathlib import Path\n\n# Gather all session intelligence\nanalytics_dir = os.path.expanduser('~/.claude/analytics')\ncontext_dir = os.path.expanduser('~/.claude/session-context')\nos.makedirs(context_dir, exist_ok=True)\n\nsession_id = os.getenv('CLAUDE_SESSION_ID', 'unknown')\n\n# Compile context summary\ncontext = {\n    'timestamp': datetime.now().isoformat(),\n    'project': os.getcwd(),\n    'session_id': session_id,\n    'summary': {\n        'files_modified': [],\n        'key_changes': [],\n        'recommendations': []\n    }\n}\n\n# Load session metrics if available\nsession_file = os.path.join(analytics_dir, f'{session_id}.json')\nif os.path.exists(session_file):\n    with open(session_file, 'r') as f:\n        session = json.load(f)\n        \n    context['summary']['files_modified'] = list(session.get('file_edits', {}).keys())\n    \n    # Generate recommendations\n    if len(session.get('file_edits', {})) > 5:\n        context['summary']['recommendations'].append('Run tests to verify changes')\n    if session.get('operations_count', 0) > 50:\n        context['summary']['recommendations'].append('Consider git commit with summary')\n\n# Save for next session\nwith open(os.path.join(context_dir, f'session-{session_id}.json'), 'w') as f:\n    json.dump(context, f, indent=2)\n\nprint(f'📦 Session context saved for next session', file=sys.stderr)\n\nsys.exit(0)\n\"",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

---

## 6. Learning & Improvement

### PostToolUse: Pattern Learning System

Track what works and learn from successful patterns.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, os\nfrom datetime import datetime\n\ndata = json.load(sys.stdin)\nresponse = data.get('tool_response', {})\ntool_name = data.get('tool_name', '')\n\n# Only track successful operations\nif not response.get('success', True):\n    sys.exit(0)\n\nlearning_dir = os.path.expanduser('~/.claude/learning')\nos.makedirs(learning_dir, exist_ok=True)\n\npatterns_file = os.path.join(learning_dir, 'success-patterns.json')\n\ntry:\n    with open(patterns_file, 'r') as f:\n        patterns = json.load(f)\nexcept:\n    patterns = {'by_tool': {}, 'successful_workflows': []}\n\n# Track successful tool sequences\nif tool_name not in patterns['by_tool']:\n    patterns['by_tool'][tool_name] = {'success_count': 0, 'last_success': None}\n\npatterns['by_tool'][tool_name]['success_count'] += 1\npatterns['by_tool'][tool_name]['last_success'] = datetime.now().isoformat()\n\nwith open(patterns_file, 'w') as f:\n    json.dump(patterns, f, indent=2)\n\nsys.exit(0)\n\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

---

## 7. Novel Integration Patterns

### PostToolUse: Slack Team Sync

Notify team of progress on shared projects.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c '\ninput=$(cat)\nfile_path=$(echo \"$input\" | jq -r \".tool_input.file_path // empty\")\nproject=$(basename \"$(pwd)\")\n\nif [[ -z \"$SLACK_WEBHOOK_URL\" ]]; then\n    exit 0\nfi\n\n# Only notify for significant changes (don't spam)\nif [[ ! -f /tmp/claude-slack-rate-limit ]]; then\n    curl -X POST \"$SLACK_WEBHOOK_URL\" \\\n        -H \"Content-Type: application/json\" \\\n        -d \"{\n            \\\"blocks\\\": [\n                {\n                    \\\"type\\\": \\\"section\\\",\n                    \\\"text\\\": {\n                        \\\"type\\\": \\\"mrkdwn\\\",\n                        \\\"text\\\": \\\"🤖 Claude updated $(basename \\\"$file_path\\\") in *$project*\\\"\n                    }\n                }\n            ]\n        }\" \\\n        --silent --max-time 5 2>/dev/null || true\n    \n    # Rate limit: only one notification per 5 minutes\n    echo \"1\" > /tmp/claude-slack-rate-limit\n    sleep 300\n    rm -f /tmp/claude-slack-rate-limit &\nfi\n\nexit 0'",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

### Database Query Hook Pattern

Safe database access for codebase analysis.

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, os\nimport sqlite3\nfrom datetime import datetime\n\n# Create lightweight codebase index database\ndb_dir = os.path.expanduser('~/.claude/codebase-index')\nos.makedirs(db_dir, exist_ok=True)\ndb_path = os.path.join(db_dir, 'index.db')\n\nconn = sqlite3.connect(db_path)\ncursor = conn.cursor()\n\n# Create tables for codebase analysis\ntry:\n    cursor.execute('''CREATE TABLE IF NOT EXISTS files (\n        id INTEGER PRIMARY KEY,\n        path TEXT UNIQUE,\n        language TEXT,\n        size_bytes INTEGER,\n        last_modified TEXT,\n        functions INTEGER,\n        classes INTEGER\n    )''')\n    \n    cursor.execute('''CREATE TABLE IF NOT EXISTS symbols (\n        id INTEGER PRIMARY KEY,\n        file_id INTEGER,\n        name TEXT,\n        type TEXT,\n        line_number INTEGER,\n        FOREIGN KEY(file_id) REFERENCES files(id)\n    )''')\n    \n    cursor.execute('''CREATE TABLE IF NOT EXISTS imports (\n        id INTEGER PRIMARY KEY,\n        file_id INTEGER,\n        module TEXT,\n        FOREIGN KEY(file_id) REFERENCES files(id)\n    )''')\n    \n    conn.commit()\n    print(f'📊 Codebase index database ready', file=sys.stderr)\nexcept Exception as e:\n    print(f'Note: Database already initialized', file=sys.stderr)\n\nconn.close()\n\nsys.exit(0)\n\"",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

---

## Usage & Configuration

### Enable Intelligence Amplifiers

Add to `.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/session-intelligence.py",
            "timeout": 5
          },
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/symbol-indexer.py",
            "timeout": 10
          },
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/relationship-mapper.py",
            "timeout": 10
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/session-report.py",
            "timeout": 15
          },
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/context-aggregator.py",
            "timeout": 10
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/initialize-learning.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

### Environment Variables

Set these for enhanced integrations:

```bash
export CLAUDE_SESSION_ID=$(uuidgen)
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
export DISCORD_WEBHOOK_URL="https://discordapp.com/api/webhooks/..."
```

---

## The Power of Amplifiers

These templates transform Claude from a tool that executes commands into an intelligent assistant that:

- **Learns from patterns** in your codebase and development style
- **Understands context** deeply through symbol indexes and relationship graphs
- **Predicts impacts** of changes before you commit
- **Suggests improvements** based on historical patterns
- **Coordinates with teams** through intelligent notifications
- **Tracks metrics** to help you optimize your workflow

The key insight: **Hooks aren't just for code quality—they're your interface to make Claude smarter about YOUR codebase and YOUR development patterns.**
