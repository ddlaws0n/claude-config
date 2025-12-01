# Custom Subagents Registry

This document provides a comprehensive registry of all custom subagents available in this Claude Code configuration. Each subagent is a specialized workflow designed to handle specific types of tasks efficiently.

## Subagent Overview

Subagents are task-specific Claude instances that operate with their own context window, tools, and instructions. Use them to:

- **Parallelize work**: Run multiple subagents simultaneously
- **Specialize expertise**: Each subagent has focused knowledge and constraints
- **Cost optimize**: Use smaller/faster models for specific tasks
- **Isolate context**: Keep large tasks separate from main conversation
- **Delegate workflows**: Hand off well-defined tasks to specialized agents

## Available Subagents

### 1. atomic-commits
**Model**: Haiku
**Purpose**: Creates atomic, well-organized git commits with conventional messages

**When to use**:
- You have staged changes that need to be committed logically
- You want to ensure commits follow conventional commit format
- You need clean, atomic commits for a specific feature or fix

**Capabilities**:
- Analyzes git status and diffs
- Proposes logical commit groupings
- Generates conventional commit messages (feat, fix, docs, style, refactor, test, chore, perf, ci)
- Executes commits with approval
- Follows best practices for commit history

**Key constraints**:
- Never mixes unrelated changes
- Never includes AI attribution
- Asks before push, reset, or revert
- Refuses force push and destructive operations

**Invocation**:
```
/Task atomic-commits
Create atomic commits for the staged changes. Group related modifications logically and ensure each commit message follows conventional commit format.
```

---

### 2. doc-specialist
**Model**: Haiku
**Purpose**: Creates, updates, and consolidates markdown documentation

**When to use**:
- Creating new documentation (CLAUDE.md, README.md, guides)
- Updating existing documentation to reflect changes
- Consolidating duplicate or scattered documentation
- Organizing documentation structure

