#!/bin/bash

# Post-tool-use hook: Tracks edited workspaces for batch processing later.
# Non-blocking, fail-safe.

# 1. Safety & Input
set -euo pipefail

# Validate dependencies
if ! command -v jq >/dev/null 2>&1; then
    echo "⚠️  Error: jq is required but not installed" >&2
    exit 0  # Fail gracefully
fi

# Read and validate input
tool_info=$(cat)
if [[ -z "$tool_info" ]]; then
    exit 0  # No input, nothing to track
fi

# Validate JSON structure
if ! echo "$tool_info" | jq . >/dev/null 2>&1; then
    echo "⚠️  Error: Invalid JSON input received" >&2
    exit 0  # Fail gracefully
fi

# 2. Extract Data (Use specific keys to avoid ambiguity)
# CLAUDE_PROJECT_DIR is injected by the environment, but fallback to CWD if missing
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# Normalize project root to absolute path
if [[ ! "$PROJECT_ROOT" = /* ]]; then
    PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"
fi

# Extract required fields with validation
tool_name=$(echo "$tool_info" | jq -r '.tool_name // empty')
raw_file_path=$(echo "$tool_info" | jq -r '.tool_input.file_path // empty')
session_id=$(echo "$tool_info" | jq -r '.session_id // "default"')

# Validate extracted data
if [[ -z "$tool_name" || -z "$raw_file_path" || -z "$session_id" ]]; then
    exit 0  # Missing required data
fi

# 3. Fast Exit Checks
[[ ! "$tool_name" =~ ^(Edit|MultiEdit|Write)$ ]] && exit 0

# Security: Validate file path format
if [[ "$raw_file_path" =~ \.\./|^\.\./ ]]; then
    echo "⚠️  Warning: Path traversal attempt detected: $raw_file_path" >&2
    exit 0  # Security protection
fi

# Skip non-code files
[[ "$raw_file_path" =~ \.(md|markdown|txt|json|lock|log)$ ]] && exit 0

# Normalize path to absolute, then calculate relative
if [[ "$raw_file_path" = /* ]]; then
  abs_path="$raw_file_path"
else
  abs_path="$PROJECT_ROOT/$raw_file_path"
fi

# Security: Resolve path traversal and normalize
abs_path="$(realpath -m "$abs_path" 2>/dev/null || echo "$abs_path")"

# Verify file exists and is within project bounds
if [[ ! -f "$abs_path" || ! "$abs_path" =~ ^"$PROJECT_ROOT"/ ]]; then
    exit 0  # File doesn't exist or outside project
fi

# Get relative path safely
rel_path="${abs_path#$PROJECT_ROOT/}"

# 4. Setup Cache
cache_dir="$PROJECT_ROOT/.claude/tsc-cache/$session_id"

# Security: Validate cache directory path
if [[ ! "$cache_dir" =~ ^"$PROJECT_ROOT"/\.claude/ ]]; then
    echo "⚠️  Error: Invalid cache directory path" >&2
    exit 0
fi

mkdir -p "$cache_dir" 2>/dev/null || {
    echo "⚠️  Warning: Failed to create cache directory: $cache_dir" >&2
    exit 0
}

# 5. Repo/Workspace Detection
detect_repo() {
    local path="$1"
    local root_folder=$(echo "$path" | cut -d'/' -f1)

    case "$root_folder" in
        # Standard Monorepo Structures
        packages|apps|libs|services|examples)
            local sub_folder=$(echo "$path" | cut -d'/' -f2)
            if [[ -n "$sub_folder" ]]; then
                echo "$root_folder/$sub_folder"
            else
                echo "$root_folder"
            fi
            ;;
        # Top-level known folders
        frontend|backend|client|server|web|api|database|prisma)
            echo "$root_folder"
            ;;
        # Root level files
        *)
            if [[ "$path" != *"/"* ]]; then
                echo "root"
            else
                echo "unknown" # Or return root_folder to be safe
            fi
            ;;
    esac
}

repo=$(detect_repo "$rel_path")
[[ "$repo" == "unknown" || -z "$repo" ]] && exit 0

repo_full_path="$PROJECT_ROOT/$repo"

# 6. Command Discovery (Aligned with your BUN/UV preference)
get_build_command() {
    local r_path="$1"

    # Prisma Special Case
    if [[ "$repo" == "database" || "$repo" == "prisma" ]]; then
        echo "cd $r_path && bun x prisma generate"
        return
    fi

    if [[ -f "$r_path/package.json" ]]; then
        # Check if build script exists safely
        if grep -q '"build":' "$r_path/package.json"; then
            echo "cd $r_path && bun run build"
            return
        fi
    fi
}

get_tsc_command() {
    local r_path="$1"

    if [[ -f "$r_path/tsconfig.json" ]]; then
        # Check for build-specific tsconfig
        if [[ -f "$r_path/tsconfig.build.json" ]]; then
            echo "cd $r_path && bun run tsc --project tsconfig.build.json --noEmit"
        elif [[ -f "$r_path/tsconfig.app.json" ]]; then
            echo "cd $r_path && bun run tsc --project tsconfig.app.json --noEmit"
        else
            echo "cd $r_path && bun run tsc --noEmit"
        fi
    fi
}

# 7. Logging (Atomic / Append Only with error handling)

# Function for safe atomic logging
safe_log() {
    local content="$1"
    local file="$2"

    # Security: Validate file path
    if [[ ! "$file" =~ ^"$cache_dir"/ && "$file" != "$cache_dir"/* ]]; then
        echo "⚠️  Error: Invalid log file path: $file" >&2
        return 1
    fi

    # Atomic write with error handling
    echo "$content" >> "$file" 2>/dev/null || {
        echo "⚠️  Warning: Failed to write to log file: $file" >&2
        return 1
    }
}

# Log the raw edit event
safe_log "$(date +%s):$rel_path:$repo" "$cache_dir/edited-files.log"

# Log the repo if not already in the "session set"
safe_log "$repo" "$cache_dir/affected-repos.log"

# Calculate commands
build_cmd=$(get_build_command "$repo_full_path" 2>/dev/null || echo "")
tsc_cmd=$(get_tsc_command "$repo_full_path" 2>/dev/null || echo "")

# Log discovered commands
if [[ -n "$build_cmd" ]]; then
    safe_log "$repo:build:$build_cmd" "$cache_dir/commands.log"
fi

if [[ -n "$tsc_cmd" ]]; then
    safe_log "$repo:tsc:$tsc_cmd" "$cache_dir/commands.log"
fi

# exit clean
exit 0
