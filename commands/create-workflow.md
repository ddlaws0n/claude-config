---
argument-hint: [description of workflow needed]
description: Create custom Skills, Subagents, Slash Commands, or Output Styles for Claude Code workflows
---

# Workflow Generator

Use the workflow-orchestrator subagent to create a workflow for: $ARGUMENTS

The workflow-orchestrator will:
1. Analyze your requirements
2. Ask clarifying questions if needed
3. Recommend the best workflow type(s)
4. Create the component(s) for you
5. Provide usage instructions

Available workflow types:
- **Output Styles**: System-wide behavior modifications
- **Skills**: Complex, multi-file capabilities with progressive disclosure
- **Subagents**: Task-specific workflows with separate context
- **Slash Commands**: Quick, frequently-used prompts
- **Combinations**: Multiple components working together
