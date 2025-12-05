# Monitoring & Notification Hook Templates

Templates for hooks that provide notifications, track progress, log activity, and integrate with external monitoring systems.

## Desktop Notifications

### Notification Hook: Desktop Alerts
```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, subprocess\nimport os\n\n# Get notification details\ndata = json.load(sys.stdin)\nmessage = data.get('message', '')\nnotification_type = data.get('notification_type', '')\n\n# Only send notifications for important events\nimportant_types = ['permission_prompt', 'idle_prompt', 'error']\n\nif notification_type in important_types:\n    # Determine icon based on type\n    icon_map = {\n        'permission_prompt': 'dialog-question',\n        'idle_prompt': 'dialog-information',\n        'error': 'dialog-error',\n        'auth_success': 'dialog-password'\n    }\n    \n    icon = icon_map.get(notification_type, 'dialog-information')\n    \n    # Try different notification systems\n    if os.name == 'darwin':  # macOS\n        subprocess.run([\n            'osascript', '-e', f'display notification \\\"Claude Code\\\" with title \\\"{message}\\\" subtitle \\\"{notification_type}\\\"'\n        ], capture_output=True)\n    elif os.name == 'posix' and shutil.which('notify-send'):  # Linux\n        subprocess.run([\n            'notify-send', '-i', icon, 'Claude Code', f'{message} ({notification_type})'\n        ], capture_output=True)\n    elif os.name == 'nt':  # Windows\n        import win10toast\n        try:\n            toaster = win10toast.ToastNotifier()\n            toaster.show_toast('Claude Code', message, duration=5)\n        except:\n            pass\n\nsys.exit(0)\n\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### Notification Hook: Attention Required Alerts
```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "permission_prompt",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c '\n# Play sound for permission requests (macOS)\nif command -v afplay &> /dev/null; then\n    afplay /System/Library/Sounds/Glass.aiff 2>/dev/null &\nelif command -v paplay &> /dev/null; then\n    paplay /usr/share/sounds/freedesktop/stereo/message.oga 2>/dev/null &\nfi\n\n# Send desktop notification\ninput=$(cat)\nmessage=$(echo \"$input\" | jq -r \".message // empty\")\n\nif command -v notify-send &> /dev/null; then\n    notify-send -u critical \"Claude Code\" \"🚨 $message\"\nelif [[ \"$OSTYPE\" == \"darwin*\" ]]; then\n    osascript -e \"display notification \\\"🚨 $message\\\" with title \\\"Claude Code - Permission Required\\\"\"\nfi'",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

## Progress Tracking and Metrics

