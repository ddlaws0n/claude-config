---
description: Sync current branch with default branch ahead of a PR
---

Compare the current non-default branch against the default branch (usually main or master) and help get it in sync for a pull request.

## Steps

1. **Identify branches**: Determine the current branch and default branch
2. **Fetch latest**: Fetch the latest from origin
3. **Compare commits**: Show commits on current branch not in default, and vice versa
4. **Check for conflicts**: Identify potential merge conflicts
5. **Recommend sync strategy**: Suggest rebase or merge based on the situation

## Commands to run

```bash
# Get current branch
git branch --show-current

# Get default branch
git remote show origin | grep "HEAD branch" | cut -d: -f2 | xargs

# Fetch latest
git fetch origin

# Show commits ahead (current branch has, default doesn't)
git log --oneline origin/<default>..HEAD

# Show commits behind (default has, current doesn't)  
git log --oneline HEAD..origin/<default>

# Check for potential conflicts
git diff --name-only origin/<default>...HEAD
```

## Sync options

After analysis, offer these options:
1. **Rebase** (preferred for clean history): `git rebase origin/<default>`
2. **Merge** (simpler, preserves history): `git merge origin/<default>`
3. **Interactive rebase** (for cleaning up commits): `git rebase -i origin/<default>`

Ask which approach the user prefers before executing any sync operation.

