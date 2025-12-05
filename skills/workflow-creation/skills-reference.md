# Skills Reference

## Frontmatter Fields

| Field | Required | Constraints |
|-------|----------|-------------|
| `name` | Yes | Lowercase letters, numbers, hyphens only. Max 64 characters. Cannot contain "anthropic" or "claude". |
| `description` | Yes | Non-empty, max 1024 characters. Must explain what it does AND when to use it. Write in third person. |
| `allowed-tools` | No | Comma-separated list of tools. If omitted, Claude asks for permission as normal. |

## Description Best Practices

Descriptions are critical for Claude to discover when to use your Skill. Include both what the Skill does and specific triggers/keywords.

**Too vague**: "Helps with documents"

**Specific**: "Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction."

Write descriptions in third person, not "I can help you" or "You can use this."

## Progressive Disclosure

Keep SKILL.md concise (under 500 lines) and link to detailed references. Claude loads additional files only when needed.

**Example structure for complex Skills**:
```
skill-name/
├── SKILL.md          (overview and quick start, under 500 lines)
├── REFERENCE.md      (detailed API reference)
├── EXAMPLES.md       (usage examples)
└── scripts/
    └── helper.py     (executable utilities)
```

**Example SKILL.md with progressive disclosure**:
```markdown
---
name: pdf-processing
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
---

# PDF Processing

## Quick start
Extract text using pdfplumber:
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()

## Advanced features
**Form filling**: See [FORMS.md](FORMS.md) for complete guide
**API reference**: See [REFERENCE.md](REFERENCE.md) for all methods
```

## Tool Restrictions

Use `allowed-tools` to limit capabilities for security-sensitive workflows:

```yaml
---
name: safe-file-reader
description: Read files without making changes. Use when you need read-only file access.
allowed-tools: Read, Grep, Glob
---
```

When this Skill is active, Claude can only use the specified tools without asking permission.

## Degrees of Freedom

Match specificity to task fragility:

**High freedom** (flexible tasks): Text-based instructions allowing Claude to choose approach
**Medium freedom** (structured tasks): Pseudocode or scripts with parameters
**Low freedom** (fragile operations): Specific scripts with exact commands

## Conciseness Guidelines

Only add context Claude doesn't already have. Challenge every paragraph: "Does Claude really need this?" Assume Claude is smart and knows common concepts. Avoid repeating information already in the description.

## Validation Rules

- SKILL.md must exist in the skill directory
- Opening `---` on line 1, closing `---` before content
- Valid YAML syntax (no tabs, correct indentation)
- Name follows naming requirements
- Description is non-empty and includes triggers
- References are one level deep (no nested references)
- Scripts have execute permissions (`chmod +x`)

## Common Patterns

**Simple Skill** (single file): SKILL.md only, under 200 lines, inline examples

**Domain-organized Skill**: SKILL.md + reference/ directory with domain-specific files

**Workflow Skill**: SKILL.md with step-by-step workflows and validation loops

**Tool-oriented Skill**: SKILL.md + scripts/ directory with executable utilities