### PostToolUse: Track Development Metrics
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, os\nfrom datetime import datetime, timedelta\nfrom pathlib import Path\n\nMETRICS_DIR = os.path.expanduser('~/.claude/metrics')\nos.makedirs(METRICS_DIR, exist_ok=True)\n\n# Load metrics file\nmetrics_file = os.path.join(METRICS_DIR, 'development-metrics.json')\n\ntry:\n    with open(metrics_file, 'r') as f:\n        metrics = json.load(f)\nexcept:\n    metrics = {\n        'session_start': datetime.now().isoformat(),\n        'tools_used': {},\n        'files_touched': set(),\n        'languages_used': set()\n    }\n\ndata = json.load(sys.stdin)\ntool_name = data.get('tool_name', '')\n\n# Track tool usage\nif tool_name not in metrics['tools_used']:\n    metrics['tools_used'][tool_name] = 0\nmetrics['tools_used'][tool_name] += 1\n\n# Track file modifications\nif tool_name in ['Edit', 'Write']:\n    file_path = data.get('tool_input', {}).get('file_path', '')\n    if file_path:\n        metrics['files_touched'].add(file_path)\n        \n        # Track language based on extension\n        ext = Path(file_path).suffix.lower()\n        if ext in ['.py', '.js', '.ts', '.tsx', '.jsx', '.go', '.rs']:\n            metrics['languages_used'].add(ext)\n\n# Update session time\nmetrics['last_activity'] = datetime.now().isoformat()\n\n# Convert sets to lists for JSON serialization\nif 'files_touched' in metrics and isinstance(metrics['files_touched'], set):\n    metrics['files_touched'] = list(metrics['files_touched'])\nif 'languages_used' in metrics and isinstance(metrics['languages_used'], set):\n    metrics['languages_used'] = list(metrics['languages_used'])\n\n# Save metrics\nwith open(metrics_file, 'w') as f:\n    json.dump(metrics, f, indent=2)\n\n# Print daily summary every 50 operations\ntotal_ops = sum(metrics['tools_used'].values())\nif total_ops % 50 == 0:\n    print(f'📊 Session stats: {total_ops} operations, {len(metrics.get(\\\"files_touched\\\", []))} files modified', file=sys.stderr)\n\nsys.exit(0)\n\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### SessionEnd: Generate Session Report
```json
{
  "hooks": {
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, os\nfrom datetime import datetime\n\n# Load session metrics\nmetrics_file = os.path.expanduser('~/.claude/metrics/development-metrics.json')\nreport_file = os.path.expanduser('~/.claude/session-reports.json')\n\ntry:\n    with open(metrics_file, 'r') as f:\n        metrics = json.load(f)\nexcept:\n    sys.exit(0)  # No metrics to report\n\n# Calculate session duration\nstart_time = datetime.fromisoformat(metrics.get('session_start', datetime.now().isoformat()))\nduration = datetime.now() - start_time\n\n# Generate report\nreport = {\n    'date': datetime.now().isoformat(),\n    'session_duration_minutes': int(duration.total_seconds() / 60),\n    'tools_used': metrics.get('tools_used', {}),\n    'files_modified': len(metrics.get('files_touched', [])),\n    'languages_used': metrics.get('languages_used', []),\n    'total_operations': sum(metrics.get('tools_used', {}).values())\n}\n\n# Save to reports\nreports = []\ntry:\n    with open(report_file, 'r') as f:\n        reports = json.load(f)\nexcept:\n    pass\n\nreports.append(report)\n\n# Keep only last 30 reports\nif len(reports) > 30:\n    reports = reports[-30:]\n\nwith open(report_file, 'w') as f:\n    json.dump(reports, f, indent=2)\n\n# Print summary\nprint('📈 Session Summary:', file=sys.stderr)\nprint(f\"  Duration: {report['session_duration_minutes']} minutes\", file=sys.stderr)\nprint(f\"  Files modified: {report['files_modified']}\", file=sys.stderr)\nprint(f\"  Operations: {report['total_operations']}\", file=sys.stderr)\nif report['languages_used']:\n    print(f\"  Languages: {', '.join(report['languages_used'])}\", file=sys.stderr)\n\n# Clean up metrics for next session\nos.remove(metrics_file)\n\nsys.exit(0)\n\"",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

## External Service Integrations

### PostToolUse: Slack Notifications
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, os, requests\nfrom datetime import datetime\n\n# Slack webhook URL (set environment variable)\nSLACK_WEBHOOK = os.getenv('SLACK_WEBHOOK_URL')\n\nif not SLACK_WEBHOOK:\n    sys.exit(0)  # Skip if not configured\n\ndata = json.load(sys.stdin)\ntool_name = data.get('tool_name', '')\nfile_path = data.get('tool_input', {}).get('file_path', '')\ncwd = data.get('cwd', '')\n\n# Get project name from directory\nproject_name = os.path.basename(cwd) or 'unknown'\n\n# Create message\nif tool_name == 'Write':\n    action = 'created'\nelif tool_name == 'Edit':\n    action = 'modified'\nelse:\n    sys.exit(0)  # Skip other tools\n\nmessage = {\n    'text': f'Claude Code activity in *{project_name}*',\n    'attachments': [{\n        'color': 'good',\n        'fields': [\n            {\n                'title': 'Action',\n                'value': f'{action} {os.path.basename(file_path)}',\n                'short': True\n            },\n            {\n                'title': 'Time',\n                'value': datetime.now().strftime('%H:%M'),\n                'short': True\n            }\n        ]\n    }]\n}\n\n# Send to Slack\ntry:\n    response = requests.post(SLACK_WEBHOOK, json=message, timeout=5)\n    if response.status_code != 200:\n        print(f'Failed to send Slack notification: {response.status_code}', file=sys.stderr)\nexcept Exception as e:\n    print(f'Slack notification error: {e}', file=sys.stderr)\n\nsys.exit(0)\n\"",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

### PostToolUse: Discord Notifications
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c '\ninput=$(cat)\ncommand=$(echo \"$input\" | jq -r \".tool_input.command // empty\")\ncwd=$(echo \"$input\" | jq -r \".cwd // empty\")\n\n# Skip certain commands\nif [[ \"$command\" =~ ^(ls|pwd|echo|cat) ]]; then\n    exit 0\nfi\n\n# Get Discord webhook from environment\nDISCORD_WEBHOOK=\"$DISCORD_WEBHOOK_URL\"\nif [[ -z \"$DISCORD_WEBHOOK\" ]]; then\n    exit 0\nfi\n\n# Get project name\nproject_name=$(basename \"$cwd\")\n\n# Create Discord embed\ncurl -X POST \"$DISCORD_WEBHOOK\" \\\n    -H \"Content-Type: application/json\" \\\n    -d \"{\n        \\\"embeds\\\": [{\n            \\\"title\\\": \\\"Claude Code Command Executed\\\",\n            \\\"description\\\": \\`\\`\\`bash\\n$command\\n\\`\\`\\`,\n            \\\"color\\\": 5814783,\n            \\\"fields\\\": [\n                {\n                    \\\"name\\\": \\\"Project\\\",\n                    \\\"value\\\": \\\"$project_name\\\",\n                    \\\"inline\\\": true\n                },\n                {\n                    \\\"name\\\": \\\"Time\\\",\n                    \\\"value\\\": \\\"$(date +%H:%M)\\\",\n                    \\\"inline\\\": true\n                }\n            ]\n        }]\n    }\" \\\n    --silent --max-time 5 2>/dev/null || true\n\nexit 0'",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

## Logging and Analytics

### PostToolUse: Detailed Activity Logger
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, os\nfrom datetime import datetime\nfrom pathlib import Path\n\n# Create logs directory\nlogs_dir = os.path.expanduser('~/.claude/logs')\nos.makedirs(logs_dir, exist_ok=True)\n\n# Create daily log file\ntoday = datetime.now().strftime('%Y-%m-%d')\nlog_file = os.path.join(logs_dir, f'activity-{today}.jsonl')\n\ndata = json.load(sys.stdin)\n\n# Create log entry\nlog_entry = {\n    'timestamp': datetime.now().isoformat(),\n    'tool': data.get('tool_name', ''),\n    'cwd': data.get('cwd', ''),\n    'success': data.get('tool_response', {}).get('success', True)\n}\n\n# Add tool-specific details\nif log_entry['tool'] == 'Bash':\n    command = data.get('tool_input', {}).get('command', '')\n    log_entry['command'] = command[:100]  # Truncate long commands\nelif log_entry['tool'] in ['Write', 'Edit']:\n    file_path = data.get('tool_input', {}).get('file_path', '')\n    log_entry['file'] = os.path.basename(file_path)\n    log_entry['extension'] = Path(file_path).suffix\nelif log_entry['tool'] == 'Read':\n    file_path = data.get('tool_input', {}).get('file_path', '')\n    log_entry['file'] = os.path.basename(file_path)\n\n# Write to log file\nwith open(log_file, 'a') as f:\n    f.write(json.dumps(log_entry) + '\\n')\n\nsys.exit(0)\n\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### Stop: Generate Daily Summary
```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, os\nfrom datetime import datetime\nfrom collections import Counter\n\n# Get today's log file\nlogs_dir = os.path.expanduser('~/.claude/logs')\ntoday = datetime.now().strftime('%Y-%m-%d')\nlog_file = os.path.join(logs_dir, f'activity-{today}.jsonl')\n\nif not os.path.exists(log_file):\n    sys.exit(0)\n\n# Read and analyze logs\nactivities = []\nwith open(log_file, 'r') as f:\n    for line in f:\n        if line.strip():\n            activities.append(json.loads(line))\n\nif not activities:\n    sys.exit(0)\n\n# Generate summary\nsummary = {\n    'date': today,\n    'total_operations': len(activities),\n    'tools_used': Counter(a['tool'] for a in activities),\n    'files_modified': sum(1 for a in activities if a['tool'] in ['Write', 'Edit']),\n    'languages': Counter(\n        a.get('extension', 'unknown') \n        for a in activities \n        if a.get('extension')\n    ),\n    'first_activity': activities[0]['timestamp'],\n    'last_activity': activities[-1]['timestamp']\n}\n\n# Print human-readable summary\nprint('📊 Today\\'s Activity Summary:', file=sys.stderr)\nprint(f\"  Total operations: {summary['total_operations']}\", file=sys.stderr)\nprint(f\"  Files modified: {summary['files_modified']}\", file=sys.stderr)\nprint(\"  Top tools:\", file=sys.stderr)\nfor tool, count in summary['tools_used'].most_common(5):\n    print(f\"    {tool}: {count}\", file=sys.stderr)\n\nif summary['languages']:\n    print(\"  Languages:\", file=sys.stderr)\n    for lang, count in summary['languages'].most_common():\n        print(f\"    {lang or 'no extension'}: {count}\", file=sys.stderr)\n\n# Save summary for analytics\nsummary_file = os.path.join(logs_dir, f'summary-{today}.json')\nwith open(summary_file, 'w') as f:\n    json.dump(summary, f, indent=2)\n\nsys.exit(0)\n\"",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

