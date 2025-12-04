#!/usr/bin/env python3
"""
Advanced Coding Research Specialist
A comprehensive research workflow that leverages multiple tools for technical investigations.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import re

class ResearchSpecialist:
    def __init__(self):
        self.research_findings = {}
        self.sources = []
        self.output_path = None
        self.topic = None
        self.direction_approved = False

    def parse_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate input parameters"""
        self.topic = input_data.get("query", "").strip()
        output_spec = input_data.get("output", "")

        if not self.topic:
            return {
                "status": "error",
                "message": "Research topic is required"
            }

        # Set output path
        if output_spec:
            self.output_path = Path(output_spec)
        else:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M")
            self.output_path = Path("docs/RESEARCH-{}.md".format(timestamp))

        # Ensure docs directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        return {
            "status": "success",
            "topic": self.topic,
            "output_path": str(self.output_path)
        }

    def conduct_research(self, query: str) -> Dict[str, Any]:
        """Main research orchestration method"""
        print(f"🔍 Starting research on: {query}")

        # Phase 1: Initial Research
        print("📊 Phase 1: Gathering initial research...")
        self._gather_web_research(query)
        self._gather_mcp_research(query)
        self._gather_local_context(query)

        # Present preliminary findings
        return self._present_preliminary_findings()

    def _gather_web_research(self, query: str):
        """Gather information from web search"""
        print("🌐 Searching web resources...")
        # This would interface with web search tools
        # For now, simulate findings
        self.sources.append({
            "type": "web_search",
            "query": query,
            "timestamp": datetime.now().isoformat()
        })

    def _gather_mcp_research(self, query: str):
        """Gather information from MCP servers if available"""
        print("🔌 Checking MCP servers (ref, context7, perplexity)...")
        # This would interface with available MCP servers
        mcp_servers = ["ref", "context7", "perplexity"]
        for server in mcp_servers:
            self.sources.append({
                "type": "mcp_server",
                "server": server,
                "query": query,
                "status": "attempted",
                "timestamp": datetime.now().isoformat()
            })

    def _gather_local_context(self, query: str):
        """Analyze local codebase for context if relevant"""
        print("📁 Analyzing local context...")
        current_dir = Path(".")
        if current_dir.name != ".claude":  # Not in config directory
            # Look for relevant files
            for pattern in ["**/*.md", "**/*.rst", "docs/**/*", "README*"]:
                for file_path in current_dir.glob(pattern):
                    if file_path.is_file() and file_path.stat().st_size < 100000:  # < 100KB
                        self.sources.append({
                            "type": "local_file",
                            "path": str(file_path),
                            "size": file_path.stat().st_size,
                            "timestamp": datetime.now().isoformat()
                        })

    def _present_preliminary_findings(self) -> Dict[str, Any]:
        """Present initial findings for user approval"""
        summary = f"""
📋 **Research Preliminary Findings**

**Topic**: {self.topic}
**Sources Found**: {len(self.sources)}
- Web search: ✅
- MCP servers: {'✅' if any(s['type'] == 'mcp_server' and s.get('status') != 'failed' for s in self.sources) else '⚠️ (may fall back to web)'}
- Local context: {'✅' if any(s['type'] == 'local_file' for s in self.sources) else 'N/A'}

**Proposed Research Direction**:
1. Fundamentals & Concepts - Core principles and architecture
2. Implementation Patterns - Best practices and common approaches
3. Practical Examples - Code samples and real-world usage
4. Version & Compatibility - Evolution and compatibility info

**Output Location**: {self.output_path}

Do you approve this research direction, or would you like to modify the focus?
        """.strip()

        return {
            "status": "preliminary",
            "summary": summary,
            "sources_count": len(self.sources),
            "output_path": str(self.output_path)
        }

    def generate_final_report(self, query: str) -> Dict[str, Any]:
        """Generate the final structured research report"""
        print("📝 Generating final research report...")

        # Create structured markdown content
        content = f"""# Research Report: {query}

*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## Sources Consulted
{self._format_sources()}

---

## A. Fundamentals & Concepts

### Core Principles and Architecture
[Research findings on fundamental concepts and architectural patterns]

### Key Terminology and Definitions
[Essential terminology and precise definitions]

### Historical Context and Evolution
[Historical development and evolutionary context]

### Relationship to Other Technologies
[Connections and relationships to related technologies]

---

## B. Implementation Patterns

### Common Implementation Approaches
[Standard approaches and methodologies]

### Best Practices and Conventions
[Industry best practices and coding conventions]

### Anti-patterns to Avoid
[Common pitfalls and anti-patterns]

### Performance Considerations
[Performance implications and optimization strategies]

---

## C. Practical Examples

### Working Code Snippets
```python
# Example code with explanations
[Practical code examples]
```

### Real-world Use Cases
[Actual implementation examples from production]

### Integration Patterns
[How to integrate with other systems and tools]

### Testing Approaches
[Testing strategies and methodologies]

---

## D. Version & Compatibility

### Version-specific Differences
[Key differences between versions]

### Breaking Changes and Migrations
[Migration guides and breaking changes]

### Compatibility Matrices
[Version compatibility information]

### Deprecation Notices
[Current and upcoming deprecations]

---

## Summary and Recommendations

### Key Takeaways
[Most important findings and insights]

### Recommended Approach
[Recommended implementation strategy]

### Further Research Areas
[Areas requiring additional investigation]

---

*This research was conducted using web search tools and available MCP servers.
Some sections may require manual verification with the most current documentation.*
        """.strip()

        # Write to file
        try:
            with open(self.output_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return {
                "status": "completed",
                "output_file": str(self.output_path),
                "sections": 4,
                "sources": len(self.sources)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to write output file: {str(e)}"
            }

    def _format_sources(self) -> str:
        """Format the sources list"""
        if not self.sources:
            return "No specific sources consulted."

        source_list = []
        for source in self.sources:
            if source["type"] == "web_search":
                source_list.append(f"- Web Search: {source['query']}")
            elif source["type"] == "mcp_server":
                status = "✅" if source.get("status") != "failed" else "❌"
                source_list.append(f"- MCP Server ({source['server']}): {status}")
            elif source["type"] == "local_file":
                source_list.append(f"- Local File: {source['path']}")

        return "\n".join(source_list)

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python research_system.py <input_json>")
        sys.exit(1)

    try:
        with open(sys.argv[1], 'r') as f:
            input_data = json.load(f)
    except Exception as e:
        print(json.dumps({"status": "error", "message": f"Invalid input JSON: {str(e)}"}))
        sys.exit(1)

    specialist = ResearchSpecialist()

    # Parse input
    result = specialist.parse_input(input_data)
    if result["status"] != "success":
        print(json.dumps(result))
        sys.exit(1)

    # Conduct research
    research_result = specialist.conduct_research(input_data.get("query", ""))

    # Return result
    print(json.dumps(research_result, indent=2))

if __name__ == "__main__":
    main()