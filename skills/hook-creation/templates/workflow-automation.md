# Workflow Automation Hook Templates

Templates for hooks that automate real-world development workflows beyond code quality, including Git operations, monorepo management, multi-environment handling, CI/CD integration, and development server management.

## 1. Git Workflow Patterns

### PreToolUse: Auto-Commit Message Generation

Generate semantic commit messages based on staged changes to guide conventional commits:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [""]
# ///
"""
Auto-generate commit message suggestions based on staged changes.
Suggests conventional commit format: type(scope): description
"""

import json
import subprocess
import sys
from pathlib import Path

def get_staged_files():
    """Get list of staged files."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=False
        )
        return result.stdout.strip().split('\n') if result.stdout else []
    except Exception:
        return []

def get_changed_dirs(files):
    """Extract directory names (scopes) from changed files."""
    scopes = set()
    for f in files:
        if '/' in f:
            # Use top-level directory as scope
            scopes.add(f.split('/')[0])
        else:
            # Use filename without extension as scope
            scopes.add(Path(f).stem)
    return sorted(scopes)[:3]  # Limit to 3 scopes

def determine_type(files):
    """Determine commit type based on changed files."""
    type_indicators = {
        'test': 'test',
        'spec': 'test',
        'docs': 'docs',
        'README': 'docs',
        'CHANGELOG': 'chore',
        'package.json': 'chore',
        'tsconfig': 'chore',
        'src': 'feat',
    }

    for f in files:
        for indicator, type_name in type_indicators.items():
            if indicator.lower() in f.lower():
                return type_name

    return 'feat'

def main():
    # Only process if this is a git repo
    if not Path('.git').exists():
        sys.exit(0)

    try:
        input_data = json.load(sys.stdin)

        # Only process Bash tool calls that look like git commit attempts
        if input_data.get("tool_name") != "Bash":
            sys.exit(0)

        command = input_data.get("tool_input", {}).get("command", "")
        if "git commit" not in command:
            sys.exit(0)

        staged_files = get_staged_files()
        if not staged_files or staged_files == ['']:
            sys.exit(0)

        commit_type = determine_type(staged_files)
        scopes = get_changed_dirs(staged_files)
        scope_str = f"({', '.join(scopes)})" if scopes else ""

        print(f"💡 Suggested commit type: {commit_type}{scope_str}", file=sys.stderr)
        print(f"   Example: git commit -m \"{commit_type}{scope_str}: brief description\"", file=sys.stderr)

    except Exception as e:
        # Fail open
        print(f"⚠️  Commit suggestion skipped: {e}", file=sys.stderr)

    sys.exit(0)

if __name__ == "__main__":
    main()
```

### PreToolUse: Branch Naming Enforcement

Validate branch names against naming conventions before committing:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [""]
# ///
"""
Enforce branch naming conventions.
Blocks commits on invalid branch names.
"""

import json
import re
import subprocess
import sys

def get_current_branch():
    """Get the current branch name."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=False
        )
        return result.stdout.strip()
    except Exception:
        return None

def validate_branch_name(branch):
    """
    Validate branch name against conventional patterns.
    Valid patterns:
    - feature/description
    - bugfix/description
    - hotfix/description
    - release/version
    - chore/description
    - main
    - develop
    - staging
    """
    if branch in ["main", "master", "develop", "staging", "production"]:
        return True, None

    # Pattern: type/description
    pattern = r"^(feature|bugfix|hotfix|release|chore|docs|refactor)/[a-z0-9\-]+$"
    if re.match(pattern, branch):
        return True, None

    return False, (
        f"❌ Invalid branch name: '{branch}'\n"
        f"   Expected format: type/description\n"
        f"   Valid types: feature, bugfix, hotfix, release, chore, docs, refactor\n"
        f"   Example: feature/user-authentication"
    )

def main():
    try:
        input_data = json.load(sys.stdin)

        if input_data.get("tool_name") != "Bash":
            sys.exit(0)

        command = input_data.get("tool_input", {}).get("command", "")
        if "git commit" not in command and "git push" not in command:
            sys.exit(0)

        branch = get_current_branch()
        if not branch:
            sys.exit(0)

        is_valid, message = validate_branch_name(branch)

        if not is_valid:
            print(message, file=sys.stderr)
            sys.exit(2)  # Block with error

        print(f"✅ Branch name valid: {branch}", file=sys.stderr)

    except Exception as e:
        print(f"⚠️  Branch validation skipped: {e}", file=sys.stderr)

    sys.exit(0)

if __name__ == "__main__":
    main()