## Health and Status Monitoring

### SessionStart: Environment Health Check
```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"\nimport json, sys, os, subprocess\nimport shutil\nfrom datetime import datetime\n\n# System health check\ndef check_command(cmd, name):\n    if shutil.which(cmd):\n        print(f'  ✅ {name}', file=sys.stderr)\n        return True\n    else:\n        print(f'  ❌ {name} not found', file=sys.stderr)\n        return False\n\ndef check_disk_space():\n    import shutil\n    total, used, free = shutil.disk_usage(os.path.expanduser('~'))\n    free_gb = free // (1024**3)\n    \n    if free_gb < 1:\n        print(f'  ⚠️ Low disk space: {free_gb}GB free', file=sys.stderr)\n        return False\n    else:\n        print(f'  ✅ Disk space: {free_gb}GB free', file=sys.stderr)\n        return True\n\nprint('🏥 Environment Health Check:', file=sys.stderr)\n\n# Check essential tools\nessential = ['git', 'python3', 'node']\nessential_ok = sum(check_command(cmd, cmd) for cmd in essential)\n\n# Check optional tools\noptional = {\n    'uv': 'Python package manager',\n    'bun': 'JavaScript runtime',\n    'docker': 'Container runtime',\n    'make': 'Build tool',\n    'gh': 'GitHub CLI'\n}\n\nprint('\\n🔧 Optional Tools:', file=sys.stderr)\nfor cmd, desc in optional.items():\n    check_command(cmd, desc)\n\n# Check system resources\nprint('\\n💾 System Resources:', file=sys.stderr)\ncheck_disk_space()\n\n# Check Claude Code specific directories\nclaude_dir = os.path.expanduser('~/.claude')\nif os.path.exists(claude_dir):\n    size = sum(\n        os.path.getsize(os.path.join(dirpath, filename))\n        for dirpath, dirnames, filenames in os.walk(claude_dir)\n        for filename in filenames\n    )\n    size_mb = size // (1024**2)\n    print(f'  📂 Claude data: {size_mb}MB', file=sys.stderr)\n    \n    if size_mb > 1000:\n        print('  💡 Consider running claude --cleanup', file=sys.stderr)\n\nprint('\\n✅ Health check complete', file=sys.stderr)\n\nsys.exit(0)\n\"",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
```

