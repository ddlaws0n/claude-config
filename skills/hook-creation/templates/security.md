# Security & Safety Hook Templates

Templates for hooks that enforce security policies, protect sensitive files, and implement access controls.

## File Protection Hooks

### PreToolUse: Block Sensitive File Modifications
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|Glob|Grep",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, os\nfrom pathlib import Path\n\n# Define sensitive patterns\nSENSITIVE_PATTERNS = [\n    '.env', '.env.local', '.env.production',\n    'secrets.yaml', 'secrets.json',\n    'id_rsa', 'id_ed25519', '*.pem', '*.key',\n    '.aws/credentials', '.aws/config',\n    '.kube/config', 'kubeconfig',\n    'config/database.yml',\n    'node_modules/', 'dist/', 'build/',\n    '.git/', '.gitignore'\n]\n\ndef is_sensitive_file(file_path):\n    path = Path(file_path)\n    filename = path.name\n    \n    for pattern in SENSITIVE_PATTERNS:\n        if pattern.endswith('/'):\n            # Directory pattern\n            if pattern[:-1] in str(path.parent):\n                return True\n        elif '*' in pattern:\n            # Wildcard pattern\n            if filename.endswith(pattern.replace('*', '')):\n                return True\n        else:\n            # Exact match\n            if filename == pattern or pattern in str(path):\n                return True\n    \n    return False\n\ndef check_content_secrets(content):\n    import re\n    \n    secret_patterns = [\n        r'password\\s*[:=]\\s*[\"'\\''][^\"'\\']+['\"\\'']',\n        r'api[_-]?key\\s*[:=]\\s*[\"'\\''][^\"'\\']{20,}['\"\\'']',\n        r'secret[_-]?key\\s*[:=]\\s*[\"'\\''][^\"'\\']{20,}['\"\\'']',\n        r'AWS[_-]?SECRET[_-]?ACCESS[_-]?KEY\\s*[:=]',\n        r'BEGIN\\s+(RSA\\s+)?PRIVATE\\s+KEY'\n    ]\n    \n    for pattern in secret_patterns:\n        if re.search(pattern, content, re.IGNORECASE):\n            return True\n    return False\n\ndata = json.load(sys.stdin)\ntool_name = data.get('tool_name', '')\ntool_input = data.get('tool_input', {})\n\nif tool_name in ['Edit', 'Write']:\n    file_path = tool_input.get('file_path', '')\n    \n    if is_sensitive_file(file_path):\n        print(f'❌ Access denied: Cannot modify sensitive file: {file_path}', file=sys.stderr)\n        sys.exit(2)  # Block the operation\n    \n    # Check content for Write operations\n    if tool_name == 'Write':\n        content = tool_input.get('content', '')\n        if check_content_secrets(content):\n            print('❌ Content contains potential secrets', file=sys.stderr)\n            sys.exit(2)\n\nelif tool_name == 'Grep':\n    pattern = tool_input.get('pattern', '')\n    if any(secret in pattern.lower() for secret in ['password', 'secret', 'key', 'token']):\n        print('⚠️ Warning: Searching for sensitive patterns', file=sys.stderr)\n\nsys.exit(0)  # Allow the operation\n\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### PreToolUse: Production Environment Protection
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|Edit|Write|Glob|Grep",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, os\nfrom pathlib import Path\n\ndef is_production_env():\n    \"\"\"Check if we're in a production environment\"\"\"\n    indicators = [\n        os.getenv('NODE_ENV') == 'production',\n        os.getenv('ENV') == 'production',\n        os.getenv('APP_ENV') == 'production',\n        'prod' in os.getenv('HOSTNAME', '').lower(),\n        os.path.exists('/.dockerenv') and os.getenv('ENV') != 'development'\n    ]\n    return any(indicators)\n\ndef is_dangerous_command(command):\n    \"\"\"Check for potentially dangerous commands\"\"\"\n    dangerous = [\n        'rm -rf /',\n        'rm -rf /*',\n        ':(){ :|:& };:',  # Fork bomb\n        'dd if=/dev/zero of=',\n        'mkfs.',\n        'fdisk',\n        'iptables -F',\n        'chmod -R 777',\n        'chown -R',\n        '> /dev/sda',\n        'sudo rm -rf'\n    ]\n    \n    cmd_lower = command.lower()\n    return any(danger in cmd_lower for danger in dangerous)\n\nif is_production_env():\n    data = json.load(sys.stdin)\n    tool_name = data.get('tool_name', '')\n    \n    if tool_name == 'Bash':\n        command = data.get('tool_input', {}).get('command', '')\n        \n        # Block dangerous commands\n        if is_dangerous_command(command):\n            print(f'❌ Dangerous command blocked in production: {command[:50]}...', file=sys.stderr)\n            sys.exit(2)\n        \n        # Warn about modifications\n        if any(word in command.lower() for word in ['rm ', 'delete', 'drop', 'truncate']):\n            print('⚠️ Warning: Modification command in production environment', file=sys.stderr)\n    \n    elif tool_name in ['Edit', 'Write']:\n        file_path = data.get('tool_input', {}).get('file_path', '')\n        print(f'⚠️ Warning: Modifying file in production: {file_path}', file=sys.stderr)\n\nsys.exit(0)\n\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

