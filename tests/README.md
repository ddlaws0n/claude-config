# Claude Code Hooks Test Suite

A comprehensive pytest test suite for the Claude Code sound hooks system, focusing on high-quality tests for critical functionality rather than broad coverage.

## Test Architecture

This test suite follows a **strategic testing approach** with 57 tests across 4 main test files, each targeting specific aspects of the hook system:

### Test Files Overview

| File | Tests | Focus | Priority |
|------|-------|--------|----------|
| `test_sound_manager.py` | 26 | Core sound logic and mapping | **CRITICAL** |
| `test_error_handling.py` | 17 | Error resilience and failure scenarios | **HIGH** |
| `test_pattern_matching.py` | 11 | Bash command pattern recognition | **HIGH** |
| `test_hook_handlers.py` | 8 | Hook handler integration | **MEDIUM** |

## Test Categories

### 🔧 **Core Sound Logic** (`test_sound_manager.py`)
Tests the foundational `SoundManager` class that powers the entire hook system.

**Key Test Areas:**
- **Sound Mapping Resolution**: Event → sound file mapping (`Notification` → `ready.wav`)
- **Tool Sound Mapping**: Tool → sound file mapping (`Edit` → `edit.wav`)
- **Bash Pattern Matching**: Regex pattern matching for commands (`git commit` → `commit.wav`)
- **Project Overrides**: `.claude-sounds` file processing for custom mappings
- **Sound Playback**: macOS `afplay` integration with async execution

**Critical Tests:**
```python
test_event_sound_mapping_notification()  # Core event mapping
test_git_commit_pattern_matching()        # Pattern recognition  
test_project_override_loading()           # Custom configurations
test_play_sound_file_success()           # Sound playback
```

### 🚨 **Error Resilience** (`test_error_handling.py`)
Ensures the system handles all failure modes gracefully without blocking Claude Code operations.

**Failure Scenarios:**
- **Missing Files**: Sound files, configuration files, directories
- **Malformed Data**: Invalid JSON, broken configurations
- **Subprocess Failures**: `afplay` command failures, permission issues
- **System Edge Cases**: Empty commands, unicode text, concurrent execution

**Critical Tests:**
```python
test_missing_sound_mappings_file()       # Graceful config failure
test_malformed_sound_mappings_file()     # JSON parsing resilience
test_subprocess_popen_failure()          # Sound playback failure
test_concurrent_hook_execution_safety()  # Thread safety
```

### 🎯 **Pattern Matching** (`test_pattern_matching.py`)
Deep validation of bash command pattern recognition - the most complex part of the system.

**Pattern Categories:**
- **Git Commands**: `git commit`, `git push`, etc. → `commit.wav`
- **GitHub CLI**: `gh pr create`, `gh pr merge` → `pr.wav`
- **Test Runners**: `npm test`, `pytest`, `go test` → `test.wav`
- **Fallback**: Unknown commands → `bash.wav`

**Edge Cases:**
- **Complex Commands**: Pipes, redirects, chaining (`git commit | tee log.txt`)
- **Case Sensitivity**: `Git commit` should not match (fallback to `bash.wav`)
- **Unicode Support**: Commands with international characters
- **Pattern Precedence**: First-match-wins behavior validation

**Critical Tests:**
```python
test_git_commit_patterns_comprehensive()  # All git commit variations
test_pattern_precedence_order()           # Match order validation
test_complex_command_combinations()       # Real-world command complexity
```

### 🔗 **Integration Testing** (`test_hook_handlers.py`)
Tests actual hook handler executables with real cchooks contexts.

**Integration Points:**
- **Hook Execution**: Direct subprocess execution of hook handlers
- **JSON Input/Output**: Real Claude Code hook event processing  
- **Context Handling**: cchooks integration validation
- **Performance**: Sub-second execution requirements

**Critical Tests:**
```python
test_pre_tool_handler_git_commit()       # PreToolUse integration
test_post_tool_handler_write()          # PostToolUse integration
test_notification_handler()             # Notification integration
test_session_start_handler()            # SessionStart integration
```

