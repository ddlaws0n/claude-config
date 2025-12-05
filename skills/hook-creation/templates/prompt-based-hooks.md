# Prompt-Based Hooks Guide

Comprehensive guide for leveraging LLM-powered intelligent decision-making in Claude Code hooks.

## Table of Contents

1. [What Are Prompt-Based Hooks?](#what-are-prompt-based-hooks)
2. [When to Use Prompt vs Command Hooks](#when-to-use-prompt-vs-command-hooks)
3. [How Prompt-Based Hooks Work](#how-prompt-based-hooks-work)
4. [Response Schema Reference](#response-schema-reference)
5. [Complete Examples by Event Type](#complete-examples-by-event-type)
6. [Real-World Use Cases](#real-world-use-cases)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

## What Are Prompt-Based Hooks?

Prompt-based hooks (`type: "prompt"`) use an LLM (Haiku) to make intelligent, context-aware decisions instead of executing command-line scripts. Rather than writing bash or Python logic, you provide:

1. **Prompt template**: A natural language instruction that guides the LLM's decision
2. **Hook input**: Contextual data from Claude Code (tool name, file paths, recent changes, etc.)
3. **Response schema**: Structured JSON output the LLM must follow

The LLM analyzes the context and responds with structured decisions that control hook behavior.

### Key Advantages

- **Context-aware**: LLM understands nuance and can make sophisticated decisions
- **Fewer false positives**: Intelligent filtering vs rigid rule-based checks
- **Semantic understanding**: Can evaluate code quality, security risks, and policy compliance
- **Adaptable**: Easy to adjust behavior without code changes (just modify prompt)
- **Natural language**: Write requirements in English, not bash/Python

### Limitations

- **Latency**: LLM calls add 1-3 seconds vs immediate script execution
- **Cost**: Each hook invocation costs tokens
- **Dependency**: Requires API connectivity and valid credentials
- **Non-deterministic**: LLM responses can vary slightly between calls

## When to Use Prompt vs Command Hooks

| Aspect | Command Hooks | Prompt-Based Hooks |
|--------|---------------|--------------------|
| **Execution Speed** | Fast (ms) | Slower (1-3s) |
| **Cost** | Free (local) | Token cost per call |
| **Best For** | File formatting, linting, running tools | Intelligent decision-making |
| **Logic Complexity** | Script-based rules | Context-aware reasoning |
| **Examples** | `ruff format`, `prettier`, `pytest` | Approval decisions, policy checks |
| **Setup** | Executable script | Prompt template + schema |

### Decision Matrix

Use **Command Hooks** for:
- Automatically formatting files (PostToolUse)
- Running quick local tools
- Checking file existence or patterns
- Blocking obviously dangerous operations
- Notifications or logging

Use **Prompt-Based Hooks** for:
- Evaluating if work is complete (Stop)
- Making permission decisions (PreToolUse, PermissionRequest)
- Validating commit messages against standards
- Assessing code quality holistically
- Policy compliance checks that require context

## How Prompt-Based Hooks Work

### Execution Flow

```
┌─────────────────────────────────────┐
│  Claude Code Event (e.g., PreToolUse) │
└──────────────┬──────────────────────┘
               │
               ↓
        ┌──────────────┐
        │ Hook Matches │ (matcher condition met?)
        └──────┬───────┘
               │ (yes)
               ↓
    ┌──────────────────────┐
    │ Prepare Hook Input   │ (tool_name, tool_input, etc.)
    └──────┬───────────────┘
           │
           ↓
    ┌──────────────────────────┐
    │ Combine with Prompt      │ (merge context + template)
    └──────┬───────────────────┘
           │
           ↓
    ┌──────────────────────────┐
    │ Call Haiku LLM           │ (Haiku 4.5 model)
    └──────┬───────────────────┘
           │
           ↓
    ┌──────────────────────────┐
    │ Parse JSON Response      │ (validate schema)
    └──────┬───────────────────┘
           │
           ↓
    ┌──────────────────────────┐
    │ Execute Hook Decision    │ (approve/block/continue)
    └──────────────────────────┘
```

### Configuration Format

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Evaluate if all work is complete...",
            "responseSchema": {
              "decision": "string",
              "reason": "string"
            },
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

### Input Context Available

All prompt-based hooks receive input containing:

```json
{
  "session_id": "string",
  "transcript_path": "string",
  "cwd": "string",
  "permission_mode": "default|plan|acceptEdits|bypassPermissions",
  "hook_event_name": "PreToolUse|PostToolUse|Stop|PermissionRequest|UserPromptSubmit|SubagentStop",

  "tool_name": "string (tool being called)",
  "tool_input": { /* tool-specific parameters */ },
  "tool_response": { /* tool output (PostToolUse only) */ },
  "tool_use_id": "string",

  "recent_changes": [
    {
      "file": "path/to/file",
      "type": "edit|write|delete",
      "timestamp": "ISO8601"
    }
  ],

  "transcript_summary": "Summary of recent conversation",
  "error_context": "Any errors from tools or previous hooks"
}
```

## Response Schema Reference

Prompt-based hooks expect JSON responses with specific fields. All responses must include at minimum:

### Common Response Fields

```json
{
  "decision": "approve|block|continue",
  "reason": "Brief explanation of the decision",
  "continue": true,
  "stopReason": "Optional reason to stop execution"
}
```

### Decision Types

| Decision | Meaning | Use Cases |
|----------|---------|-----------|
| `approve` | Allow operation to proceed | PermissionRequest, PreToolUse |
| `block` | Prevent operation, show error | PreToolUse security check |
| `continue` | No action, pass through | PostToolUse, Stop hooks |

### Field Definitions

#### `decision` (required)
- Type: `string` (enum: `approve`, `block`, `continue`)
- Controls whether operation proceeds or is blocked
- For Stop hooks, typically use `continue` (decision made via stop behavior)

#### `reason` (required)
- Type: `string`
- Explanation of decision shown to user via stderr
- Should be clear and actionable
- Example: "Missing error handling in async function"

#### `continue` (optional, default: true)
- Type: `boolean`
- Whether to continue processing next hooks
- `false` stops remaining hooks in chain

#### `stopReason` (optional, for Stop hooks)
- Type: `string`
- Reason to prevent agent from stopping
- Only used in Stop hooks when work is incomplete

#### `systemMessage` (optional)
- Type: `string`
- Internal message for Claude Code logging
- Not shown to user, for debugging

### Response Schema Specification

When defining hooks, specify expected response structure:

```json
{
  "type": "prompt",
  "prompt": "...",
  "responseSchema": {
    "decision": { "type": "string", "enum": ["approve", "block", "continue"] },
    "reason": { "type": "string" },
    "continue": { "type": "boolean", "default": true },
    "stopReason": { "type": "string" }
  },
  "timeout": 30
}
```

The LLM must respond with valid JSON matching this schema.

## Complete Examples by Event Type

### 1. Stop Hook: Intelligent Work Completion Check

Use case: Prevent agent from stopping until all tasks complete, no console.logs remain, and tests pass.

#### Configuration

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "You are a code quality gate. Analyze the recent work and decide if it's ready to ship.\n\nContext:\n- Hook event: {hook_event_name}\n- Recent changes: {recent_changes}\n- CWD: {cwd}\n- Transcript summary: {transcript_summary}\n\nEvaluate:\n1. Are all requested tasks complete?\n2. Are there any console.log/debugger statements that should be removed?\n3. Are there any TODO/FIXME comments?\n4. Has the code been formatted and linted?\n5. Have tests been run and passed?\n\nRespond with JSON:\n{\n  \"decision\": \"approve\" if ready or \"block\" if more work needed,\n  \"reason\": \"Brief explanation\",\n  \"continue\": true\n}\n\nBe thorough but not overly strict. Small issues can be fixed later.",
            "responseSchema": {
              "decision": { "type": "string", "enum": ["approve", "block"] },
              "reason": { "type": "string" },
              "continue": { "type": "boolean" }
            },
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

#### How It Works

1. Agent finishes responding
2. Claude Code invokes Stop hook
3. Hook input includes all recent changes and transcript summary
4. Prompt template guides LLM to evaluate completion
5. LLM returns decision (approve or block)
6. If `block`, agent cannot stop; user must continue or force quit
7. If `approve`, agent stops normally

#### Example LLM Response

```json
{
  "decision": "block",
  "reason": "Found console.log statements in src/api/users.ts and test file wasn't mentioned as passing. Please remove debug statements and run tests.",
  "continue": true
}
```

---

### 2. SubagentStop Hook: Verify Subagent Task Completion

Use case: Ensure subagent completed its specific task before returning to main agent.

#### Configuration

```json
{
  "hooks": {
    "SubagentStop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Verify subagent task completion.\n\nContext:\n- Task assigned: {task_description}\n- Subagent work summary: {transcript_summary}\n- Files modified: {recent_changes}\n- Any errors: {error_context}\n\nDecide if the subagent successfully completed the assigned task.\n\nRespond with JSON:\n{\n  \"decision\": \"approve\" if complete, \"block\" if incomplete,\n  \"reason\": \"What was accomplished or what's missing\",\n  \"continue\": true\n}\n\nBe pragmatic - minor issues are acceptable if core task is done.",
            "responseSchema": {
              "decision": { "type": "string", "enum": ["approve", "block"] },
              "reason": { "type": "string" },
              "continue": { "type": "boolean" }
            },
            "timeout": 25
          }
        ]
      }
    ]
  }
}
```

#### Use Cases

- Implementing a feature sub-task
- Running tests for a component
- Refactoring a specific module
- Code review checklist validation

---

### 3. PreToolUse Hook: Context-Aware Permission Decision

Use case: Make intelligent permission decisions based on tool, inputs, and context.

#### Configuration

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Evaluate if tool use is safe and appropriate.\n\nTool: {tool_name}\nInput: {tool_input}\nContext: {transcript_summary}\nCurrent directory: {cwd}\n\nConsider:\n1. Is this a potentially dangerous command (e.g., recursive delete)?\n2. Is the user modifying sensitive files (.env, credentials, etc.)?\n3. Does the context suggest the tool use is intentional?\n4. Are proper safeguards in place?\n\nRespond with JSON:\n{\n  \"decision\": \"approve\" to allow or \"block\" to prevent,\n  \"reason\": \"Why you made this decision\",\n  \"continue\": true\n}\n\nBe permissive in general - block only obvious security issues.",
            "responseSchema": {
              "decision": { "type": "string", "enum": ["approve", "block"] },
              "reason": { "type": "string" },
              "continue": { "type": "boolean" }
            },
            "timeout": 20
          }
        ]
      }
    ]
  }
}
```

#### Example: Blocking Dangerous Commands

Input:
```json
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "rm -rf / --force"
  }
}
```

LLM Response:
```json
{
  "decision": "block",
  "reason": "Recursive delete from root filesystem would destroy the system. This is clearly unintended.",
  "continue": true
}
```

---

### 4. PermissionRequest Hook: Intelligent Auto-Approval

Use case: Approve routine operations automatically while requesting approval for risky ones.

#### Configuration

```json
{
  "hooks": {
    "PermissionRequest": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Determine if this action requires user approval or can be auto-approved.\n\nAction type: {permission_type}\nTool: {tool_name}\nDetails: {tool_input}\nContext: {transcript_summary}\n\nAuto-approve safe actions like:\n- Reading files for analysis\n- Running tests on modified files\n- Formatting code\n- Creating new files in appropriate directories\n\nRequest approval for:\n- Modifying files outside project scope\n- Bash commands (always require approval)\n- Large batch operations\n- Writing to sensitive paths\n\nRespond with JSON:\n{\n  \"decision\": \"approve\" or \"block\",\n  \"reason\": \"Explanation of decision\",\n  \"continue\": true\n}",
            "responseSchema": {
              "decision": { "type": "string", "enum": ["approve", "block"] },
              "reason": { "type": "string" },
              "continue": { "type": "boolean" }
            },
            "timeout": 15
          }
        ]
      }
    ]
  }
}
```

#### Approval Flow

1. Claude attempts restricted action
2. PermissionRequest hook fires
3. LLM analyzes whether action is routine or risky
4. Auto-approves safe actions (no user interaction)
5. Blocks risky actions (requires user confirmation)

---

### 5. UserPromptSubmit Hook: Intelligent Prompt Validation

Use case: Validate and critique user prompts before agent processing.

#### Configuration

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Review user prompt for clarity and feasibility.\n\nUser prompt: {user_input}\nProject context: {cwd}\nSession history: {transcript_summary}\n\nEvaluate:\n1. Is the request clear and specific?\n2. Is it feasible given project scope?\n3. Could it cause problems (dangerous operations)?\n4. Are there obvious dependencies or prerequisites?\n5. Would the request be better broken into smaller tasks?\n\nRespond with JSON:\n{\n  \"decision\": \"continue\" (allow processing),\n  \"reason\": \"Brief feedback\",\n  \"suggestions\": \"Optional improvements to the request\",\n  \"continue\": true\n}\n\nAlways respond with 'continue' - you're providing feedback, not blocking.",
            "responseSchema": {
              "decision": { "type": "string", "enum": ["continue"] },
              "reason": { "type": "string" },
              "suggestions": { "type": "string" },
              "continue": { "type": "boolean" }
            },
            "timeout": 25
          }
        ]
      }
    ]
  }
}
```

