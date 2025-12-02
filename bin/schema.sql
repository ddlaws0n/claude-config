-- ============================================================================
-- PROJECTS & SESSIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS projects (
    path TEXT PRIMARY KEY,              -- Unique project path
    name TEXT,
    git_origin TEXT,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_projects_last_seen ON projects(last_seen DESC);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,                -- UUID from sessionId
    project_path TEXT NOT NULL,
    cwd TEXT,
    git_branch TEXT,
    version TEXT,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    FOREIGN KEY (project_path) REFERENCES projects(path) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sessions_project ON sessions(project_path);
CREATE INDEX IF NOT EXISTS idx_sessions_started ON sessions(started_at DESC);

-- ============================================================================
-- AGENTS (SUBAGENTS/SIDECHAINS)
-- ============================================================================

CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,                -- agentId (8 hex chars)
    session_id TEXT NOT NULL,
    is_sidechain BOOLEAN DEFAULT FALSE,
    parent_message_uuid TEXT,
    first_seen TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_agents_session ON agents(session_id);

-- ============================================================================
-- MESSAGES (CONVERSATION HISTORY)
-- ============================================================================

CREATE TABLE IF NOT EXISTS messages (
    uuid TEXT PRIMARY KEY,              -- UUID from message
    parent_uuid TEXT,
    session_id TEXT NOT NULL,
    agent_id TEXT,
    timestamp TIMESTAMP NOT NULL,
    type TEXT NOT NULL,                 -- user, assistant, tool_use, tool_result, thinking

    -- Message content
    role TEXT,                          -- user, assistant
    content_text TEXT,                  -- Simple text content
    content_json TEXT,                  -- Complex content (JSON string)

    -- Assistant-specific
    model TEXT,
    message_id TEXT,                    -- Claude API message ID
    stop_reason TEXT,

    -- Token usage
    input_tokens INTEGER,
    output_tokens INTEGER,
    cache_creation_tokens INTEGER,
    cache_read_tokens INTEGER,

    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE SET NULL,
    FOREIGN KEY (parent_uuid) REFERENCES messages(uuid) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_messages_type ON messages(type);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp DESC);

-- ============================================================================
-- TOOL USAGE
-- ============================================================================

CREATE TABLE IF NOT EXISTS tool_uses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_uuid TEXT NOT NULL,
    tool_id TEXT NOT NULL,              -- Tool use ID from content block
    tool_name TEXT NOT NULL,            -- Bash, Read, Write, etc.
    input_json TEXT,
    FOREIGN KEY (message_uuid) REFERENCES messages(uuid) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_tool_uses_message ON tool_uses(message_uuid);
CREATE INDEX IF NOT EXISTS idx_tool_uses_name ON tool_uses(tool_name);

CREATE TABLE IF NOT EXISTS tool_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_uuid TEXT NOT NULL,
    tool_use_id TEXT NOT NULL,
    is_error BOOLEAN DEFAULT FALSE,
    content_preview TEXT,               -- First 1000 chars
    FOREIGN KEY (message_uuid) REFERENCES messages(uuid) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_tool_results_message ON tool_results(message_uuid);

-- ============================================================================
-- TODOS
-- ============================================================================

CREATE TABLE IF NOT EXISTS todos (
    id TEXT PRIMARY KEY,                -- Generated: {parent_session_id}-{ref_session_id}-{sequence}
    parent_session_id TEXT NOT NULL,    -- Parent session from filename (may not exist in sessions table)
    ref_session_id TEXT,                -- Referenced session from filename (may be same as parent)
    agent_id TEXT,                      -- Agent ID if found (8-char hex), nullable
    sequence INTEGER NOT NULL,
    content TEXT NOT NULL,
    active_form TEXT,
    status TEXT NOT NULL,               -- pending, in_progress, completed
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE SET NULL
    -- Note: No FK on parent_session_id - todos can exist for sessions not yet in DB
);

CREATE INDEX IF NOT EXISTS idx_todos_parent_session ON todos(parent_session_id);
CREATE INDEX IF NOT EXISTS idx_todos_ref_session ON todos(ref_session_id);

-- ============================================================================
-- FILE HISTORY
-- ============================================================================

CREATE TABLE IF NOT EXISTS file_versions (
    id TEXT PRIMARY KEY,                -- {session_id}/{file_hash}@v{version}
    session_id TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    version INTEGER NOT NULL,
    content TEXT NOT NULL,
    file_size INTEGER,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_file_versions_session ON file_versions(session_id);
CREATE INDEX IF NOT EXISTS idx_file_versions_hash ON file_versions(file_hash);

-- ============================================================================
-- SHELL SNAPSHOTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS shell_snapshots (
    id TEXT PRIMARY KEY,                -- snapshot-zsh-{timestamp}-{random}
    timestamp TIMESTAMP NOT NULL,
    shell_type TEXT,
    content TEXT NOT NULL,
    content_hash TEXT
);

CREATE INDEX IF NOT EXISTS idx_shell_snapshots_timestamp ON shell_snapshots(timestamp DESC);

-- ============================================================================
-- HISTORY LOG
-- ============================================================================

CREATE TABLE IF NOT EXISTS history_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP NOT NULL,
    project_path TEXT,
    display TEXT,
    FOREIGN KEY (project_path) REFERENCES projects(path) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_history_log_timestamp ON history_log(timestamp DESC);

-- ============================================================================
-- PLANS
-- ============================================================================

CREATE TABLE IF NOT EXISTS plans (
    filename TEXT PRIMARY KEY,
    agent_id TEXT,
    title TEXT,
    content TEXT NOT NULL,
    created_at TIMESTAMP,
    modified_at TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_plans_modified ON plans(modified_at DESC);

-- ============================================================================
-- ETL STATE TRACKING
-- ============================================================================

CREATE TABLE IF NOT EXISTS etl_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_timestamp TIMESTAMP NOT NULL,
    source TEXT NOT NULL,
    files_processed INTEGER DEFAULT 0,
    records_inserted INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    duration_seconds REAL,
    status TEXT                         -- success, partial, failed
);

CREATE INDEX IF NOT EXISTS idx_etl_runs_timestamp ON etl_runs(run_timestamp DESC);

CREATE TABLE IF NOT EXISTS etl_file_state (
    file_path TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    mtime TIMESTAMP NOT NULL,
    size INTEGER,
    last_processed TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_etl_file_state_source ON etl_file_state(source);