```

### Stop: Pre-Push Validation

Comprehensive checks before git push:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [""]
# ///
"""
Pre-push validation hook.
Runs comprehensive checks before allowing git push.
"""

import json
import subprocess
import sys

def run_command(cmd, description):
    """Run a command and return success status."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            print(f"✅ {description}", file=sys.stderr)
            return True
        else:
            print(f"❌ {description} failed", file=sys.stderr)
            if result.stderr:
                print(f"   {result.stderr[:200]}", file=sys.stderr)
            return False
    except Exception as e:
        print(f"⚠️  {description} error: {e}", file=sys.stderr)
        return True  # Don't block on tool errors

def main():
    checks_passed = []
    checks_failed = []

    print("🔍 Running pre-push validation checks...\n", file=sys.stderr)

    # 1. Check for uncommitted changes
    if run_command(["git", "diff", "--quiet"], "No uncommitted changes"):
        checks_passed.append("uncommitted")
    else:
        checks_failed.append("uncommitted")

    # 2. Check branch exists on remote
    result = subprocess.run(
        ["git", "branch", "-r"],
        capture_output=True,
        text=True,
        check=False
    )

    # 3. Run tests if test script exists
    result = subprocess.run(
        ["npm", "test"],
        cwd=".",
        capture_output=True,
        text=True,
        check=False
    )
    if result.returncode == 0:
        print(f"✅ Tests passed", file=sys.stderr)
        checks_passed.append("tests")
    else:
        print(f"⚠️  Tests skipped or not configured", file=sys.stderr)

    # 4. Verify commit messages format
    result = subprocess.run(
        ["git", "log", "origin/main..HEAD", "--pretty=format:%B"],
        capture_output=True,
        text=True,
        check=False
    )

    if checks_failed:
        print(f"\n⚠️  Some checks failed. Push may be rejected.\n", file=sys.stderr)
        sys.exit(0)  # Don't block, let server decide

    print(f"\n✅ Pre-push checks complete. Ready to push!\n", file=sys.stderr)
    sys.exit(0)

if __name__ == "__main__":
    main()
```

### Protected Branch Detection

Configuration-based hook to block direct commits to protected branches:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash -c '\ninput=$(cat)\ncommand=$(echo \"$input\" | jq -r \".tool_input.command // empty\")\n\nif [[ \"$command\" == *\"git commit\"* ]] || [[ \"$command\" == *\"git push\"* ]]; then\n    branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo \"\")\n    \n    # Check if on protected branch\n    if [[ \"$branch\" == \"main\" ]] || [[ \"$branch\" == \"master\" ]] || [[ \"$branch\" == \"production\" ]]; then\n        # Check if trying to push directly (not from PR)\n        if [[ \"$command\" == *\"git push\"* ]] && [[ \"$GITHUB_REF\" == \"\" ]]; then\n            echo \"🚫 Direct push to protected branch blocked: $branch\" >&2\n            echo \"   Please create a pull request instead.\" >&2\n            exit 2  # Block\n        fi\n    fi\nfi\nexit 0'",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

---

## 2. Monorepo Handling

### Affected Package Detection

Detect which packages/workspaces were affected by changes:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [""]
# ///
"""
Detect affected packages in monorepo based on changed files.
Supports npm workspaces, yarn workspaces, pnpm workspaces, and turborepo.
"""

import json
import subprocess
from pathlib import Path
from typing import Set

