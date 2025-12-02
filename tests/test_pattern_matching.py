"""
Critical pattern matching tests.

Focused tests for bash command pattern matching logic which is the most
complex and failure-prone part of the sound mapping system.

Tests edge cases, pattern precedence, and comprehensive regex validation
against all patterns defined in sound_mappings.json.
"""

import re
import sys
from pathlib import Path

import pytest

# Add hooks utils to path for imports
hooks_dir = Path(__file__).parent.parent / "hooks"
sys.path.insert(0, str(hooks_dir / "utils"))

from sound_manager import SoundManager


@pytest.mark.sound_logic
class TestBashPatternMatching:
    """Test bash command pattern matching with comprehensive coverage."""

    def test_git_commit_patterns_comprehensive(self, sound_manager_with_mock_sounds):
        """Test all variations of git commit commands."""
        git_commit_commands = [
            # Basic forms
            "git commit",
            "git commit -m 'message'",
            'git commit -m "message"',
            "git commit --message='message'",
            'git commit --message="message"',
            
            # With flags
            "git commit -am 'message'",
            "git commit -a -m 'message'", 
            "git commit --all -m 'message'",
            "git commit -s -m 'message'",  # signed
            "git commit --amend -m 'message'",
            
            # Multi-line messages
            'git commit -m "Line 1\nLine 2"',
            "git commit -F commit_message.txt",
            
            # Edge cases with paths and special chars
            "git commit -m 'Fix: handle $VAR expansion'",
            "git commit -m 'Add support for @mentions'",
        ]
        
        for command in git_commit_commands:
            sound_file = sound_manager_with_mock_sounds._get_bash_sound(command)
            assert sound_file is not None, f"No sound found for: {command}"
            assert sound_file.name == "commit.wav", f"Wrong sound for: {command}"

    def test_github_pr_patterns_comprehensive(self, sound_manager_with_mock_sounds):
        """Test all GitHub CLI PR command variations."""
        gh_pr_commands = [
            # Basic PR operations
            "gh pr create",
            "gh pr list",
            "gh pr view",
            "gh pr edit", 
            "gh pr merge",
            "gh pr close",
            "gh pr reopen",
            "gh pr review",
            
            # With arguments
            "gh pr create --title 'New feature'",
            "gh pr merge 123",
            "gh pr view --web",
            "gh pr list --state open",
            'gh pr create --body "Description here"',
            
            # Complex examples
            "gh pr create --title 'Fix bug' --body 'Long description' --draft",
            "gh pr merge 456 --squash --delete-branch",
        ]
        
        for command in gh_pr_commands:
            sound_file = sound_manager_with_mock_sounds._get_bash_sound(command)
            assert sound_file is not None, f"No sound found for: {command}"
            assert sound_file.name == "pr.wav", f"Wrong sound for: {command}"

    def test_test_runner_patterns_comprehensive(self, sound_manager_with_mock_sounds):
        """Test all test runner command variations."""
        test_commands = [
            # Commands that match the actual patterns in sound_mappings.json
            "npm test",
            "npm test -- --coverage",
            "yarn test", 
            "yarn test --watch",
            "pnpm test",
            "bun test",
            "pytest",
            "pytest tests/",
            "pytest -v",
            "go test",
            "go test ./...",
            "just test",
            
            # Ruby (from sound_mappings.json)
            "bundle exec rspec",
            "rspec",
            "bin/rspec",
        ]
        
        for command in test_commands:
            sound_file = sound_manager_with_mock_sounds._get_bash_sound(command)
            assert sound_file is not None, f"No sound found for: {command}"
            assert sound_file.name == "test.wav", f"Wrong sound for: {command}"

    def test_pattern_precedence_order(self, sound_manager_with_mock_sounds):
        """Test that patterns are matched in correct precedence order."""
        # git commit should match commit pattern, not fallback bash pattern
        command = "git commit -m 'test'"
        sound_file = sound_manager_with_mock_sounds._get_bash_sound(command)
        assert sound_file.name == "commit.wav"
        
        # gh pr should match pr pattern, not fallback
        command = "gh pr create"
        sound_file = sound_manager_with_mock_sounds._get_bash_sound(command) 
        assert sound_file.name == "pr.wav"
        
        # test commands should match test pattern, not fallback
        command = "npm test"
        sound_file = sound_manager_with_mock_sounds._get_bash_sound(command)
        assert sound_file.name == "test.wav"

    def test_fallback_pattern_coverage(self, sound_manager_with_mock_sounds):
        """Test that unmatched commands fall back to bash.wav."""
        unmatched_commands = [
            "ls -la",
            "cat file.txt",
            "grep pattern file",
            "find . -name '*.py'",
            "docker build -t image .",
            "kubectl get pods",
            "terraform plan",
            "ansible-playbook site.yml",
            "make build",
            "cargo build",
            "mvn clean install",
            "gradle test",
            "custom-command --special-flag",
        ]
        
        for command in unmatched_commands:
            sound_file = sound_manager_with_mock_sounds._get_bash_sound(command)
            assert sound_file is not None, f"Fallback failed for: {command}"
            assert sound_file.name == "bash.wav", f"Wrong fallback for: {command}"