#### User Experience

```
User: "Build authentication"

Hook analysis suggests:
"This request is broad. Consider breaking it into:
1. Database schema for users
2. Login API endpoint
3. JWT token generation
4. Protected route middleware"

Agent proceeds with full request or adjusted based on feedback
```

---

### 6. PostToolUse Hook: Intelligent Post-Processing

Use case: Decide whether to run additional checks after file modifications.

#### Configuration

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Determine if post-processing checks are needed.\n\nFile modified: {tool_input.file_path}\nOperation: {tool_input.operation}\nFile type: {file_type}\nProject: {cwd}\n\nConsider running:\n- Format/lint checks for code files\n- Type checking for TypeScript/Python\n- Basic validation\n- Security scanning for sensitive operations\n\nRespond with JSON:\n{\n  \"decision\": \"continue\",\n  \"reason\": \"What checks should run\",\n  \"checksNeeded\": [\"format\", \"lint\", \"type\"],\n  \"continue\": true\n}",
            "responseSchema": {
              "decision": { "type": "string" },
              "reason": { "type": "string" },
              "checksNeeded": { "type": "array", "items": { "type": "string" } },
              "continue": { "type": "boolean" }
            },
            "timeout": 15
          }
        ]
      }
    ]
  }
}
```

---

## Real-World Use Cases

### Use Case 1: Code Quality Gate

**Goal**: Block agent from stopping until code meets standards.

**Prompt**:
```
You are a senior code reviewer. Analyze recent work and block if:
- Console.log/debugger statements present
- Comments with TODO/FIXME without explanation
- Functions without docstrings
- Missing test coverage
- Type errors