## Complete Monitoring Setup

### All-in-One Monitoring Configuration
```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "permission_prompt|idle_prompt",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/desktop-notify.sh",
            "timeout": 5
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/log-activity.sh",
            "timeout": 5
          },
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/track-metrics.sh",
            "timeout": 5
          }
        ]
      },
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/slack-notify.sh",
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
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/generate-summary.sh",
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
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/health-check.sh",
            "timeout": 15
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/session-report.sh",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

Create `.claude/hooks/desktop-notify.sh`:
```bash
#!/bin/bash
# Desktop notification hook
input=$(cat)
message=$(echo "$input" | jq -r '.message // empty')
notification_type=$(echo "$input" | jq -r '.notification_type // empty')

# Send notification based on platform
case "$OSTYPE" in
    darwin*)
        osascript -e "display notification \"$message\" with title \"Claude Code\" subtitle \"$notification_type\""
        # Play sound for permission prompts
        if [[ "$notification_type" == "permission_prompt" ]]; then
            afplay /System/Library/Sounds/Glass.aiff 2>/dev/null &
        fi
        ;;
    linux*)
        if command -v notify-send &> /dev/null; then
            urgency="normal"
            [[ "$notification_type" == "permission_prompt" ]] && urgency="critical"
            notify-send -u "$urgency" "Claude Code" "$message"
        fi
        ;;