@pytest.mark.sound_logic
class TestPatternEdgeCases:
    """Test edge cases and boundary conditions in pattern matching."""

    def test_empty_command_handling(self, sound_manager_with_mock_sounds):
        """Test behavior with empty or whitespace-only commands."""
        edge_commands = [
            "",
            " ",
            "\t",
            "\n",
            "   \t\n   ",
        ]
        
        for command in edge_commands:
            sound_file = sound_manager_with_mock_sounds._get_bash_sound(command)
            # Should either return bash.wav fallback or None
            if sound_file is not None:
                assert sound_file.name == "bash.wav"

    def test_complex_command_combinations(self, sound_manager_with_mock_sounds):
        """Test commands with pipes, redirects, and complex syntax."""
        complex_commands = [
            # Pipes - should still match first command
            "git commit -m 'test' | tee log.txt",
            "npm test | grep 'passing'",
            "gh pr create | jq '.url'",
            
            # Command chaining - should match first command
            "git commit -m 'test' && git push",
            "npm test; echo 'done'",
            "gh pr create || echo 'failed'",
            
            # Redirection - should still match main command  
            "git commit -m 'test' > commit.log 2>&1",
            "npm test > test_results.txt",
            
            # Background execution
            "npm test &",
            "pytest --cov &",
        ]
        
        expected_sounds = [
            "commit.wav", "test.wav", "pr.wav",  # pipes
            "commit.wav", "test.wav", "pr.wav",  # chaining
            "commit.wav", "test.wav",            # redirection  
            "test.wav", "test.wav",              # background
        ]
        
        for command, expected_sound in zip(complex_commands, expected_sounds):
            sound_file = sound_manager_with_mock_sounds._get_bash_sound(command)
            assert sound_file is not None, f"No sound for complex command: {command}"
            assert sound_file.name == expected_sound, f"Wrong sound for: {command}"

    def test_case_sensitivity_patterns(self, sound_manager_with_mock_sounds):
        """Test case sensitivity in pattern matching."""
        # These should NOT match (patterns are case-sensitive)
        case_variations = [
            "Git commit -m 'test'",  # Capital G
            "GIT COMMIT -m 'test'",  # All caps
            "Npm test",              # Capital N
            "Gh pr create",          # Capital G
            "Pytest",                # Capital P
        ]
        
        for command in case_variations:
            sound_file = sound_manager_with_mock_sounds._get_bash_sound(command)
            # Should fall back to bash.wav, not match specific patterns
            assert sound_file.name == "bash.wav", f"Case insensitive match for: {command}"


@pytest.mark.sound_logic
class TestPatternRegexValidation:
    """Test regex pattern validation and compilation."""

    def test_all_patterns_compile_successfully(self, sound_mappings_data):
        """Test that all regex patterns in mappings compile without errors."""
        bash_patterns = sound_mappings_data.get("bash_patterns", [])
        
        for pattern_config in bash_patterns:
            pattern = pattern_config["pattern"]
            try:
                compiled = re.compile(pattern)
                # Test that pattern can be used for matching
                compiled.search("test string")
            except re.error as e:
                pytest.fail(f"Invalid regex pattern '{pattern}': {e}")

    def test_pattern_specificity(self, sound_mappings_data):
        """Test that patterns are appropriately specific."""
        bash_patterns = sound_mappings_data.get("bash_patterns", [])
        
        # Find the fallback pattern (should be ".*")
        fallback_pattern = None
        specific_patterns = []
        
        for pattern_config in bash_patterns:
            pattern = pattern_config["pattern"]
            if pattern == ".*":
                fallback_pattern = pattern_config
            else:
                specific_patterns.append(pattern_config)
        
        # Should have exactly one fallback pattern
        assert fallback_pattern is not None, "No fallback pattern found"
        
        # Should have multiple specific patterns
        assert len(specific_patterns) >= 3, "Not enough specific patterns"
        
        # Fallback should be last (for precedence)
        assert bash_patterns[-1]["pattern"] == ".*", "Fallback pattern not last"

    def test_pattern_non_overlapping_coverage(self, sound_manager_with_mock_sounds):
        """Test that command examples don't incorrectly match multiple patterns."""
        # These commands should match exactly one specific pattern each
        specific_matches = [
            ("git commit -m 'test'", "commit.wav"),
            ("gh pr create", "pr.wav"), 
            ("npm test", "test.wav"),
            ("pytest", "test.wav"),
        ]
        
        for command, expected_sound in specific_matches:
            sound_file = sound_manager_with_mock_sounds._get_bash_sound(command)
            assert sound_file.name == expected_sound
            
            # Verify this is the first match by manually checking patterns
            mappings = sound_manager_with_mock_sounds.mappings
            bash_patterns = mappings.get("bash_patterns", [])
            
            matches_found = 0
            first_match_sound = None
            
            for pattern_config in bash_patterns:
                pattern = pattern_config["pattern"]
                if re.search(pattern, command):
                    matches_found += 1
                    if first_match_sound is None:
                        first_match_sound = pattern_config["sound"]
            
            # Should match at least one pattern (could match fallback too)
            assert matches_found >= 1, f"Command '{command}' matched no patterns"
            
            # First match should be the expected sound
            assert f"{first_match_sound}.wav" == expected_sound, \
                f"First match mismatch for '{command}'"


# Additional fixtures for pattern matching tests
@pytest.fixture
def sound_manager_with_mock_sounds(mock_sounds_dir, sound_mappings_data):
    """Create sound manager with mock sounds directory."""
    import json
    # Create a temporary hooks directory with sound_mappings.json
    hooks_dir = mock_sounds_dir.parent.parent
    mappings_file = hooks_dir / "sound_mappings.json"
    with open(mappings_file, "w") as f:
        json.dump(sound_mappings_data, f)
    
    return SoundManager(str(hooks_dir))