Only block if these are new issues introduced by this session.
```

**Benefits**:
- Catches common mistakes automatically
- Prevents regressions
- Saves code review time
- Improves code consistency

### Use Case 2: Security Policy Enforcement

**Goal**: Auto-approve safe actions, block policy violations.

**Prompt**:
```
Enforce security policy:
1. Allow file reads for analysis
2. Allow write to src/ and tests/ directories
3. Block writes to sensitive paths: .env, config/, secrets/
4. Block Bash commands that modify system files
5. Block usage of unsafe functions: eval(), exec()

Approve safe operations automatically.
Block violations and explain policy.
```

**Benefits**:
- Prevents accidental data exposure
- Enforces consistent practices
- Blocks before damage occurs
- Allows flexibility with override option

### Use Case 3: Team Workflow Standards

**Goal**: Enforce commit message format and PR requirements.

**Prompt**:
```
Validate commit message against team standards:
- Starts with type: fix|feat|refactor|docs|test|chore
- Format: "type(scope): description"
- Max 72 characters
- Lowercase
- No period at end

Validate PR requirements:
- At least 2 reviewers needed
- All tests passing
- No console.logs
- Updated changelog

Block if not met.
```

**Benefits**:
- Consistent commit history
- Enforced review process
- Automated pre-PR checks
- Searchable git log

### Use Case 4: Intelligent Resource Management

**Goal**: Prevent resource exhaustion, auto-approve efficient operations.

**Prompt**:
```
Evaluate resource impact:
- If running tests: auto-approve if < 10 files changed
- If Bash: ask for confirmation on long-running commands
- If processing large files: suggest chunking
- Auto-approve database queries that use indices

