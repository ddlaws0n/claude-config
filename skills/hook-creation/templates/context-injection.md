# Context Injection Hook Templates

Templates for UserPromptSubmit hooks that inject intelligent context into Claude's prompts. These hooks run when a user submits a prompt and can add contextual information by writing to stdout.

## Understanding Context Injection

### What It Is
UserPromptSubmit hooks can output text to stdout, which Claude automatically appends to the user's prompt as additional context. This allows you to dynamically inject relevant information based on:

- Current project state
- Git history and status
- Environment information
- Codebase statistics
- Active issues or TODOs
- Recent errors or logs
- Project-specific guidelines

### Why It Matters
- **Smarter Assistance**: Claude has real-time context about your project
- **Reduced Ambiguity**: No need to manually repeat project info
- **Consistency**: Project standards are always visible
- **Efficiency**: One-shot requests instead of clarification loops
- **Relevance**: Context-aware suggestions and code completions

### How It Works
1. User submits a prompt in Claude Code
2. UserPromptSubmit hook receives JSON input
3. Hook analyzes project and generates context
4. Hook writes context to stdout
5. Claude receives: `[user prompt]\n\n[injected context]`
6. Claude responds with full context awareness

### Performance Considerations
- Hooks run **before** Claude starts processing
- Keep execution under 2-3 seconds for responsive UX
- Cache expensive operations (git log, large scans)
- Use conditional logic to avoid unnecessary work

## Basic Template: Git Status Context

Inject current branch, uncommitted changes, and recent commits:

```bash
#!/bin/bash
# git-context.sh - Inject git context into prompts

input=$(cat)

# Only inject context if we're in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    exit 0
fi

# Extract prompt content to decide what context to include
prompt=$(echo "$input" | jq -r '.prompt // empty')

# Get current branch and status
branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
status=$(git status --short 2>/dev/null)
commit_count=$(git rev-list --count HEAD 2>/dev/null)

# Only inject if prompt mentions code/commit/git
if [[ "$prompt" =~ (code|commit|git|push|branch|change) ]]; then
    echo ""
    echo "## Git Context (Auto-injected)"
    echo "- **Current branch**: \`$branch\`"
    echo "- **Total commits**: $commit_count"

    if [[ -n "$status" ]]; then
        echo "- **Uncommitted changes**: Yes"
        echo "\`\`\`"
        echo "$status"
        echo "\`\`\`"
    else
        echo "- **Uncommitted changes**: None"
    fi

    # Show last 3 commits
    echo ""
    echo "### Recent Commits"
    echo "\`\`\`"
    git log --oneline -3 2>/dev/null || echo "No commits yet"
    echo "\`\`\`"
fi

exit 0
```

Configure in settings.json:
```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/git-context.sh",
            "timeout": 3
          }
        ]
      }
    ]
  }
}
```

## Active TODOs and Tasks Context

Inject all TODO/FIXME comments from codebase:

```python
#!/usr/bin/env python3
"""Inject active TODOs and FIXMEs into context"""
import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime

data = json.load(sys.stdin)
prompt = data.get('prompt', '').lower()

# Skip if prompt doesn't mention todos/tasks
if not any(word in prompt for word in ['todo', 'task', 'fixme', 'issues', 'bugs']):
    sys.exit(0)

try:
    # Find all TODO comments using grep
    result = subprocess.run(
        ['grep', '-r', '-n', '--include=*.py', '--include=*.js', '--include=*.ts',
         '--include=*.tsx', '--include=*.jsx', '-E', '(TODO|FIXME|HACK|XXX):'],
        capture_output=True,
        text=True,
        timeout=2
    )

    if result.stdout:
        lines = result.stdout.strip().split('\n')

        print("\n## Active TODOs and FIXMEs (Auto-injected)")
        print(f"Found {len(lines)} items:\n")
        print("```")

        # Show first 20 TODOs
        for line in lines[:20]:
            print(line)

        if len(lines) > 20:
            print(f"\n... and {len(lines) - 20} more")

        print("```")

except Exception:
    pass

sys.exit(0)
```

Configure in settings.json:
```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/todos-context.py",
            "timeout": 3
          }
        ]
      }
    ]
  }
}
```

## Recent Error Logs Context

Inject recent errors or warnings from application logs:

```python
#!/usr/bin/env python3
"""Inject recent errors from logs"""
import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

