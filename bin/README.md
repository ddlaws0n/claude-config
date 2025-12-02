# Claude Code ETL

Extracts Claude Code conversation data from `~/.claude` into a queryable SQLite database.

## Quick Start

```bash
# Run ETL with incremental loading
uv run bin/etl.py

# Force re-process all files
uv run bin/etl.py --force

# Verbose output
uv run bin/etl.py --verbose
```

## Data Sources

The ETL extracts from 6 data sources in `~/.claude`:

| Source | Directory | Description |
|--------|-----------|-------------|
| `projects` | `projects/{encoded_path}/{session_id}.jsonl` | Conversation history (messages, tool uses, tool results) |
| `todos` | `todos/{parent_session}-agent-{ref_session}.json` | Task lists from conversations |
| `file-history` | `file-history/{session_id}/{hash}@v{version}` | File version snapshots |
| `history` | `history.jsonl` | Global session history log |
| `plans` | `plans/*.md` | Planning mode markdown outputs |
| `shell-snapshots` | `shell-snapshots/*.txt` | Shell environment captures |

## Database Schema

Output: `~/.local/share/claude/conversations.db`

### Core Tables

```
projects          → Workspace paths and metadata
sessions          → Conversation sessions per project
agents            → Subagents/sidechains within sessions
messages          → All conversation messages (user, assistant, system)
tool_uses         → Tool invocations (Bash, Read, Write, Edit, etc.)
tool_results      → Tool execution results
```

### Auxiliary Tables

```
todos             → Task items from todo files
file_versions     → File content snapshots
shell_snapshots   → Shell environment captures
history_log       → Global session history
plans             → Planning mode outputs
```

### ETL Tracking

```
etl_runs          → Run history with stats
etl_file_state    → File modification tracking for incremental loads
```

## CLI Options

```
--source DIR      Source directory (default: ~/.claude)
--db PATH         Database path (default: ~/.local/share/claude/conversations.db)
--force           Re-process all files (ignore incremental state)
--sources LIST    Comma-separated sources: projects,todos,file-history,history,plans,shell-snapshots
--verbose         Enable DEBUG logging
--dry-run         Count records without inserting
```

## Architecture

```
bin/
├── etl.py              # CLI entry point and orchestration
├── etl_database.py     # SQLite connection, schema init, batch operations
├── etl_extractors.py   # 6 extractor classes (one per data source)
├── etl_state.py        # Incremental loading state tracker
├── schema.sql          # Database DDL
└── README.md           # This file
```

### Extractor Classes

| Class | Source | Records |
|-------|--------|---------|
| `ProjectsExtractor` | projects/*.jsonl | sessions, agents, messages, tool_uses, tool_results |
| `TodosExtractor` | todos/*.json | todos |
| `FileHistoryExtractor` | file-history/**/* | file_versions |
| `HistoryLogExtractor` | history.jsonl | history_log |
| `PlansExtractor` | plans/*.md | plans |
| `ShellSnapshotsExtractor` | shell-snapshots/*.txt | shell_snapshots |

## Example Queries

```sql
-- Message count by session
SELECT s.id, COUNT(m.uuid) as msg_count
FROM sessions s
JOIN messages m ON m.session_id = s.id
GROUP BY s.id ORDER BY msg_count DESC LIMIT 10;

-- Most used tools
SELECT tool_name, COUNT(*) as uses
FROM tool_uses
GROUP BY tool_name ORDER BY uses DESC;

-- Token usage by model
SELECT model, SUM(input_tokens) as input, SUM(output_tokens) as output
FROM messages
WHERE model IS NOT NULL
GROUP BY model;

-- Recent sessions with project paths
SELECT p.path, s.id, s.started_at
FROM sessions s
JOIN projects p ON s.project_path = p.path
ORDER BY s.started_at DESC LIMIT 10;
```

## Data Model Notes

### Message Content

Messages have two content fields:
- `content_text` — Extracted text from message content
- `content_json` — Full JSON for complex content (arrays, nested objects)

**Why some messages have empty `content_text`:**
Assistant messages that only invoke tools (no accompanying text) will have empty `content_text`. The tool invocation details are stored in `tool_uses` table, linked by `message_uuid`.

### Tool Uses vs Tool Results

- `tool_uses` — Extracted from assistant messages with `type: "tool_use"` content blocks
- `tool_results` — Extracted from user messages with `type: "tool_result"` content blocks
- Linked via `tool_use_id` field

### Session Relationships

```
projects (1) ← (N) sessions (1) ← (N) agents
                              ↑
                    messages ──┘
```

## Incremental Loading

The ETL uses hybrid incremental loading:

1. **File state tracking** — Records `mtime` and `size` per file in `etl_file_state`
2. **Skip unchanged** — Files with same mtime+size are skipped
3. **INSERT OR IGNORE** — Duplicate records are silently skipped
4. **Force mode** — `--force` bypasses file state but not INSERT OR IGNORE

To fully reset:
```bash
rm ~/.local/share/claude/conversations.db
uv run bin/etl.py
```

## Performance

Typical run on ~5,700 files:
- **Incremental**: 1-5 seconds (only changed files)
- **Full reload**: 15-30 seconds