**Capabilities**:
- Expert in CLAUDE.md memory files
- Understands AGENTS.md conventions
- Maintains README.md patterns
- Organizes docs/ directory effectively
- Applies DRY (Don't Repeat Yourself) principles
- Ensures internal documentation consistency

**Key expertise**:
- Documentation hierarchy and best practices
- Cross-references and linking
- Markdown formatting and structure
- Consolidation strategies

**Invocation**:
```
/Task doc-specialist
Create comprehensive documentation for the hook system including architecture decisions and configuration examples.
```

---

### 3. gemini-task-runner
**Model**: Haiku
**Purpose**: Executes specific tasks using Google's Gemini API

**When to use**:
- Need to offload specific tasks to Gemini for cost optimization
- Want to test Gemini's approach to a particular problem
- Need multi-model evaluation for decision-making

**Capabilities**:
- Integrates with Gemini API
- Handles task execution through alternative LLM
- Cost-conscious task delegation

**Invocation**:
```
/Task gemini-task-runner
Execute this analysis using Gemini API and report back results.
```

---

### 4. haiku-coder
**Model**: Haiku
**Purpose**: Fast, cost-effective general-purpose implementation agent

**When to use**:
- Delegating specific coding tasks (file modifications, implementations)
- Need quick turnaround on well-defined development work
- Want to optimize cost while maintaining code quality
- Breaking down complex features into implementation tasks

**Capabilities**:
- Writes clean, functional code
- Modifies existing files according to specifications
- Executes coding tasks efficiently
- Follows coding standards and project patterns
- Full tool access (Read, Write, Edit, Grep, Glob, Bash, Task)

**Best for**:
- Implementing specific functions or components
- Adding features to existing code
- Fixing bugs with clear reproduction steps
- Writing tests for existing functionality
- Refactoring isolated code sections

**Efficiency guidelines**:
- Prefers straightforward solutions
- Minimizes token usage without sacrificing quality
- Avoids over-analysis or unnecessary refactoring
- Fast execution without verbose explanations

**Invocation**:
```
/Task haiku-coder
Implement the `calculateTax` function in `src/utils/billing.js` according to the spec. Should handle US sales tax rates.
```

---

### 5. output-style-generator
**Model**: Haiku
**Purpose**: Creates custom output styles for system-wide behavior modifications

**When to use**:
- Want Claude to behave differently across all interactions (teaching mode, expert persona, communication style)
- Need persistent behavioral modifications
- Creating domain-specific interaction patterns (data scientist, lawyer, teacher)

**Capabilities**:
- Generates output style definitions
- Creates system prompts for behavior modification
- Designs teaching/explanation modes
- Develops domain-specific interaction patterns

**Key features**:
- System-wide effect (affects main conversation)
- Persistent across session
- Fundamental behavior changes
- Available globally through `/output-style` command

**Invocation**:
```
/Task output-style-generator
Create an output style that makes Claude explain its reasoning as it codes, showing thought process for each step.
```

---

### 6. skill-generator
**Model**: Haiku
**Purpose**: Creates complex, multi-file Agent Skills with progressive disclosure

**When to use**:
- Building comprehensive capabilities with multiple components
- Need organized knowledge with templates and scripts
- Creating team-standardized workflows
- Capabilities requiring multiple files or resources

**Capabilities**:
- Generates SKILL.md structure
- Creates reference documentation
- Designs multi-file skill organization
- Produces example workflows and templates
- Includes validation scripts

**Key features**:
- Multi-file structure with organization
- Progressive disclosure of complexity
- Automatic discovery by Claude
- Team-standardized workflows
- Persistent capabilities

**Invocation**:
```
/Task skill-generator
Create a code review Skill with security checklist, performance patterns, and linter integration.
```

---

### 7. slash-command-generator
**Model**: Haiku
**Purpose**: Creates custom slash commands for frequently-used prompts

**When to use**:
- Building quick, reusable prompts
- Creating command shortcuts for common tasks
- Simple one-file workflows
- Manual/explicit invocation needs

**Capabilities**:
- Generates slash command markdown files
- Implements argument handling ($ARGUMENTS, $1, $2, etc.)
- Integrates bash command execution
- Supports file references and thinking mode
- Manages frontmatter and metadata

**Key features**:
- Single markdown file per command
- Quick, frequently-used prompts
- Manual invocation (explicit `/command`)
- Project or personal scope
- Simple implementation

**Invocation**:
```
/Task slash-command-generator
Create a `/review-security` command that checks code for vulnerabilities and OWASP compliance.
```

---

### 8. subagent-generator
**Model**: Haiku
**Purpose**: Creates custom subagent definitions for task-specific workflows

**When to use**:
- Need specialized agents for specific domains or tasks
- Want to create task-specific context isolation
- Building complex workflows with delegated tasks
- Creating expert personas for specific domains

**Capabilities**:
- Generates subagent configuration files
- Defines specialized instructions and constraints
- Configures tool access and permissions
- Sets up model and behavior parameters
- Documents capabilities and use cases

**Key features**:
- Task-specific context isolation
- Specialized expertise and constraints
- Separate from main conversation
- Parallel execution capability
- Efficient delegation pattern

**Invocation**:
```
/Task subagent-generator
Create a security-specialist subagent for conducting security reviews and threat modeling.
```

---

### 9. workflow-orchestrator
**Model**: Sonnet
**Purpose**: Orchestrates creation of all Claude Code workflow components

**When to use**:
- User wants to create custom workflows but isn't sure what type
- Need guidance on choosing between Skills, Subagents, Commands, or Styles
- Building complex multi-component workflows
- Enterprise workflow standardization

**Capabilities**:
- Analyzes requirements and recommends approach
- Determines appropriate workflow component(s)
- Delegates to specialized generators
- Guides combination strategies
- Provides best-practice recommendations

**Key features**:
- Highest-level orchestration
- Intelligent recommendations
- Multi-component workflow creation
- Expert guidance on design choices
- Full coordination with other subagents

**Process**:
1. Understands user requirements
2. Asks clarifying questions if needed
3. Recommends workflow type(s)
4. Delegates to appropriate generator
5. Coordinates creation of related components

**Invocation**:
```
/Task workflow-orchestrator
I want to build automated code review capabilities that run on every PR. What should I create and how should it work?
```

---

## Subagent Selection Guide

### Quick Task Implementation
Use **haiku-coder** for:
- Implementing specific functions
- Modifying files
- Adding features
- Writing tests

### Creating Custom Workflows
Use **workflow-orchestrator** to determine if you need:
- **slash-command-generator** → Quick, manual prompts
- **skill-generator** → Complex, multi-file capabilities
- **subagent-generator** → Task-specific, isolated workflows
- **output-style-generator** → System-wide behavior changes

### Documentation & Knowledge
Use **doc-specialist** for:
- Creating/updating CLAUDE.md
- Building README files
- Consolidating documentation
- Organizing docs/ structure

### Git Operations
Use **atomic-commits** for:
- Committing staged changes
- Clean commit history
- Conventional commits

### Administrative
Use **subagent-generator** or **output-style-generator** for:
- Creating domain-specific personas
- Building specialized workflows
- Standardizing team processes

---

## How Subagents Work

### Invocation
All subagents are invoked using the Task tool:

```
/Task subagent-name
Task description and context here.
```

### Context Isolation
Each subagent:
- Gets fresh context window
- Has defined tool access
- Operates independently from main conversation
- Can be run in parallel with others

### Model Selection
- **Haiku**: Fast, cost-effective (most subagents)
- **Sonnet**: Complex reasoning (workflow-orchestrator)

### Tool Access
Each subagent has specific tools configured for its purpose. See individual subagent docs for details.

---

## Subagent Relationships & Workflows

### Creation Workflow
```
User → workflow-orchestrator →
  ├→ slash-command-generator
  ├→ skill-generator
  ├→ subagent-generator
  └→ output-style-generator
```

### Implementation Workflow
```
Main Claude → haiku-coder →
  └→ (other subagents as needed for specialized tasks)
```

### Documentation Workflow
```
Any task → doc-specialist →
  └→ (updates/creates documentation)
```

### Git Workflow
```
Changes → atomic-commits →
  └→ (clean commit history)
```

---

## Best Practices

### When to Use Subagents
- **Complex features**: Break into implementation tasks for haiku-coder
- **Specialized work**: Use domain experts (security, performance, docs)
- **Cost optimization**: Use Haiku subagents for straightforward tasks
- **Parallel work**: Run multiple subagents simultaneously
- **Isolation**: Keep large tasks separate from main conversation

### When NOT to Use Subagents
- Simple tasks you can handle directly
- Tasks requiring full context awareness
- Interactive/iterative work in main conversation
- Quick fixes and debugging
- First-time exploration of unfamiliar code

### Creating Effective Tasks
**Good task for subagent**:
> "Implement the `calculateTax` function in `src/utils/billing.js` according to the spec in the requirements doc. Should handle US sales tax rates and return the calculated amount."

**Poor task** (too vague):
> "Improve the billing module"

**Poor task** (too complex for Haiku):
> "Redesign the entire authentication system with OAuth2, JWT, and refresh tokens"

---

## Maintenance & Updates

This registry should be updated whenever:
- New subagents are created (add entry to list)
- Subagent capabilities change (update description)
- Best practices evolve (update guidelines)
- Models or tools are updated (reflect changes)

For documentation updates, use the **doc-specialist** subagent.

---

## See Also

- **CLAUDE.md** - Configuration repository memory and context
- **README.md** - Hook system and configuration overview
- **docs/** - Comprehensive guides and references
- **/Task** - How to invoke subagents in Claude Code

