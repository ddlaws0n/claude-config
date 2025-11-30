---
description: Create atomic commits with signing and push to origin
agent: atomic-commits
---

Analyze current changes and create atomic commits with conventional commit messages. Before committing:

1. Verify git commit signing is configured (check `git config --get commit.gpgsign`)
2. If not configured, warn user and ask if they want to proceed
3. Create atomic commits with proper conventional messages
4. After all commits are created successfully, push to origin

IMPORTANT: Ensure commits are properly signed if signing is enabled. Ask user before pushing.
