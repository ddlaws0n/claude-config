# Template Documentation Guide

## Template Optimization for Token Efficiency

This document provides guidance on using the template files efficiently to minimize token usage when Claude loads them.

## Template Files Overview

| Template | Lines | Purpose | Key Features |
|----------|-------|---------|--------------|
| `dashboard.py` | 351 | Interactive data dashboard | Reactive filters, visualizations |
| `analytics.py` | 531 | Data analysis workflow | Statistical testing, cleaning |
| `form.py` | 641 | Multi-step form builder | Validation, state management |
| `ml_pipeline.py` | 841 | Machine learning workflow | Classification, regression, clustering |
| `realtime.py` | 622 | Real-time monitoring | Live data streaming, alerts |

## Token Usage Recommendations

### When Loading Templates
- **Load only needed templates**: Use the specific template file rather than loading all
- **Focus on structure**: The `@app.cell` decorators and function signatures are most important
- **Skip extensive comments**: Inline documentation can be ignored during code generation

### Template Structure Patterns
All templates follow this consistent pattern:
```python
@app.cell
def cell_N():
    """Brief description"""
    # Core functionality
    return variables
```

## Template-Specific Optimization Tips

### Dashboard Template (`templates/dashboard.py`)
**Core elements to focus on:**
- Cell function definitions (`cell_1` through `cell_9`)
- UI component creation (`mo.ui.*`)
- Data binding patterns
- Reactive chart configurations

**Can skip for token efficiency:**
- Detailed comment blocks
- Multi-line docstrings
- Example data generation code

### Analytics Template (`templates/analytics.py`)
**Core elements to focus on:**
- Data loading and validation patterns
- Statistical analysis functions
- Visualization configurations
- Data cleaning workflows

**Can skip for token efficiency:**
- Insight generation logic (lines 440+)
- Detailed quality assessment comments
- Sample data generation

### Form Template (`templates/form.py`)
**Core elements to focus on:**
- Form structure and validation patterns
- State management approach
- Multi-step form logic
- UI component combinations

**Can skip for token efficiency:**
- Extensive form field documentation
- Example form configurations
- Validation message templates

### ML Pipeline Template (`templates/ml_pipeline.py`)
**Core elements to focus on:**
- ML workflow structure
- Model training patterns
- Cross-validation setup
- Result visualization

**Can skip for token efficiency:**
- Feature engineering explanations
- Model comparison logic
- Detailed performance metrics

### Realtime Template (`templates/realtime.py`)
**Core elements to focus on:**
- Real-time data streaming patterns
- Alert system configuration
- Auto-refresh mechanisms
- Live chart updates

**Can skip for token efficiency:**
- Alert generation logic
- Data simulation functions
- Status monitoring details

## Loading Strategies

### Efficient Template Loading
```bash
# Load specific template
read templates/dashboard.py

# Load just the structure (first ~50 lines)
head -50 templates/dashboard.py

# Skip to specific cell functions
grep -n "@app.cell" templates/dashboard.py
```

### Code Generation Patterns
When using templates for code generation:
1. **Extract cell patterns**: Focus on the `@app.cell` structure
2. **Adapt function names**: Use unique function names for new notebooks
3. **Modify imports**: Keep only necessary imports
4. **Simplify logic**: Remove complex example code

## Custom Template Creation

### Best Practices for Lightweight Templates
- **Minimal documentation**: Use brief, single-line docstrings
- **Focused functions**: Each cell should have a single responsibility
- **Essential imports only**: Remove unused imports
- **Consistent naming**: Use predictable function names

### Template Boilerplate
```python
import marimo

__generated_with = "0.8.0"
app = marimo.App(width="full")

@app.cell
def cell_1():
    """Setup and imports"""
    import marimo as mo
    import pandas as pd
    return mo, pd

@app.cell
def cell_2(mo, pd):
    """Core functionality"""
    # Main logic here
    return result
```

## Reference Documentation

For detailed template features and advanced usage, see:
- `templates/README.md` - Complete template documentation
- Individual template files for full implementation details
- `reference/code_structure.md` - Core marimo patterns
- `reference/best_practices.md` - Development guidelines