def get_changed_files() -> Set[str]:
    """Get list of changed files in working directory."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
            check=False
        )
        return set(result.stdout.strip().split('\n')) if result.stdout else set()
    except Exception:
        return set()

def get_workspace_packages() -> dict:
    """Detect workspace structure from package.json or pnpm-workspace.yaml."""
    packages = {}

    # Check npm/yarn workspaces
    if Path('package.json').exists():
        try:
            with open('package.json') as f:
                data = json.load(f)
                if 'workspaces' in data:
                    workspaces = data['workspaces']
                    if isinstance(workspaces, list):
                        for ws in workspaces:
                            pattern = ws.replace('*', '')
                            for pkg_dir in Path('.').glob(ws):
                                if (pkg_dir / 'package.json').exists():
                                    with open(pkg_dir / 'package.json') as pf:
                                        pkg_data = json.load(pf)
                                        name = pkg_data.get('name', pkg_dir.name)
                                        packages[name] = str(pkg_dir)
        except Exception:
            pass

    # Check pnpm workspaces
    if Path('pnpm-workspace.yaml').exists():
        try:
            import yaml
            with open('pnpm-workspace.yaml') as f:
                data = yaml.safe_load(f)
                if 'packages' in data:
                    for pattern in data['packages']:
                        pattern_clean = pattern.replace('!', '').replace('*', '')
                        for pkg_dir in Path('.').glob(pattern):
                            if (pkg_dir / 'package.json').exists():
                                with open(pkg_dir / 'package.json') as pf:
                                    pkg_data = json.load(pf)
                                    name = pkg_data.get('name', pkg_dir.name)
                                    packages[name] = str(pkg_dir)
        except Exception:
            pass

    # Check turborepo
    if Path('turbo.json').exists():
        try:
            with open('turbo.json') as f:
                data = json.load(f)
                # turborepo uses the same workspaces config from root package.json
                if Path('package.json').exists():
                    with open('package.json') as pf:
                        pkg_data = json.load(pf)
                        if 'workspaces' in pkg_data:
                            for ws in pkg_data['workspaces']:
                                for pkg_dir in Path('.').glob(ws):
                                    if (pkg_dir / 'package.json').exists():
                                        with open(pkg_dir / 'package.json') as wpf:
                                            wpkg = json.load(wpf)
                                            name = wpkg.get('name', pkg_dir.name)
                                            packages[name] = str(pkg_dir)
        except Exception:
            pass

    return packages

def get_affected_packages(changed_files: Set[str], packages: dict) -> Set[str]:
    """Determine which packages are affected by changes."""
    affected = set()

    for pkg_name, pkg_path in packages.items():
        pkg_prefix = pkg_path.rstrip('/') + '/'

        # Check if any changed file is in this package
        for file in changed_files:
            if file.startswith(pkg_prefix):
                affected.add(pkg_name)
                break

    # Also check for root-level changes that affect all packages
    root_files = {f for f in changed_files if '/' not in f}
    if root_files and any(f in ['package.json', 'pnpm-workspace.yaml', 'turbo.json', 'lerna.json'] for f in root_files):
        # Root config changed - all packages affected
        affected.update(packages.keys())

    return affected

def main():
    try:
        packages = get_workspace_packages()
        if not packages:
            # Not a monorepo
            sys.exit(0)

        changed_files = get_changed_files()
        affected = get_affected_packages(changed_files, packages)

        if affected:
            print("📦 Affected packages:", file=sys.stderr)
            for pkg in sorted(affected):
                print(f"   • {pkg} ({packages[pkg]})", file=sys.stderr)

            # Set environment variable for downstream tools
            print(f"AFFECTED_PACKAGES={'|'.join(sorted(affected))}", file=sys.stderr)

    except Exception as e:
        print(f"⚠️  Affected packages detection failed: {e}", file=sys.stderr)

    sys.exit(0)

if __name__ == "__main__":
    main()
```

### Targeted Build and Test Execution

Only build and test affected packages:

```bash
#!/bin/bash
# PostToolUse hook: Run tests for affected packages only

set -e

input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

if [[ ! "$file_path" ]]; then
    exit 0
fi

# Detect workspace type
if [[ -f "pnpm-workspace.yaml" ]]; then
    PKG_MANAGER="pnpm"
elif [[ -f "package.json" ]] && grep -q '"workspaces"' package.json; then
    PKG_MANAGER="npm"
elif [[ -f "turbo.json" ]]; then
    PKG_MANAGER="turbo"
else
    # Not a monorepo
    exit 0
fi

# Extract package directory from file path
IFS='/' read -r pkg_dir rest <<< "$file_path"

echo "🧪 Running tests for affected package: $pkg_dir" >&2

case "$PKG_MANAGER" in
    pnpm)
        # Run tests only in affected workspace
        if [[ -f "$pkg_dir/package.json" ]]; then
            pnpm --filter "$pkg_dir" test 2>/dev/null || true
        fi
        ;;
    npm)
        # Use npm workspaces filtering if available
        if [[ -f "$pkg_dir/package.json" ]]; then
            npm test --workspace="$pkg_dir" 2>/dev/null || true
        fi
        ;;
    turbo)
        # Use turbo to run tests in affected packages
        turbo run test --filter="$pkg_dir" 2>/dev/null || true
        ;;
esac

exit 0
```

### Dependency Graph Traversal

Validate changes don't break dependent packages:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [""]
# ///
"""
Validate dependent packages when changes are made.
Detects package dependencies and ensures changes don't break them.
"""

import json
from pathlib import Path
from collections import defaultdict, deque

def build_dependency_graph():
    """Build package dependency graph from workspace packages."""
    graph = defaultdict(set)  # pkg -> set of dependencies

    try:
        with open('package.json') as f:
            root_data = json.load(f)
            workspaces = root_data.get('workspaces', [])

            # Scan all workspace packages
            for ws_pattern in workspaces:
                pattern = ws_pattern.replace('*', '')
                for pkg_dir in Path('.').glob(ws_pattern):
                    if (pkg_dir / 'package.json').exists():
                        with open(pkg_dir / 'package.json') as pf:
                            pkg_data = json.load(pf)
                            pkg_name = pkg_data.get('name')

                            if not pkg_name:
                                continue

                            # Collect dependencies from all dependency types
                            for dep_type in ['dependencies', 'devDependencies', 'peerDependencies']:
                                for dep_name in pkg_data.get(dep_type, {}):
                                    # Check if this dep is another workspace package
                                    for dep_pkg_dir in Path('.').glob(ws_pattern):
                                        if (dep_pkg_dir / 'package.json').exists():
                                            with open(dep_pkg_dir / 'package.json') as dpf:
                                                dep_pkg = json.load(dpf)
                                                if dep_pkg.get('name') == dep_name:
                                                    graph[pkg_name].add(dep_name)

    except Exception as e:
        print(f"⚠️  Could not build dependency graph: {e}")

    return graph

def get_dependents(package_name, graph):
    """Get all packages that depend on the given package."""
    dependents = set()

    for pkg, deps in graph.items():
        if package_name in deps:
            dependents.add(pkg)
            # Recursively get dependents of dependents
            dependents.update(get_dependents(pkg, graph))

    return dependents

def main():
    try:
        input_data = json.load(sys.stdin)

        # Get the affected package from environment (set by earlier hook)
        affected_pkg = input_data.get("environment", {}).get("AFFECTED_PACKAGE")
        if not affected_pkg:
            sys.exit(0)

        graph = build_dependency_graph()
        dependents = get_dependents(affected_pkg, graph)

        if dependents:
            print(f"⚠️  Changes to '{affected_pkg}' may affect dependent packages:", file=sys.stderr)
            for dep in sorted(dependents):
                print(f"   • {dep}", file=sys.stderr)
            print(f"\n   Consider running tests for these packages as well.", file=sys.stderr)

    except Exception as e:
        print(f"⚠️  Dependency check skipped: {e}", file=sys.stderr)

    sys.exit(0)

if __name__ == "__main__":
    main()
```

---

## 3. Multi-Environment Handling

### Environment Detection and Validation

Detect environment from multiple sources and apply environment-specific policies:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [""]
# ///
"""
Detect current environment (dev/staging/prod) and apply policies.
Sources: env vars, git branch, config files, current node.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