Block obviously inefficient operations.
```

**Benefits**:
- Prevents accidental resource exhaustion
- Suggests optimizations
- Maintains system health
- Provides performance feedback

---

## Best Practices

### 1. Be Specific in Prompts

**Bad**:
```
Check if this is good.
```

**Good**:
```
Verify all new code has docstrings, is type-annotated, and has no console.log statements.
Only block if new code violates these standards. Allow reasonable exceptions for simple utility functions.
```

### 2. Include Clear Decision Criteria

**Bad**:
```
Decide if the work is done.
```

**Good**:
```
Work is complete if:
1. All requested features are implemented (check transcript)
2. No console.log/debugger statements present
3. All new functions have docstrings
4. Tests have been run and mentioned as passing
5. No obvious bugs or incomplete logic

If ANY criterion fails, block.
```

### 3. Set Appropriate Timeouts

- **Quick decisions** (simple approval): 10-15s
- **Standard evaluation** (moderate complexity): 20-30s
- **Deep analysis** (comprehensive review): 30-45s
- **Complex decisions** (multiple factors): 45-60s

```json
{
  "type": "prompt",
  "prompt": "...",
  "timeout": 30  // Adjust based on complexity
}
```

### 4. Use Contextual Information Effectively

```
Prompt structure:
1. State the role/goal
2. Provide specific context
3. Enumerate decision criteria
4. Request JSON response
5. Include guardrails/flexibility notes
```

### 5. Balance Strictness vs Flexibility

**Too Strict** (blocks too much):
```
Block if ANY issue exists.
```

**Too Lenient** (approves too much):
```
Only block obvious security issues.
```

**Right Balance**:
```
Block new issues introduced this session.
Allow existing issues unless they're critical security problems.
Use judgment for edge cases.
```

### 6. Handle Missing Context Gracefully

```
"If transcript is unavailable or unclear,
use available signals (file types, recent changes)
and err on the side of approval."
```

### 7. Provide Actionable Feedback

**Poor**:
```
"Not ready"
```

**Good**:
```
"Contains 3 console.log statements in src/api/users.ts (lines 45, 67, 89).
Remove these and re-run."
```

### 8. Test Before Deployment

1. Create test hook configuration
2. Simulate hook input with sample data
3. Verify LLM response format
4. Check decision logic
5. Test edge cases

```bash
# Test prompt-based hook manually
cat > test_input.json << 'EOF'
{
  "hook_event_name": "Stop",
  "recent_changes": [...],
  "transcript_summary": "Added user authentication..."
}
EOF