data = json.load(sys.stdin)
prompt = data.get('prompt', '').lower()

# Look for error-related keywords
if not any(word in prompt for word in ['error', 'fail', 'bug', 'crash', 'debug', 'issue']):
    sys.exit(0)

# Search for log files
log_locations = [
    'logs',
    '.logs',
    'log',
    'var/log',
    'build/logs',
    'dist/logs'
]

recent_errors = []

for log_dir in log_locations:
    log_path = Path(log_dir)
    if log_path.exists() and log_path.is_dir():
        # Find .log files modified in last hour
        cutoff = datetime.now() - timedelta(hours=1)

        for log_file in log_path.glob('**/*.log'):
            try:
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if mtime > cutoff:
                    with open(log_file, 'r', errors='ignore') as f:
                        content = f.read()

                    # Extract error lines
                    for line in content.split('\n'):
                        if any(word in line.lower() for word in ['error', 'exception', 'failed', 'fatal']):
                            recent_errors.append(f"{log_file.name}: {line[:100]}")
            except:
                pass

if recent_errors:
    print("\n## Recent Errors (Auto-injected)")
    print("```")
    for error in recent_errors[:10]:
        print(error)
    if len(recent_errors) > 10:
        print(f"\n... and {len(recent_errors) - 10} more errors")
    print("```")

sys.exit(0)
```

## Environment and Version Context

Inject relevant tool versions and environment information:

```bash
#!/bin/bash
# environment-context.sh - Inject tool versions and environment

input=$(cat)
prompt=$(echo "$input" | jq -r '.prompt // empty')

# Only inject if prompt mentions environment/versions
if [[ ! "$prompt" =~ (version|environment|setup|install|config|python|node|rust|go) ]]; then
    exit 0
fi

echo ""
echo "## Development Environment (Auto-injected)"
echo ""

# Node/npm versions
if command -v node &> /dev/null; then
    echo "- **Node.js**: $(node --version)"
    echo "- **npm**: $(npm --version)"
fi

# Python version
if command -v python3 &> /dev/null; then
    echo "- **Python**: $(python3 --version 2>&1 | awk '{print $2}')"
fi

# Rust version
if command -v rustc &> /dev/null; then
    echo "- **Rust**: $(rustc --version | awk '{print $2}')"
fi

# Go version
if command -v go &> /dev/null; then
    echo "- **Go**: $(go version | awk '{print $3}')"
fi

# Operating System
echo "- **OS**: $(uname -s)"
echo "- **Architecture**: $(uname -m)"

# Check for virtual environments
if [[ -n "$VIRTUAL_ENV" ]]; then
    echo "- **Python venv**: $(basename "$VIRTUAL_ENV")"
fi

if [[ -n "$NVM_BIN" ]]; then
    echo "- **NVM active**: Yes"
fi

echo ""

exit 0
```

## Project Statistics Context

Inject codebase statistics (file counts, line counts, language breakdown):

```python
#!/usr/bin/env python3
"""Inject project statistics"""
import json
import sys
from pathlib import Path
from collections import defaultdict

data = json.load(sys.stdin)
prompt = data.get('prompt', '').lower()

# Only inject for project-related prompts
if not any(word in prompt for word in ['project', 'codebase', 'repo', 'stats', 'size', 'large']):
    sys.exit(0)

try:
    # Count files by type
    file_stats = defaultdict(int)
    total_lines = 0

    extensions = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.jsx': 'JSX',
        '.tsx': 'TSX',
        '.java': 'Java',
        '.go': 'Go',
        '.rs': 'Rust',
        '.c': 'C',
        '.cpp': 'C++',
        '.h': 'C/C++ Header',
        '.css': 'CSS',
        '.html': 'HTML',
        '.json': 'JSON',
        '.yml': 'YAML',
        '.yaml': 'YAML',
        '.md': 'Markdown',
        '.sh': 'Shell',
    }

    # Scan files
    for filepath in Path('.').rglob('*'):
        if filepath.is_file() and not any(part.startswith('.') for part in filepath.parts):
            ext = filepath.suffix.lower()
            lang = extensions.get(ext, 'Other')
            file_stats[lang] += 1

            # Count lines for text files
            if ext in extensions and ext not in ['.json', '.jpg', '.png']:
                try:
                    total_lines += sum(1 for _ in filepath.open(errors='ignore'))
                except:
                    pass

    if file_stats:
        print("\n## Project Statistics (Auto-injected)")
        print(f"**Total lines of code**: ~{total_lines:,}")
        print("\n**Files by language**:")
        print("```")
        for lang in sorted(file_stats.keys(), key=lambda x: -file_stats[x]):
            print(f"  {lang}: {file_stats[lang]} files")
        print("```")

