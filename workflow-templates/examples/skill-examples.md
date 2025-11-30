# Skill Examples

Examples of well-structured Skills for reference.

## Example 1: Simple PDF Processing Skill

```markdown
---
name: processing-pdfs
description: Extract text and tables from PDF files. Use when working with PDF files or when the user mentions PDFs or document extraction.
---

# PDF Processing

## Quick start

Extract text using pdfplumber:

\`\`\`python
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
\`\`\`

## Extract tables

\`\`\`python
with pdfplumber.open("file.pdf") as pdf:
    tables = pdf.pages[0].extract_tables()
\`\`\`

## Best practices

- Always check if file exists before processing
- Handle exceptions for corrupted PDFs
- Consider page count for large documents
```

## Example 2: Complex Data Analysis Skill

```markdown
---
name: analyzing-sales-data
description: Analyze sales data in BigQuery, generate reports, and provide insights. Use when working with sales data, revenue metrics, or BigQuery queries.
---

# Sales Data Analysis

## Quick start

Basic query pattern:

\`\`\`sql
SELECT date, revenue, region
FROM sales_data
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
\`\`\`

## Data sources

**Sales metrics**: See [reference/sales.md](reference/sales.md)
**Revenue metrics**: See [reference/revenue.md](reference/revenue.md)
**Regional data**: See [reference/regions.md](reference/regions.md)

## Analysis workflows

### Revenue trend analysis

1. Query sales_data for date range
2. Group by appropriate period (day/week/month)
3. Calculate growth rates
4. Identify anomalies

### Regional comparison

1. Query by region
2. Normalize for market size
3. Compare performance metrics
4. Generate visualization recommendations

## Validation

Always filter out test accounts: `WHERE account_type != 'test'`
```

## Example 3: Git Workflow Skill

```markdown
---
name: managing-git-workflows
description: Handle git operations including commits, branching, and PR management. Use when working with git, creating commits, or managing branches.
---

# Git Workflow Management

## Commit message format

Follow conventional commits:

\`\`\`
type(scope): brief description

Detailed explanation of what and why.
\`\`\`

Types: feat, fix, docs, refactor, test, chore

## Branch naming

- `feature/description` for new features
- `fix/description` for bug fixes
- `refactor/description` for refactoring

## PR workflow

1. Create feature branch from main
2. Make changes with descriptive commits
3. Push and create PR
4. Address review feedback
5. Squash merge when approved
```

## Key patterns to notice

1. **Clear descriptions**: Include specific keywords and triggers
2. **Progressive disclosure**: Complex skills reference additional files
3. **Concrete examples**: Show actual code, not just descriptions
4. **Concise content**: Only essential information, assume Claude is smart
5. **Workflows**: Step-by-step processes for complex tasks