def detect_environment() -> tuple[str, str]:
    """
    Detect environment from multiple sources.
    Returns: (environment, reason)
    """

    # 1. Check explicit environment variable
    if env := os.environ.get('APP_ENV'):
        return env, "from APP_ENV"

    if env := os.environ.get('NODE_ENV'):
        return env, "from NODE_ENV"

    # 2. Check git branch
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=False
        )
        branch = result.stdout.strip()

        if branch in ["main", "master"]:
            return "production", "from git branch (main)"
        elif branch == "develop":
            return "staging", "from git branch (develop)"
        elif branch.startswith("feature/") or branch.startswith("bugfix/"):
            return "development", "from git branch (feature/bugfix)"
    except Exception:
        pass

    # 3. Check .env file
    if Path('.env').exists():
        try:
            with open('.env') as f:
                for line in f:
                    if line.startswith('APP_ENV=') or line.startswith('NODE_ENV='):
                        env = line.split('=', 1)[1].strip()
                        return env, "from .env file"
        except Exception:
            pass

    # 4. Check config files
    if Path('config/environment.json').exists():
        try:
            with open('config/environment.json') as f:
                config = json.load(f)
                if env := config.get('environment'):
                    return env, "from config/environment.json"
        except Exception:
            pass

    # Default to development if nothing detected
    return "development", "default"

def get_environment_policy(env: str) -> dict:
    """Get policies for the detected environment."""
    policies = {
        "development": {
            "allow_force_push": True,
            "allow_direct_commit_to_main": False,
            "allow_uncommitted_changes": True,
            "require_tests": False,
            "require_code_review": False,
        },
        "staging": {
            "allow_force_push": False,
            "allow_direct_commit_to_main": False,
            "allow_uncommitted_changes": False,
            "require_tests": True,
            "require_code_review": True,
        },
        "production": {
            "allow_force_push": False,
            "allow_direct_commit_to_main": False,
            "allow_uncommitted_changes": False,
            "require_tests": True,
            "require_code_review": True,
            "require_deployment_approval": True,
        },
    }

    return policies.get(env, policies["development"])

def validate_configuration(env: str, policy: dict) -> bool:
    """Validate that required environment variables are set."""
    required_vars = {
        "production": ["API_KEY", "DATABASE_URL", "SECRET_KEY"],
        "staging": ["API_KEY", "DATABASE_URL"],
        "development": [],
    }

    missing = []
    for var in required_vars.get(env, []):
        if not os.environ.get(var):
            missing.append(var)

    if missing:
        print(f"❌ Missing required env vars for {env}:", file=sys.stderr)
        for var in missing:
            print(f"   • {var}", file=sys.stderr)
        return False

    return True

def main():
    try:
        env, reason = detect_environment()
        policy = get_environment_policy(env)

        print(f"🌍 Environment: {env} ({reason})", file=sys.stderr)
        print(f"   Policy: Tests required={policy['require_tests']}, Code review required={policy['require_code_review']}", file=sys.stderr)

        # Validate configuration
        if not validate_configuration(env, policy):
            if env == "production":
                print(f"❌ Cannot proceed in production without required configuration", file=sys.stderr)
                sys.exit(2)  # Block
            else:
                print(f"⚠️  Configuration incomplete, but continuing in {env}", file=sys.stderr)

        # Set environment info in output for other hooks
        print(f"DETECTED_ENV={env}", file=sys.stderr)
        print(f"ENV_POLICY={json.dumps(policy)}", file=sys.stderr)

    except Exception as e:
        print(f"⚠️  Environment detection failed: {e}", file=sys.stderr)

    sys.exit(0)