except Exception:
    pass

sys.exit(0)
```

## Code Examples from Similar Files

Inject relevant code patterns from similar files in the codebase:

```python
#!/usr/bin/env python3
"""Inject relevant code examples"""
import json
import sys
import subprocess
from pathlib import Path

data = json.load(sys.stdin)
prompt = data.get('prompt', '')

# Extract file extension if working with specific file
file_path = data.get('file_path', '')
if not file_path:
    sys.exit(0)

try:
    ext = Path(file_path).suffix
    if not ext:
        sys.exit(0)

    # Only for code files
    if ext not in ['.py', '.js', '.ts', '.java', '.go', '.rs']:
        sys.exit(0)

    # Find similar files
    result = subprocess.run(
        ['find', '.', '-name', f'*{ext}', '-type', 'f'],
        capture_output=True,
        text=True,
        timeout=2
    )

    files = [f for f in result.stdout.strip().split('\n')
             if f and f != file_path][:3]

    if files:
        print("\n## Similar Files in Project (Auto-injected)")
        print("Found similar files for reference:\n")

        for similar_file in files:
            try:
                with open(similar_file, 'r', errors='ignore') as f:
                    lines = f.readlines()

                # Show first function/class definition
                print(f"**{similar_file}**:")
                print("```")
                for i, line in enumerate(lines[:20]):
                    print(line.rstrip())
                    if 'def ' in line or 'class ' in line or 'function ' in line:
                        # Show a bit more of the definition
                        for j in range(i+1, min(i+5, len(lines))):
                            print(lines[j].rstrip())
                        break
                print("```\n")
            except:
                pass

except Exception:
    pass

sys.exit(0)
```

## Documentation and Guidelines Context

Inject project-specific guidelines and documentation:

```bash
#!/bin/bash
# docs-context.sh - Inject project guidelines and standards

input=$(cat)

# Look for relevant documentation
echo ""
echo "## Project Guidelines (Auto-injected)"
echo ""

# Check for various documentation files
if [[ -f "CONTRIBUTING.md" ]]; then
    echo "**Contribution Guidelines**:"
    echo '```'
    head -20 CONTRIBUTING.md
    echo '```'
    echo ""
fi

if [[ -f "ARCHITECTURE.md" ]]; then
    echo "**Architecture Overview**:"
    echo '```'
    head -20 ARCHITECTURE.md
    echo '```'
    echo ""
fi

if [[ -f ".cursorrules" ]] || [[ -f ".clinerules" ]]; then
    rules_file=$([[ -f ".cursorrules" ]] && echo ".cursorrules" || echo ".clinerules")
    echo "**Development Rules**:"
    echo '```'
    head -15 "$rules_file"
    echo '```'
    echo ""
fi

# Check for coding standards
if [[ -f ".eslintrc" ]] || [[ -f ".eslintrc.json" ]]; then
    echo "**Code Style**: ESLint configured"
fi

if [[ -f ".prettierrc" ]]; then
    echo "**Code Formatting**: Prettier configured"
fi

if [[ -f "pyproject.toml" ]] && grep -q "black" pyproject.toml 2>/dev/null; then
    echo "**Python Formatting**: Black configured"
fi

echo ""

exit 0
```

## Git History Context with Blame Info

Inject recent relevant commits and file history:

```python
#!/usr/bin/env python3
"""Inject git history context for current file"""
import json
import sys
import subprocess

data = json.load(sys.stdin)
prompt = data.get('prompt', '')
file_path = data.get('file_path', '')

# Only if working with a specific file
if not file_path or not any(word in prompt.lower() for word in ['history', 'blame', 'change', 'edit', 'modify']):
    sys.exit(0)