## Secret Detection Hooks

### PostToolUse: Scan for Committed Secrets
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, re\nfrom pathlib import Path\n\n# Common secret patterns\nSECRET_PATTERNS = {\n    'AWS Access Key': r'AKIA[0-9A-Z]{16}',\n    'AWS Secret Key': r'(?i)aws[_-]?secret[_-]?access[_-]?key\\s*[:=]\\s*[\"'\\'']([A-Za-z0-9/+=]{40})[\"'\\'']',\n    'GitHub Token': r'ghp_[a-zA-Z0-9]{36}',\n    'Generic API Key': r'(?i)api[_-]?key\\s*[:=]\\s*[\"'\\'']([a-zA-Z0-9_\-]{20,})[\"'\\'']',\n    'Password': r'(?i)password\\s*[:=]\\s*[\"'\\'']([^\"'\\'>]{8,})[\"'\\'']',\n    'Private Key': r'-----BEGIN(?: RSA| DSA| EC| OPENSSH)? PRIVATE KEY-----',\n    'Database URL': r'(?i)(?:postgres|mysql|mongodb)://[^:]+:[^@]+@[^/]+',\n    'JWT Token': r'eyJ[a-zA-Z0-9_-]*\\.eyJ[a-zA-Z0-9_-]*\\.[a-zA-Z0-9_-]*'\n}\n\ndef scan_for_secrets(content):\n    findings = []\n    for name, pattern in SECRET_PATTERNS.items():\n        matches = re.findall(pattern, content, re.MULTILINE)\n        if matches:\n            findings.append({\n                'type': name,\n                'matches': len(matches),\n                'pattern': pattern\n            })\n    return findings\n\ndata = json.load(sys.stdin)\nfile_path = data.get('tool_input', {}).get('file_path', '')\ncontent = data.get('tool_input', {}).get('content', '')\n\nif content and not file_path.endswith(('.key', '.pem', '.env')):\n    findings = scan_for_secrets(content)\n    \n    if findings:\n        print(f'⚠️ Potential secrets detected in {Path(file_path).name}:', file=sys.stderr)\n        for finding in findings:\n            print(f'  - {finding[\"type\"]}: {finding[\"matches\"]} matches', file=sys.stderr)\n        print('  ❌ Please review and remove any sensitive information', file=sys.stderr)\n\nsys.exit(0)\n\"",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

### PreToolUse: Block Secret Operations in Git
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c '\ninput=$(cat)\ncommand=$(echo \"$input\" | jq -r \".tool_input.command // empty\")\n\n# Block git operations that might expose secrets\nif [[ \"$command\" =~ ^git ]]; then\n    # Check for risky git commands\n    if [[ \"$command\" =~ (git\\s+add|git\\s+commit) ]]; then\n        # Check staged files for secrets\n        if command -v git &> /dev/null; then\n            # Get list of staged files\n            staged_files=$(git diff --cached --name-only 2>/dev/null || true)\n            \n            for file in $staged_files; do\n                if [[ \"$file\" =~ \\.(env|key|pem|p12)$ ]]; then\n                    echo \"❌ Cannot commit sensitive file: $file\" >&2\n                    exit 2\n                fi\n                \n                # Quick scan for obvious patterns\n                if git show :\"$file\" 2>/dev/null | grep -q -E \"(password|secret|key|token).*=.*['\\\"]\"; then\n                    echo \"⚠️ Warning: $file may contain secrets\" >&2\n                fi\n            done\n        fi\n    fi\n    \n    # Block git push to main/master\n    if [[ \"$command\" =~ git\\s+push.*(main|master) ]]; then\n        echo \"❌ Direct push to main/master is blocked. Use pull requests instead.\" >&2\n        exit 2\n    fi\nfi\n\nexit 0'",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