if __name__ == "__main__":
    main()
```

### Production Safety Block

Block dangerous operations in production environments:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash -c '\ninput=$(cat)\ncommand=$(echo \"$input\" | jq -r \".tool_input.command // empty\")\nenv=$(echo \"$DETECTED_ENV\" | tr '[:upper:]' '[:lower:]')\n\n# List of dangerous commands in production\ndangerous_cmds=(\n    \"rm -rf\"\n    \"git reset --hard\"\n    \"git push --force\"\n    \"DROP DATABASE\"\n    \"DELETE FROM\"\n    \"truncate\"\n)\n\nif [[ \"$env\" == \"production\" ]]; then\n    for danger in \"${dangerous_cmds[@]}\"; do\n        if [[ \"$command\" == *\"$danger\"* ]]; then\n            echo \"🚫 Dangerous command blocked in PRODUCTION: $danger\" >&2\n            echo \"   This operation is not allowed in production.\" >&2\n            echo \"   If absolutely necessary, use manual deployment procedures.\" >&2\n            exit 2  # Block\n        fi\n    done\nfi\nexit 0'",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

---

## 4. CI/CD Integration Patterns

### Trigger CI Builds on Push

Automatically trigger CI builds and notify about status:

```bash
#!/bin/bash
# PostToolUse hook: Trigger CI builds when changes are pushed

set -e

input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // empty')

# Only trigger on git push
if [[ ! "$command" =~ ^git\ push ]]; then
    exit 0
fi

# Detect CI platform
if [[ -f ".github/workflows" ]]; then
    # GitHub Actions - push automatically triggers
    echo "✅ GitHub Actions will be triggered on push" >&2

    # Wait a moment and check commit status
    sleep 2
    if command -v gh &> /dev/null; then
        echo "🔍 Checking workflow status..." >&2
        gh run list --limit 1 2>/dev/null || true
    fi
fi

# GitLab CI
if [[ -f ".gitlab-ci.yml" ]]; then
    echo "✅ GitLab CI will be triggered on push" >&2
fi

# Jenkins
if [[ -f "Jenkinsfile" ]]; then
    echo "✅ Jenkins pipeline configured (manual or webhook trigger)" >&2
fi

exit 0
```

### Update Issue Trackers

Auto-update GitHub/Jira issues when commits reference them:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = ["requests"]
# ///
"""
Auto-update issue trackers based on commit messages.
Supports: GitHub issues, Jira, Linear.
"""

import json
import re
import subprocess
import sys
from urllib.request import urlopen, Request

def extract_issue_refs(commit_message: str) -> list[str]:
    """Extract issue references from commit message."""
    patterns = [
        r'#(\d+)',                    # GitHub: #123
        r'(PROJ-\d+)',                # Jira: PROJ-123
        r'(LIN-\d+)',                 # Linear: LIN-123
        r'(closes|fixes|resolves)\s+#(\d+)',  # closes #123
    ]

    issues = []
    for pattern in patterns:
        matches = re.findall(pattern, commit_message, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                # Filter out action words
                issue = [m for m in match if m and not re.match(r'closes|fixes|resolves', m, re.IGNORECASE)]
                if issue:
                    issues.extend(issue)
            else:
                issues.append(match)

    return issues

def update_github_issue(issue_num: str, commit_sha: str):
    """Post commit to GitHub issue."""
    try:
        repo = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            check=False
        ).stdout.strip()

        # Extract owner/repo from URL
        match = re.search(r'github.com[:/](.+?)/(.+?)(?:\.git)?$', repo)
        if not match:
            return

        owner, reponame = match.groups()

        # Get commit message
        commit_msg = subprocess.run(
            ["git", "log", "-1", "--pretty=format:%B", commit_sha],
            capture_output=True,
            text=True,
            check=False
        ).stdout.strip()

        # Update issue (requires GitHub token in GITHUB_TOKEN env var)
        token = sys.argv.get('GITHUB_TOKEN', '')
        if not token:
            return

        print(f"💬 Would update GitHub issue #{issue_num} with commit {commit_sha[:7]}", file=sys.stderr)

    except Exception as e:
        print(f"⚠️  GitHub issue update failed: {e}", file=sys.stderr)

def update_jira_issue(issue_key: str, commit_sha: str):
    """Add comment to Jira issue."""
    try:
        jira_url = sys.argv.get('JIRA_URL', '')
        jira_user = sys.argv.get('JIRA_USER', '')
        jira_token = sys.argv.get('JIRA_TOKEN', '')

        if not all([jira_url, jira_user, jira_token]):
            return

        # Get commit info
        commit_msg = subprocess.run(
            ["git", "log", "-1", "--pretty=format:%B", commit_sha],
            capture_output=True,
            text=True,
            check=False
        ).stdout.strip()

        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=False
        ).stdout.strip()

        comment = f"Commit {commit_sha[:7]} on branch {branch}:\n{commit_msg}"

        print(f"💬 Would update Jira issue {issue_key} with commit reference", file=sys.stderr)

    except Exception as e:
        print(f"⚠️  Jira issue update failed: {e}", file=sys.stderr)

def main():
    try:
        # Get latest commit message
        result = subprocess.run(
            ["git", "log", "-1", "--pretty=format:%B"],
            capture_output=True,
            text=True,
            check=False
        )

        commit_msg = result.stdout.strip()
        commit_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False
        ).stdout.strip()

        issues = extract_issue_refs(commit_msg)

        if not issues:
            sys.exit(0)

        print(f"🔗 Found issue references: {', '.join(issues)}", file=sys.stderr)

        for issue in set(issues):
            if issue.startswith('#') or issue.isdigit():
                update_github_issue(issue.lstrip('#'), commit_sha)
            elif re.match(r'[A-Z]+-\d+', issue):
                update_jira_issue(issue, commit_sha)

    except Exception as e:
        print(f"⚠️  Issue tracker update failed: {e}", file=sys.stderr)

    sys.exit(0)

if __name__ == "__main__":
    main()
```