esac

exit 0
```

Create `.claude/hooks/log-activity.sh`:
```bash
#!/bin/bash
# Activity logging hook
LOG_DIR="$HOME/.claude/logs"
mkdir -p "$LOG_DIR"

LOG_FILE="$LOG_DIR/activity-$(date +%Y-%m-%d).jsonl"

# Read input and create log entry
input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name // empty')
timestamp=$(date -Iseconds)

# Create basic log entry
cat >> "$LOG_FILE" << EOF
{"timestamp": "$timestamp", "tool": "$tool_name"}
EOF

exit 0
```

Create `.claude/hooks/track-metrics.sh`:
```bash
#!/bin/bash
# Metrics tracking hook
METRICS_FILE="$HOME/.claude/metrics.json"

input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name // empty')

# Simple metrics tracking
if [[ ! -f "$METRICS_FILE" ]]; then
    echo '{"tools_used": {}}' > "$METRICS_FILE"
fi

# Increment tool count
tmp=$(mktemp)
jq --arg tool "$tool_name" '.tools_used[$tool] += 1' "$METRICS_FILE" > "$tmp"
mv "$tmp" "$METRICS_FILE"

exit 0
```

Create `.claude/hooks/slack-notify.sh`:
```bash
#!/bin/bash
# Slack notification hook (requires SLACK_WEBHOOK_URL env var)
WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"

[[ -z "$WEBHOOK_URL" ]] && exit 0

input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name // empty')
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

if [[ "$tool_name" =~ ^(Write|Edit)$ ]]; then
    project=$(basename "$(pwd)")
    action=$([[ "$tool_name" == "Write" ]] && echo "created" || echo "modified")

    curl -X POST "$WEBHOOK_URL" \
        -H 'Content-Type: application/json' \
        -d "{\"text\": \"Claude Code $action $(basename "$file_path") in $project\"}" \
        --silent --max-time 5 2>/dev/null || true
fi

exit 0
```

Create `.claude/hooks/generate-summary.sh`:
```bash
#!/bin/bash
# Daily summary generation
LOG_DIR="$HOME/.claude/logs"
TODAY=$(date +%Y-%m-%d)
LOG_FILE="$LOG_DIR/activity-$TODAY.jsonl"

[[ ! -f "$LOG_FILE" ]] && exit 0

# Count operations
total=$(wc -l < "$LOG_FILE")
echo "📊 Today's activity: $total operations" >&2

# Top tools
echo "Top tools:" >&2
jq -r '.tool' "$LOG_FILE" | sort | uniq -c | sort -nr | head -5 | while read count tool; do
    echo "  $tool: $count" >&2
done

exit 0
```

Create `.claude/hooks/health-check.sh`:
```bash
#!/bin/bash
# Environment health check
echo "🏥 Health Check:" >&2

# Check essential tools
for cmd in git python3 node; do
    if command -v "$cmd" &> /dev/null; then
        echo "  ✅ $cmd" >&2
    else
        echo "  ❌ $cmd not found" >&2
    fi
done

# Check disk space
available=$(df -h ~ | awk 'NR==2 {print $4}')
echo "  💾 Disk space: $available available" >&2

exit 0
```

Create `.claude/hooks/session-report.sh`:
```bash
#!/bin/bash
# Session end report
echo "📈 Session Summary:" >&2

# Count today's activities
LOG_FILE="$HOME/.claude/logs/activity-$(date +%Y-%m-%d).jsonl"
if [[ -f "$LOG_FILE" ]]; then
    count=$(wc -l < "$LOG_FILE")
    echo "  Total operations: $count" >&2
fi

echo "✅ Session complete" >&2
exit 0
```