# Run test (command-line test if available)
cat test_input.json | python test_hook.py
```

---

## Troubleshooting

### Hook Not Firing

**Symptom**: Prompt hook never executes.

**Solutions**:
1. Verify matcher condition (if PostToolUse/PreToolUse)
   ```json
   "matcher": "Edit|Write"  // Must match tool name
   ```

2. Check hook configuration JSON validity
   ```bash
   jq . .claude/settings.json
   ```

3. Restart Claude Code (settings snapshot at startup)

4. Check `hook_event_name` spelling exactly

---

### LLM Response Parse Error

**Symptom**: "Invalid response format" error.

**Solutions**:
1. Response schema must match exactly:
   ```json
   {
     "decision": "string value",
     "reason": "string value",
     "continue": true
   }
   ```

2. Verify all required fields are present

3. Test response with `jq`:
   ```bash
   echo '{"decision":"approve","reason":"OK","continue":true}' | jq .
   ```

4. Increase timeout to give LLM more time:
   ```json
   "timeout": 45
   ```

---

### LLM Response Unexpected

**Symptom**: LLM makes inconsistent or wrong decisions.

**Solutions**:
1. Make prompt more specific with examples
2. Add explicit decision criteria
3. Include guardrails: "Block ONLY if..."
4. Provide examples of good/bad cases
5. Test with multiple prompts to find clearest wording

---

### Hook Timeout

**Symptom**: Hook exceeds timeout consistently.

**Solutions**:
1. Increase timeout (but monitor costs)
2. Simplify prompt (fewer decision criteria)
3. Move to Stop hook if not time-critical
4. Use command hook instead if rule-based

---

### High Token Cost

**Symptom**: Prompt hooks consuming too many tokens.

**Solutions**:
1. Use command hooks for simple checks
2. Reduce prompt verbosity
3. Limit how often hook fires (matcher conditions)
4. Cache decisions where possible
5. Consider hybrid: command hook + selective prompt hooks

---

### Decision Logic Unclear

**Symptom**: "Why did it approve/block?" is unclear.

**Solutions**:
1. Always return detailed `reason` field
2. Include concrete examples in reason
3. Add decision context to `systemMessage`
4. Test with `claude --debug` to see full hook execution

---

## Configuration Template

Complete minimal example ready to customize:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "You are a code quality gate.\n\nContext:\n- Event: {hook_event_name}\n- Changes: {recent_changes}\n- Summary: {transcript_summary}\n\nDecide if work is complete and ready to ship.\n\nBlock ONLY if critical issues:\n- Incomplete implementation\n- Obvious bugs\n- Breaking changes\n\nRespond with JSON:\n{\n  \"decision\": \"continue\",\n  \"reason\": \"Explanation\",\n  \"continue\": true\n}",
            "responseSchema": {
              "decision": { "type": "string" },
              "reason": { "type": "string" },
              "continue": { "type": "boolean" }
            },
            "timeout": 30
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Evaluate if tool use is safe.\n\nTool: {tool_name}\nInput: {tool_input}\nContext: {cwd}\n\nBlock ONLY obvious security issues.\n\nRespond with JSON:\n{\n  \"decision\": \"approve\",\n  \"reason\": \"Why\",\n  \"continue\": true\n}",
            "responseSchema": {
              "decision": { "type": "string", "enum": ["approve", "block"] },
              "reason": { "type": "string" },
              "continue": { "type": "boolean" }
            },
            "timeout": 20
          }
        ]
      }
    ]
  }
}
```

---

## Summary

Prompt-based hooks enable intelligent, context-aware automation:

- **Stop hooks**: Quality gates and completion checks
- **PreToolUse hooks**: Permission decisions with context
- **PermissionRequest hooks**: Auto-approval for safe operations
- **SubagentStop hooks**: Verify subagent task completion
- **UserPromptSubmit hooks**: Validate and improve user input
- **PostToolUse hooks**: Intelligent post-processing decisions

Use them to enforce standards, improve security, and enable team workflows without rigid rule-based checks.