---

## 5. PreCompact Hook Examples

### Session Summary Before Compaction

Save conversation summary before context compaction:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [""]
# ///
"""
PreCompact hook: Generate session summary before conversation compaction.
Saves key context, decisions, and session analytics.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

def generate_session_summary(input_data: dict) -> str:
    """Generate summary of the session."""
    summary = []
    summary.append("# Session Summary\n")
    summary.append(f"Generated: {datetime.now().isoformat()}\n")

    # Extract conversation statistics
    if messages := input_data.get("conversation", {}).get("messages", []):
        summary.append(f"\n## Conversation Stats\n")
        summary.append(f"- Total messages: {len(messages)}\n")
        summary.append(f"- User messages: {len([m for m in messages if m.get('role') == 'user'])}\n")
        summary.append(f"- Assistant messages: {len([m for m in messages if m.get('role') == 'assistant'])}\n")

    # Extract key decisions and changes
    if changes := input_data.get("files_changed", []):
        summary.append(f"\n## Files Changed ({len(changes)})\n")
        for file in changes[:10]:  # Limit to first 10
            summary.append(f"- {file}\n")
        if len(changes) > 10:
            summary.append(f"- ... and {len(changes) - 10} more\n")

    # Extract tools used
    if tools := input_data.get("tools_used", []):
        summary.append(f"\n## Tools Used\n")
        tool_counts = {}
        for tool in tools:
            tool_counts[tool] = tool_counts.get(tool, 0) + 1
        for tool, count in sorted(tool_counts.items(), key=lambda x: -x[1]):
            summary.append(f"- {tool}: {count} times\n")

    # Extract decisions made
    if decisions := input_data.get("decisions", []):
        summary.append(f"\n## Key Decisions\n")
        for decision in decisions[:5]:
            summary.append(f"- {decision}\n")

    summary.append(f"\n## Compaction Note\n")
    summary.append(f"This session is being compacted. See above for key context.\n")

    return "".join(summary)

def save_session_archive(session_id: str, summary: str) -> bool:
    """Save session summary to archive."""
    try:
        archive_dir = Path("/Users/dlawson/.claude/session-archives")
        archive_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        archive_file = archive_dir / f"session-{session_id}-{timestamp}.md"

        archive_file.write_text(summary)
        print(f"📦 Session archived: {archive_file}", file=sys.stderr)
        return True
    except Exception as e:
        print(f"⚠️  Failed to archive session: {e}", file=sys.stderr)
        return False

def main():
    try:
        input_data = json.load(sys.stdin)

        # Only process on actual compaction
        if input_data.get("hook_type") != "PreCompact":
            sys.exit(0)

        session_id = input_data.get("session_id", "unknown")
        summary = generate_session_summary(input_data)

        # Print summary
        print(summary, file=sys.stderr)

        # Archive session
        if save_session_archive(session_id, summary):
            print(f"✅ Session context preserved before compaction", file=sys.stderr)

    except Exception as e:
        print(f"⚠️  Session summary failed: {e}", file=sys.stderr)

    sys.exit(0)

if __name__ == "__main__":
    main()
```

### Session Report Generation

Generate detailed session analytics and exports:

```bash
#!/bin/bash
# PreCompact hook: Generate comprehensive session report

set -e

# Session report directory
REPORT_DIR="${HOME}/.claude/session-reports"
mkdir -p "$REPORT_DIR"

SESSION_ID="${CLAUDE_SESSION_ID:-unknown}"
TIMESTAMP=$(date +"%Y-%m-%d-%H:%M:%S")
REPORT_FILE="$REPORT_DIR/session-$SESSION_ID-$TIMESTAMP.txt"

{
    echo "=== CLAUDE CODE SESSION REPORT ==="
    echo "Session ID: $SESSION_ID"
    echo "Generated: $TIMESTAMP"
    echo ""

    echo "=== FILES MODIFIED ==="
    git status --short 2>/dev/null || echo "Not a git repository"
    echo ""

    echo "=== GIT LOG ==="
    git log --oneline -10 2>/dev/null || echo "Not a git repository"
    echo ""

    echo "=== SESSION STATISTICS ==="
    echo "Current directory: $(pwd)"
    echo "User: $(whoami)"
    echo "Platform: $(uname -s)"

} > "$REPORT_FILE"

echo "📄 Session report saved: $REPORT_FILE" >&2
exit 0
```

---

## 6. Development Server Management

### Auto-Start Dev Servers When Needed

Intelligently start development servers based on context:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [""]
# ///
"""
Auto-start development server when needed (e.g., when editing frontend code).
Uses the duplicate_process_blocker pattern to prevent duplicates.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