## Access Control Hooks

### PermissionRequest: Auto-Approve Safe Operations
```json
{
  "hooks": {
    "PermissionRequest": [
      {
        "matcher": "Read|Write|Edit|Glob|Grep",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys\nfrom pathlib import Path\n\n# Safe directories and patterns\nSAFE_DIRECTORIES = [\n    'src/', 'lib/', 'app/', 'docs/', 'tests/',\n    'scripts/', 'config/', 'templates/'\n]\n\nSAFE_EXTENSIONS = [\n    '.md', '.txt', '.json', '.yaml', '.yml', '.toml',\n    '.py', '.js', '.ts', '.tsx', '.jsx',\n    '.css', '.scss', '.html', '.xml'\n]\n\nDANGEROUS_EXTENSIONS = [\n    '.env', '.key', '.pem', '.p12', '.crt',\n    '.sh', '.bat', '.cmd', '.exe', '.bin'\n]\n\ndef is_safe_path(file_path):\n    path = Path(file_path)\n    \n    # Check if in safe directory\n    for safe_dir in SAFE_DIRECTORIES:\n        if str(path).startswith(safe_dir):\n            return True\n    \n    # Check extension\n    if path.suffix in DANGEROUS_EXTENSIONS:\n        return False\n    \n    if path.suffix in SAFE_EXTENSIONS:\n        return True\n    \n    # Default to manual approval\n    return False\n\ndata = json.load(sys.stdin)\ntool_name = data.get('tool_name', '')\ntool_input = data.get('tool_input', {})\n\n# Auto-approve reads from safe paths\nif tool_name == 'Read':\n    file_path = tool_input.get('file_path', '')\n    if is_safe_path(file_path):\n        # Auto-approve read operations for safe files\n        output = {\n            'hookSpecificOutput': {\n                'hookEventName': 'PermissionRequest',\n                'decision': {\n                    'behavior': 'allow',\n                    'message': f'Auto-approved: Reading safe file {Path(file_path).name}'\n                }\n            }\n        }\n        print(json.dumps(output))\n        sys.exit(0)\n\n# Auto-approve writes to safe directories for safe extensions\nelif tool_name in ['Write', 'Edit']:\n    file_path = tool_input.get('file_path', '')\n    if is_safe_path(file_path):\n        output = {\n            'hookSpecificOutput': {\n                'hookEventName': 'PermissionRequest',\n                'decision': {\n                    'behavior': 'allow',\n                    'message': f'Auto-approved: Writing to safe path {file_path}'\n                }\n            }\n        }\n        print(json.dumps(output))\n        sys.exit(0)\n\n# Default: require manual approval\nsys.exit(0)\n\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

## Audit and Logging Hooks

### PostToolUse: Security Audit Log
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, os\nfrom datetime import datetime\n\n# Create audit log directory\naudit_dir = os.path.expanduser('~/.claude/audit')\nos.makedirs(audit_dir, exist_ok=True)\n\n# Create log file for today\nlog_file = os.path.join(audit_dir, f'audit-{datetime.now().strftime(\"%Y-%m-%d\")}.jsonl')\n\ndata = json.load(sys.stdin)\n\n# Create audit entry\naudit_entry = {\n    'timestamp': datetime.now().isoformat(),\n    'session_id': data.get('session_id', ''),\n    'tool_name': data.get('tool_name', ''),\n    'cwd': data.get('cwd', ''),\n    'permission_mode': data.get('permission_mode', ''),\n    'tool_input': data.get('tool_input', {}),\n    'tool_response': data.get('tool_response', {})\n}\n\n# Log sensitive operations\nsensitive_tools = ['Bash', 'Write', 'Edit', 'Grep']\nif audit_entry['tool_name'] in sensitive_tools:\n    with open(log_file, 'a') as f:\n        f.write(json.dumps(audit_entry) + '\\n')\n\nsys.exit(0)\n\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### SessionStart: Security Context Check
```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, os\nfrom pathlib import Path\n\n# Security context report\nreport = []\n\n# Check environment variables\nsensitive_vars = ['API_KEY', 'SECRET', 'TOKEN', 'PASSWORD']\nfound_vars = [var for var in os.environ.keys() if any(s in var.upper() for s in sensitive_vars)]\n\nif found_vars:\n    report.append(f'⚠️ Sensitive environment variables detected: {len(found_vars)}')\n\n# Check for insecure file permissions\ncwd = Path.cwd()\ninsecure_files = []\n\nfor pattern in ['.env', 'secrets.*', '*.key', '*.pem']:\n    for file in cwd.glob(pattern):\n        if file.is_file() and oct(file.stat().st_mode)[-3:] != '600':\n            insecure_files.append(str(file))\n\nif insecure_files:\n    report.append(f'❌ Files with insecure permissions: {len(insecure_files)}')\n    for f in insecure_files[:3]:\n        report.append(f'  - {f}')\n\n# Check git status\nif (cwd / '.git').exists():\n    import subprocess\n    result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)\n    if result.stdout.strip():\n        report.append('📝 Git repository has uncommitted changes')\n\n# Add context to session\nif report:\n    context = '\\n'.join(report)\n    print('Security Context:')\n    print(context)\nelse:\n    print('✅ Security checks passed')\n\nsys.exit(0)\n\"",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

