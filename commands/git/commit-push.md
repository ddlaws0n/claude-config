---
description: Create atomic commits with signing and push to origin
model: claude-haiku-4-5-20251001
disable-model-invocation: true
---

Use the atomic-commits subagent to analyze current changes and create atomic commits with conventional commit messages. Before committing, verify git commit signing is configured by checking `git config --get commit.gpgsign`. If not configured, warn user and ask if they want to proceed. Create atomic commits with proper conventional messages, ensuring commits are properly signed if signing is enabled. After all commits are created successfully, ask user before pushing to origin.