## Test Configuration (`conftest.py`)

Provides fixtures and test infrastructure for comprehensive testing:

### **Real Hook Event Fixtures**
Based on actual Claude Code hook events from production testing:

```python
@pytest.fixture
def pre_tool_bash_commit_fixture():
    return {
        "session_id": "test-session-456",
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": "git commit -m \"Add feature\""}
    }
```

### **Mock Infrastructure**
- **Sound Directories**: Temporary directories with mock `.wav` files
- **Configuration Files**: Mock `sound_mappings.json` files
- **Subprocess Mocking**: Mock `afplay` calls for testing without audio

### **Testing Utilities**
- **Context Objects**: Mock cchooks contexts for isolated testing
- **Project Overrides**: Mock `.claude-sounds` files
- **Error Scenarios**: Controlled failure condition setup

## Running Tests

### **Full Suite**
```bash
uv run pytest tests/ -v
```

### **By Category**
```bash
# Core logic only
uv run pytest tests/test_sound_manager.py -v

# Error scenarios only  
uv run pytest tests/test_error_handling.py -v

# Pattern matching only
uv run pytest tests/test_pattern_matching.py -v

# Integration only
uv run pytest tests/test_hook_handlers.py -v
```

### **By Markers**
```bash
# Sound logic tests
uv run pytest -m sound_logic -v

# Integration tests
uv run pytest -m integration -v

# Error handling tests  
uv run pytest -m error_handling -v

# Performance tests
uv run pytest -m performance -v
```

## Test Strategy

### **Quality Over Coverage**
- **57 strategic tests** rather than 200+ shallow tests
- **Focus on critical failure modes** that would break the system
- **Real-world scenarios** based on actual Claude Code usage patterns

### **Failure Mode Testing**
- **Graceful Degradation**: Sound failures never block Claude Code
- **Error Resilience**: Invalid input handled safely
- **Edge Case Coverage**: Unicode, empty input, malformed data

### **Integration Validation**
- **Real Hook Execution**: Direct subprocess calls to actual hook handlers
- **Authentic Data**: Real Claude Code JSON event structures
- **End-to-End Testing**: Complete hook execution pipeline

## Technical Implementation

### **Modern Python Features**
- **Type Hints**: Full type safety with Python 3.12 syntax (`str | None`)
- **Path Handling**: `pathlib.Path` for cross-platform compatibility
- **Modern JSON**: Robust error handling and validation

### **Testing Best Practices**
- **Fixture Reuse**: Shared test infrastructure across files
- **Mock Strategy**: Mock external dependencies (subprocess) but not core logic
- **Isolation**: Each test runs independently with clean state

### **Performance Requirements**
- **Fast Execution**: Full suite runs in ~2 seconds
- **Parallel Safe**: Tests can run concurrently without interference
- **Resource Efficient**: Temporary files and directories cleaned up automatically

## Dependencies

- **pytest**: Test framework with fixtures and markers
- **pytest-mock**: Mocking utilities for subprocess calls
- **cchooks**: Claude Code hooks SDK integration
- **Python 3.12+**: Modern type hints and features

## Maintenance

### **Adding New Tests**
1. **Identify Category**: Core logic, error handling, pattern matching, or integration
2. **Use Existing Fixtures**: Leverage `conftest.py` fixtures when possible
3. **Follow Patterns**: Match existing test structure and naming conventions
4. **Add Markers**: Use appropriate pytest markers for categorization

### **Updating for Changes**
- **Sound Mappings**: Update `sound_mappings_data` fixture when patterns change
- **Hook Events**: Update fixtures when Claude Code hook schemas evolve
- **New Hook Types**: Add new fixtures and tests for additional hook handlers

### **Debugging Failures**
- **Verbose Output**: Use `pytest -v` for detailed test information
- **Single Test**: Run individual tests with `pytest tests/file.py::test_name`
- **Debug Mode**: Use `pytest -s` to see print statements and stdout