## Complete Security Hook Configuration

### Production-Ready Security Setup
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/security-check.sh",
            "timeout": 5
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/secret-scan.sh",
            "timeout": 10
          }
        ]
      },
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/audit-log.sh",
            "timeout": 5
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/security-context.sh",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

Create `.claude/hooks/security-check.sh`:
```bash
#!/bin/bash
# Combined security check hook
input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name // empty')

# Check file modifications
if [[ "$tool_name" =~ ^(Edit|Write|Glob|Grep)$ ]]; then
    # Run file protection check
    echo "$input" | python3 -c "
import json, sys
from pathlib import Path

SENSITIVE_FILES = [
    '.env', 'secrets.', '.aws/', '.kube/',
    'id_rsa', '*.pem', '*.key', '.git/'
]

data = json.load(sys.stdin)
file_path = data.get('tool_input', {}).get('file_path', '')

for pattern in SENSITIVE_FILES:
    if pattern in file_path or file_path.endswith(pattern.replace('*', '')):
        print(f'❌ Access denied to sensitive file: {file_path}', file=sys.stderr)
        sys.exit(2)
"
fi

exit 0
```

Create `.claude/hooks/secret-scan.sh`:
```bash
#!/bin/bash
# Secret scanning hook
input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')
content=$(echo "$input" | jq -r '.tool_input.content // empty')

if [[ -n "$content" ]] && [[ ! "$file_path" =~ \.(key|pem|env)$ ]]; then
    # Quick secret pattern check
    if echo "$content" | grep -qE "(password|secret|key|token).*=.*['\"][^'\"]{10,}['\"]"; then
        echo "⚠️ Potential secrets detected in $(basename "$file_path")" >&2
        echo "❌ Please review for sensitive information" >&2
    fi
fi

exit 0
```

Create `.claude/hooks/audit-log.sh`:
```bash
#!/bin/bash
# Audit logging hook
input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name // empty')

# Only log sensitive operations
if [[ "$tool_name" =~ ^(Bash|Write|Edit|Grep)$ ]]; then
    AUDIT_DIR="$HOME/.claude/audit"
    mkdir -p "$AUDIT_DIR"

    LOG_FILE="$AUDIT_DIR/audit-$(date +%Y-%m-%d).jsonl"
    echo "$(date -Iseconds) $tool_name $(echo "$input" | jq -r '.cwd // empty')" >> "$LOG_FILE"
fi

exit 0
```

Create `.claude/hooks/security-context.sh`:
```bash
#!/bin/bash
# Security context report
echo "🔒 Security Context:" >&2

# Check environment
if env | grep -qE "(API_KEY|SECRET|TOKEN|PASSWORD)"; then
    echo "  ⚠️ Sensitive environment variables present" >&2
fi

# Check file permissions
find . -maxdepth 2 -type f \( -name "*.env" -o -name "secrets.*" -o -name "*.key" \) -not -perm 600 2>/dev/null | while read f; do
    echo "  ❌ Insecure permissions: $f" >&2
done

# Check git status
if git rev-parse --git-dir > /dev/null 2>&1; then
    if [[ -n $(git status --porcelain 2>/dev/null) ]]; then
        echo "  📝 Git repository has changes" >&2
    fi
fi

echo "✅ Security context loaded" >&2
exit 0
```