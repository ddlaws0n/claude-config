---
name: working-with-marimo
description: Creates, edits, and converts marimo reactive notebooks; use when the user needs dashboards, interactive notebooks, or Jupyter-to-marimo conversion.
allowed-tools: Read, Write, Execute
license: MIT
---

# Working with Marimo

This skill helps you create and manage [marimo](https://docs.marimo.io/) notebooks—reactive Python notebooks stored as pure `.py` files. Marimo provides deterministic execution, reactive programming, and seamless deployment capabilities.

## Quick Start

1. **Install dependencies**: Read [reference/dependencies.md](reference/dependencies.md) for complete setup
2. **Create notebook**: `uv run scripts/scaffold_marimo.py my_notebook.py`
3. **Edit**: `marimo edit my_notebook.py`
4. **Run as app**: `marimo run my_notebook.py --host 0.0.0.0 --port 2718`

## Capabilities

### Core Features
- ✅ **Notebook Scaffolding**: Generate valid marimo notebooks
- ✅ **Template Library**: Pre-built templates for dashboards, analytics, forms, ML
- ✅ **Jupyter Conversion**: Enhanced conversion with validation
- ✅ **Validation & Testing**: Comprehensive notebook structure validation
- ✅ **Performance Optimization**: Automatic optimization suggestions
- ✅ **Deployment Automation**: Multi-platform deployment tools

## Structured Workflows

For detailed step-by-step guides with validation checklists:

- **Interactive Dashboard**: Read [reference/workflows.md](reference/workflows.md) for dashboard creation workflow
- **Jupyter Conversion**: Read [reference/workflows.md](reference/workflows.md) for notebook conversion workflow
- **Real-time Monitor**: Read [reference/workflows.md](reference/workflows.md) for monitoring system workflow
- **Web Application**: Read [reference/workflows.md](reference/workflows.md) for deployment workflow
- **ML Pipeline**: Read [reference/workflows.md](reference/workflows.md) for machine learning workflow

## CLI Commands

For complete command reference:

- **Basic Marimo Commands**: Read [reference/cli_commands.md](reference/cli_commands.md) for essential operations
- **Enhanced Utilities**: Read [reference/cli_commands.md](reference/cli_commands.md) for advanced scripting tools
- **Template Management**: Read [reference/cli_commands.md](reference/cli_commands.md) for template operations
- **Deployment Tools**: Read [reference/cli_commands.md](reference/cli_commands.md) for production deployment

## Templates

**Available Templates:**
- `dashboard` - Interactive data dashboard with filters and charts
- `analytics` - Data analysis workflow with statistical testing
- `form` - Multi-step form builder with validation
- `realtime` - Real-time monitoring with alerts
- `ml_pipeline` - Machine learning workflow templates

**Usage:** `python scripts/create_dashboard.py my_app.py --template dashboard`

**Template Details**: Read [reference/template_documentation.md](reference/template_documentation.md) for complete template guide

## Reference Documentation

For detailed guides and troubleshooting:

- **Core Concepts**: Read [reference/core_concepts.md](reference/core_concepts.md) when learning marimo fundamentals
- **Advanced Features**: Read [reference/advanced_features.md](reference/advanced_features.md) for complex workflows
- **Integration Guides**: Read [reference/integration_guides.md](reference/integration_guides.md) to connect with external tools
- **Code Structure**: Read [reference/code_structure.md](reference/code_structure.md) for syntax patterns
- **Template Optimization**: Read [reference/template_documentation.md](reference/template_documentation.md) for custom templates
- **Best Practices**: Read [reference/best_practices.md](reference/best_practices.md) for production guidelines
- **Troubleshooting**: Read [reference/troubleshooting.md](reference/troubleshooting.md) for common issues
- **Version History**: Read [reference/version_history.md](reference/version_history.md) for changelog

## File Structure

Marimo files are pure Python with `@app.cell` decorators. Read [reference/code_structure.md](reference/code_structure.md) for complete syntax examples.

## Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| Notebook won't run | `marimo check notebook.py` to validate structure |
| Import errors | Install missing packages, check virtual environment |
| Reactivity not working | Verify cell references with `@cell` decorators |
| Performance issues | Use `validate_notebook.py --profile` for analysis |

**For detailed solutions:** Read [reference/troubleshooting.md](reference/troubleshooting.md) for complete troubleshooting guide