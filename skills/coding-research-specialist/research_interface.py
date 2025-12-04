#!/usr/bin/env python3
"""
Research Specialist Interface
Main entry point for the research workflow with progressive disclosure
"""

import json
import sys
import subprocess
from pathlib import Path

def detect_research_intent(message: str) -> bool:
    """Detect if message contains research intent"""
    research_keywords = [
        "research", "investigate", "analyze", "explore", "deep dive",
        "tell me about", "explain", "how does", "what is", "best practices",
        "patterns", "architecture", "evolution", "history of"
    ]

    message_lower = message.lower()
    return any(keyword in message_lower for keyword in research_keywords)

def extract_topic(message: str) -> str:
    """Extract the research topic from user message"""
    # Remove research intent keywords to get the core topic
    prefixes = [
        "research ", "investigate ", "analyze ", "explore ",
        "tell me about ", "explain ", "how does ", "what is ",
        "what are ", "can you research ", "can you investigate "
    ]

    topic = message.strip()
    for prefix in prefixes:
        if topic.lower().startswith(prefix):
            topic = topic[len(prefix):].strip()
            break

    # Remove trailing questions marks and clean up
    topic = topic.rstrip('?').strip()

    return topic if topic else message.strip()

def main():
    """Main interface entry point"""
    if len(sys.argv) < 2:
        print(json.dumps({
            "status": "error",
            "message": "Usage: python research_interface.py <user_message>"
        }))
        sys.exit(1)

    user_message = sys.argv[1]

    # Check if this is a research request
    if not detect_research_intent(user_message):
        print(json.dumps({
            "status": "not_research",
            "message": "No research intent detected"
        }))
        sys.exit(0)

    # Extract the topic
    topic = extract_topic(user_message)

    # Create input for the research system
    research_input = {
        "query": topic,
        "output": "",  # Use default
        "user_message": user_message
    }

    # Get the script directory
    script_dir = Path(__file__).parent
    research_script = script_dir / "research_system.py"

    # Create temporary input file
    temp_input = script_dir / "temp_input.json"
    with open(temp_input, 'w') as f:
        json.dump(research_input, f)

    try:
        # Run the research system
        result = subprocess.run(
            [sys.executable, str(research_script), str(temp_input)],
            capture_output=True,
            text=True,
            cwd=str(script_dir)
        )

        # Clean up temp file
        temp_input.unlink(missing_ok=True)

        if result.returncode != 0:
            print(json.dumps({
                "status": "error",
                "message": f"Research system failed: {result.stderr}"
            }))
            sys.exit(1)

        # Parse and return the result
        try:
            research_output = json.loads(result.stdout)
            print(json.dumps(research_output, indent=2))
        except json.JSONDecodeError:
            print(json.dumps({
                "status": "error",
                "message": f"Invalid JSON from research system: {result.stdout}"
            }))
            sys.exit(1)

    except Exception as e:
        # Clean up on error
        temp_input.unlink(missing_ok=True)
        print(json.dumps({
            "status": "error",
            "message": f"Failed to run research: {str(e)}"
        }))
        sys.exit(1)

if __name__ == "__main__":
    main()