def should_start_server(file_path: str) -> bool:
    """Determine if a dev server should be started based on changed file."""
    frontend_patterns = [
        r'\.tsx?$',      # TypeScript/JavaScript
        r'\.jsx?$',
        r'\.vue$',       # Vue
        r'\.svelte$',    # Svelte
        r'\.css$',       # Styles
        r'\.scss$',
        r'\.less$',
        r'public/',      # Static assets
        r'src/pages',    # Next.js pages
    ]

    import re
    return any(re.search(pattern, file_path) for pattern in frontend_patterns)

def detect_dev_server_command() -> str | None:
    """Detect the appropriate dev server command for this project."""
    commands = [
        ("next.json", "next dev"),
        ("vite.config", "vite"),
        ("webpack.config", "webpack-dev-server"),
        ("nuxt.config", "nuxt dev"),
        ("tailwind.config", "npm run dev"),
    ]

    for config_file, cmd in commands:
        # Check for config file
        for pkg_file in Path('.').glob(f"**/{config_file}.*"):
            if pkg_file.exists():
                return cmd

    # Check package.json for dev script
    if Path('package.json').exists():
        try:
            with open('package.json') as f:
                pkg = json.load(f)
                if 'dev' in pkg.get('scripts', {}):
                    return "npm run dev"
        except Exception:
            pass

    return None

def is_server_running(server_cmd: str) -> bool:
    """Check if a dev server is already running."""
    try:
        # Use the duplicate_process_blocker pattern
        result = subprocess.run(
            ["~/.claude/hooks/duplicate_process_blocker.py", "--status"],
            capture_output=True,
            text=True,
            check=False
        )
        return server_cmd.lower() in result.stdout.lower()
    except Exception:
        return False

def start_server_background(server_cmd: str) -> bool:
    """Start dev server in background."""
    try:
        # Use nohup to detach from current shell
        subprocess.Popen(
            f"{server_cmd} > /tmp/dev-server.log 2>&1",
            shell=True,
            preexec_fn=os.setsid
        )
        print(f"🚀 Started dev server: {server_cmd}", file=sys.stderr)
        return True
    except Exception as e:
        print(f"⚠️  Failed to start dev server: {e}", file=sys.stderr)
        return False

def main():
    try:
        input_data = json.load(sys.stdin)

        # Only process Write/Edit operations
        tool_name = input_data.get("tool_name")
        if tool_name not in ["Edit", "Write"]:
            sys.exit(0)

        file_path = input_data.get("tool_input", {}).get("file_path", "")
        if not should_start_server(file_path):
            sys.exit(0)

        # Check if user has enabled auto-start
        if not os.environ.get("CLAUDE_AUTO_START_DEV_SERVER"):
            sys.exit(0)

        # Detect server command
        server_cmd = detect_dev_server_command()
        if not server_cmd:
            sys.exit(0)

        # Check if already running
        if is_server_running(server_cmd):
            print(f"✅ Dev server already running: {server_cmd}", file=sys.stderr)
            sys.exit(0)

        # Start server
        start_server_background(server_cmd)

    except Exception as e:
        print(f"⚠️  Auto-start dev server failed: {e}", file=sys.stderr)

    sys.exit(0)

if __name__ == "__main__":
    main()
```

### Port Conflict Resolution

Detect and resolve port conflicts intelligently:

```bash
#!/bin/bash
# Hook: Detect port conflicts and suggest alternatives

set -e

input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // empty')

# Extract port from command if present
port=$(echo "$command" | grep -oP '(?:--port|:)\K\d+' | head -1)