try:
    # Get recent commits for this file
    result = subprocess.run(
        ['git', 'log', '--oneline', '-10', file_path],
        capture_output=True,
        text=True,
        timeout=2,
        cwd='.'
    )

    if result.returncode == 0 and result.stdout:
        print("\n## File History (Auto-injected)")
        print(f"**Recent changes to {file_path}**:")
        print("```")
        print(result.stdout.strip())
        print("```")

        # Get who last modified each section (if file is small enough)
        try:
            blame_result = subprocess.run(
                ['git', 'blame', '-L', '1,20', file_path],
                capture_output=True,
                text=True,
                timeout=2,
                cwd='.'
            )

            if blame_result.returncode == 0:
                print("\n**Recent edits** (first 20 lines):")
                print("```")
                for line in blame_result.stdout.split('\n')[:10]:
                    if line:
                        # Extract author and commit info
                        parts = line.split(')')
                        if len(parts) > 1:
                            print(parts[0][:50] + ") " + parts[1][:60])
                print("```")
        except:
            pass

except Exception:
    pass

sys.exit(0)
```

## Issue Tracker Context

Inject relevant open issues from GitHub/GitLab:

```python
#!/usr/bin/env python3
"""Inject open issues from repository"""
import json
import sys
import os
from pathlib import Path

data = json.load(sys.stdin)
prompt = data.get('prompt', '').lower()

# Check for issue-related keywords
if not any(word in prompt for word in ['issue', 'bug', 'feature', 'problem', 'task']):
    sys.exit(0)

# Try to detect repo type
gh_path = Path('.github')
gl_path = Path('.gitlab')

# For GitHub, try to use gh CLI if available
if gh_path.exists():
    try:
        import subprocess

        result = subprocess.run(
            ['gh', 'issue', 'list', '--limit', '10'],
            capture_output=True,
            text=True,
            timeout=3
        )

        if result.returncode == 0 and result.stdout:
            print("\n## Open Issues (Auto-injected)")
            print("```")
            # Show first 10 issues
            for line in result.stdout.strip().split('\n')[:10]:
                if line:
                    print(line[:100])
            print("```")
    except:
        pass

sys.exit(0)
```

## Advanced: Conditional Context by File Type

Smart context injection that varies by file type being edited:

```python
#!/usr/bin/env python3
"""Smart context injection based on file type"""
import json
import sys
from pathlib import Path
from datetime import datetime

data = json.load(sys.stdin)
prompt = data.get('prompt', '')
file_path = data.get('file_path', '')

if not file_path:
    sys.exit(0)

ext = Path(file_path).suffix.lower()
name = Path(file_path).name

print(f"\n## File Context (Auto-injected)")

# Python files
if ext == '.py':
    print(f"**File**: {name}")

    # Check for tests
    if 'test_' in name or '_test.py' in name:
        print("**Type**: Test file")
        # Inject testing framework info
        try:
            with open('pyproject.toml', 'r') as f:
                if 'pytest' in f.read():
                    print("**Test Framework**: pytest")
        except:
            pass
    else:
        print("**Type**: Module")

    # Check imports to understand dependencies
    try:
        with open(file_path, 'r') as f:
            first_50_lines = ''.join(f.readlines()[:50])

        if 'django' in first_50_lines:
            print("**Framework**: Django detected")
        elif 'flask' in first_50_lines:
            print("**Framework**: Flask detected")
        elif 'fastapi' in first_50_lines:
            print("**Framework**: FastAPI detected")
    except:
        pass

# TypeScript/JavaScript files
elif ext in ['.ts', '.tsx', '.js', '.jsx']:
    print(f"**File**: {name}")

    if 'test' in name or 'spec' in name:
        print("**Type**: Test file")
    elif 'component' in name or ext in ['.tsx', '.jsx']:
        print("**Type**: React component")
    else:
        print("**Type**: Module")

    # Check package.json for frameworks
    try:
        import json
        with open('package.json', 'r') as f:
            pkg = json.load(f)
            deps = list(pkg.get('dependencies', {}).keys())

        if 'react' in deps:
            print("**Framework**: React")
        elif 'vue' in deps:
            print("**Framework**: Vue")
        elif 'next' in deps:
            print("**Framework**: Next.js")
        elif 'express' in deps:
            print("**Framework**: Express")
    except:
        pass

