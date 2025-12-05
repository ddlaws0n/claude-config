---
description: Execute an approved plan by delegating tasks to haiku-coder subagents
argument-hint: [path/to/plan.md]
allowed-tools: Read, Grep, Glob
model: claude-sonnet-4-5-20250929
---

Act as project manager to execute the approved plan. Locate the plan at $ARGUMENTS if provided, otherwise check .claude/plan.md, plan.md, or use !`find . -maxdepth 2 -name "*plan*.md" -type f -mtime -7 | head -5`.

Read the plan thoroughly and break it into well-defined, self-contained tasks with clear scope, file paths, and success criteria. Note dependencies between tasks to determine ordering. Delegate each task to haiku-coder subagent with complete context including relevant plan section, files to modify, specific requirements, and validation criteria. Execute dependent tasks sequentially; independent tasks can proceed in sequence.

Track progress showing completed tasks with subagent IDs, in-progress work, pending tasks, and blockers. After completion, verify integration, run tests, and provide a summary covering tasks completed, files modified, any deviations from plan, and recommended next steps.

As orchestrator, delegate all implementation to haiku-coder. You manage coordination, quality, and communication - not coding.