if [[ -z "$port" ]]; then
    exit 0
fi

# Check if port is in use
if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port $port is already in use" >&2

    # Find what's using it
    process=$(lsof -i :$port -t 2>/dev/null | head -1)
    if [[ ! -z "$process" ]]; then
        echo "   Process running: $(ps -p "$process" -o comm=)" >&2
    fi

    # Suggest alternatives
    echo "💡 Available alternatives:" >&2
    for alt_port in $((port+1)) $((port+2)) $((port+100)); do
        if ! lsof -Pi :$alt_port -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo "   • Port $alt_port is available" >&2
            if [[ "$command" == *"--port=$port"* ]]; then
                suggested="${command/--port=$port/--port=$alt_port}"
                echo "   Try: $suggested" >&2
            fi
        fi
    done
fi

exit 0
```

### Health Check and Recovery

Monitor dev server health and auto-restart if needed:

```bash
#!/bin/bash
# PostToolUse hook: Check dev server health

set -e

input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // empty')

# Only check health when actually using the server
if [[ ! "$command" =~ (curl|fetch|http|localhost|127.0.0.1) ]]; then
    exit 0
fi

# Extract port if present
port=$(echo "$command" | grep -oP '(?::)\K\d+' | head -1 || echo "3000")

# Health check endpoint patterns
endpoints=("/health" "/api/health" "/__health" "/status" "/")

server_up=false

for endpoint in "${endpoints[@]}"; do
    if curl -sf "http://localhost:$port$endpoint" > /dev/null 2>&1; then
        server_up=true
        break
    fi
done

if $server_up; then
    echo "✅ Dev server is healthy on port $port" >&2
else
    echo "⚠️  Dev server may not be responding on port $port" >&2
    echo "   Try: npm run dev (or your dev command)" >&2
fi

exit 0
```

---

## Configuration Examples

### Complete Workflow Automation Setup

Add to `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "/Users/dlawson/.claude/hooks/branch-validator.py",
            "timeout": 5
          },
          {
            "type": "command",
            "command": "/Users/dlawson/.claude/hooks/environment-detector.py",
            "timeout": 5
          },
          {
            "type": "command",
            "command": "/Users/dlawson/.claude/hooks/production-safety.sh",
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
            "command": "/Users/dlawson/.claude/hooks/monorepo-detector.py",
            "timeout": 10
          },
          {
            "type": "command",
            "command": "/Users/dlawson/.claude/hooks/auto-start-dev-server.py",
            "timeout": 10
          },
          {
            "type": "command",
            "command": "/Users/dlawson/.claude/hooks/port-health-check.sh",
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
            "command": "/Users/dlawson/.claude/hooks/pre-push-validation.py",
            "timeout": 30
          },
          {
            "type": "command",
            "command": "/Users/dlawson/.claude/hooks/issue-tracker-update.py",
            "timeout": 30
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/Users/dlawson/.claude/hooks/session-summary.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

### Environment Variables for Automation

Set these to enable features:

```bash
# Enable auto-start of dev servers
export CLAUDE_AUTO_START_DEV_SERVER=1

# Git workflow
export GIT_ENFORCE_BRANCH_NAMES=1
export GIT_AUTO_COMMIT_MESSAGES=1

# Monorepo
export DETECT_AFFECTED_PACKAGES=1
export RUN_AFFECTED_TESTS=1

# CI/CD
export TRIGGER_CI_BUILDS=1
export UPDATE_ISSUE_TRACKERS=1
export GITHUB_TOKEN="your_token_here"

# Environment detection
export APP_ENV="development"
export JIRA_URL="https://your-jira.atlassian.net"
export JIRA_USER="your-email@example.com"
export JIRA_TOKEN="your-token-here"

# Development server
export DEV_SERVER_PORT=3000
export DEV_SERVER_TIMEOUT_MINUTES=10
```

---

## Testing Your Workflow Hooks

```bash
# Test a hook manually
cat > test_input.json << 'EOF'
{
  "tool_name": "Edit",
  "tool_input": {
    "file_path": "/path/to/file.ts"
  },
  "session_id": "test-session"
}
EOF

# Run the hook
cat test_input.json | /path/to/hook.py

# Check hook execution in Claude Code
# Use /hooks command to see registration and execution times
```

---

## Best Practices

1. **Fail Open**: All hooks should exit 0 on unexpected errors to avoid blocking workflows
2. **Fast Feedback**: Keep PostToolUse hooks fast (< 2 seconds typically)
3. **Deferred Validation**: Save heavy validation (tests, type checks) for Stop hooks
4. **Environment Aware**: Check environment before running destructive operations
5. **Logging**: Use stderr for all status messages and debugging
6. **Caching**: Cache expensive lookups (dependency graphs, workspace detection) when possible
7. **Testing**: Test hooks with real project configurations before deploying
8. **Documentation**: Document environment variables and policies clearly