# Markdown/docs files
elif ext in ['.md', '.mdx']:
    print(f"**File**: {name}")
    print("**Type**: Documentation")

    # Check if it's a README
    if 'readme' in name.lower():
        print("**Priority**: Main documentation")

print("")
sys.exit(0)
```

## Rate-Limited Context Caching

Cache expensive context operations to avoid running on every prompt:

```python
#!/usr/bin/env python3
"""Cache context to avoid expensive recomputation"""
import json
import sys
import os
import hashlib
import time
from pathlib import Path

data = json.load(sys.stdin)
prompt = data.get('prompt', '')

# Setup cache directory
cache_dir = Path('./.claude/hook-cache')
cache_dir.mkdir(parents=True, exist_ok=True)

# Create cache key from prompt
prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
cache_file = cache_dir / f'context-{prompt_hash}.json'

# Use cache if it's less than 5 minutes old
if cache_file.exists():
    age = time.time() - cache_file.stat().st_mtime
    if age < 300:  # 5 minutes
        try:
            with open(cache_file, 'r') as f:
                cached = json.load(f)
                print(cached.get('context', ''))
            sys.exit(0)
        except:
            pass

# If no cache, generate fresh context (simulated)
context = ""

# ... expensive context generation here ...

# Cache the result
try:
    with open(cache_file, 'w') as f:
        json.dump({
            'context': context,
            'generated': time.time()
        }, f)
except:
    pass

print(context)
sys.exit(0)
```

## Input Validation: Block on Sensitive Prompts

Validate prompts before injecting context to prevent leaking information:

```python
#!/usr/bin/env python3
"""Validate prompt and block context injection if needed"""
import json
import sys

data = json.load(sys.stdin)
prompt = data.get('prompt', '').lower()

# Patterns that shouldn't get context injection
blocking_patterns = [
    'password',
    'secret',
    'token',
    'api_key',
    'credentials',
    'auth_code',
    'ssh_key'
]

# Check for sensitive content
if any(pattern in prompt for pattern in blocking_patterns):
    # Don't inject context that might contain sensitive info
    print("")
    print("**Security Note**: Sensitive topic detected - limiting context injection")
    print("")
    sys.exit(0)

# Safe to inject full context
# ... proceed with context injection ...

sys.exit(0)
```

## Real-World Pattern: Full-Featured Context Injection

Production-ready hook combining multiple context sources:

```python
#!/usr/bin/env python3
"""Production-grade context injection hook"""
import json
import sys
import subprocess
import os
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta

def safe_run(cmd, timeout=2):
    """Run command safely with timeout"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=isinstance(cmd, str)
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except:
        return ""

def get_git_context():
    """Get git status and recent commits"""
    if not Path('.git').exists():
        return ""

    context = "\n## Git Status (Auto-injected)\n"

    # Current branch
    branch = safe_run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
    if branch:
        context += f"- **Branch**: `{branch}`\n"

    # Uncommitted changes
    status = safe_run(['git', 'status', '--short'])
    if status:
        context += f"- **Changes**: {len(status.split(chr(10)))} files modified\n"
    else:
        context += "- **Working tree**: Clean\n"

    # Recent commits
    commits = safe_run(['git', 'log', '--oneline', '-5'])
    if commits:
        context += "\n**Recent commits**:\n```\n"
        context += commits
        context += "\n```\n"

    return context

def get_project_type():
    """Detect project type and relevant info"""
    context = "\n## Project Type (Auto-injected)\n"

    if Path('package.json').exists():
        context += "- **Type**: Node.js/JavaScript\n"
        try:
            import json
            with open('package.json') as f:
                pkg = json.load(f)
                if 'framework' in str(pkg):
                    context += f"- **Framework**: Detected\n"
        except:
            pass

    if Path('pyproject.toml').exists():
        context += "- **Type**: Python\n"

    if Path('Cargo.toml').exists():
        context += "- **Type**: Rust\n"

    if Path('go.mod').exists():
        context += "- **Type**: Go\n"

    return context

def get_todos():
    """Extract TODO items"""
    todos = safe_run([
        'grep', '-r', '-n', '-E', '(TODO|FIXME):',
        '--include=*.py', '--include=*.js', '--include=*.ts'
    ])

    if todos:
        lines = todos.split('\n')[:5]
        context = "\n## Active TODOs (Auto-injected)\n```\n"
        context += '\n'.join(lines)
        if len(todos.split('\n')) > 5:
            context += f"\n... and {len(todos.split(chr(10))) - 5} more\n"
        context += "```\n"
        return context

    return ""

# Main hook logic
data = json.load(sys.stdin)
prompt = data.get('prompt', '').lower()

# Build context
context = ""

# Always include git context if in repo
context += get_git_context()

# Include project type
context += get_project_type()

# Include TODOs if mentioned or code-related
if any(word in prompt for word in ['todo', 'task', 'code', 'build', 'fix']):
    context += get_todos()

# Print context
if context:
    print(context)

sys.exit(0)
```

## Best Practices

### 1. Keep Execution Fast
- Target execution time: < 1 second
- Use `timeout` in hook configuration
- Cache expensive operations

```json
{
  "type": "command",
  "command": "my-context-hook.sh",
  "timeout": 2
}
```

### 2. Provide Clear Attribution
Always mark injected content so Claude knows it's auto-generated:
```
## Git Status (Auto-injected)
- Branch: main
- Changes: 3 files modified
```

### 3. Be Conditional
Only inject context when relevant to the prompt:
```bash
if [[ "$prompt" =~ (git|commit|branch) ]]; then
    # Inject git context
fi
```

### 4. Respect User Intent
Don't override user prompts or add context they didn't ask for:
```bash
# Good: augments user request
## Environment (Auto-injected)
- Node: 18.0.0
- Python: 3.11.0

# Bad: contradicts user request
# User said ignore environment, but we inject it anyway
```

### 5. Handle Errors Gracefully
If context generation fails, fail silently:
```bash
if [[ ! -f "package.json" ]]; then
    exit 0  # Not a Node project, no context needed
fi
```

### 6. Cache When Expensive
For operations that might take time, cache results:
```python
cache_file = Path('./.claude/hook-cache/git-status.json')
if cache_file.exists() and (time.time() - cache_file.stat().st_mtime) < 60:
    # Use cached results
```

## Troubleshooting

### Context Not Appearing
- **Issue**: Injected context doesn't show in Claude's response
- **Cause**: Hook might be outputting to stderr instead of stdout
- **Fix**: Ensure all context goes to `print()` or `echo`, not `print(..., file=sys.stderr)`

### Hook Too Slow
- **Issue**: Delay before Claude starts responding
- **Cause**: Context hook taking too long
- **Fix**: Add timeout to hook, move slow operations to cache, or simplify logic

### Unwanted Context
- **Issue**: Context appearing when you don't want it
- **Cause**: Hook not checking prompt content
- **Fix**: Add conditional checks: `if word in prompt: inject_context()`

### Git Context Missing
- **Issue**: Git information not injected
- **Cause**: Not in git repository
- **Fix**: Check for `.git` directory before running git commands

### Performance Degradation
- **Issue**: Each prompt takes longer
- **Cause**: Hook running expensive operations on every prompt
- **Fix**: Implement caching or move to periodic updates

## Performance Benchmark

Typical hook execution times:

| Operation | Time |
|-----------|------|
| Git status | 50-100ms |
| Grep for TODOs | 100-500ms |
| Environment variables | 10-20ms |
| Project statistics | 500ms-1s |
| Documentation read | 50-100ms |
| File history (blame) | 200-500ms |

**Total recommended**: < 2 seconds for responsive UX

## Advanced Patterns

### Conditional Rich Context
Inject different context based on file type:
```python
if file_path.endswith('.py'):
    inject_python_context()
elif file_path.endswith('.ts'):
    inject_typescript_context()
```

### Multi-Hook Orchestration
Chain multiple context hooks:
```json
"UserPromptSubmit": [
    { "type": "command", "command": "git-context.sh" },
    { "type": "command", "command": "todos-context.py" },
    { "type": "command", "command": "env-context.sh" }
]
```

### Smart Rate Limiting
Use file modification times to avoid recomputing:
```python
if cache_age > 300:  # 5 minutes
    regenerate_context()
```

