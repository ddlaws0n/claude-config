# CLI Commands Reference

Complete reference for marimo and utility command-line operations.

## Basic Marimo Commands

### Essential Commands
```bash
# Convert Jupyter notebook to marimo
marimo convert notebook.ipynb -o notebook.py

# Open marimo editor in browser
marimo edit notebook.py

# Run notebook as web application
marimo run notebook.py

# Start interactive tutorial
marimo tutorial intro

# Validate notebook structure
marimo check notebook.py

# List available commands
marimo --help
```

### Advanced Marimo Commands
```bash
# Export to different formats
marimo export notebook.py --format html
marimo export notebook.py --format markdown
marimo export notebook.py --format ipynb

# Run with custom configuration
marimo run notebook.py --host 0.0.0.0 --port 2718
marimo run notebook.py --headless --no-open-browser

# Development mode with hot reload
marimo edit notebook.py --develop --watch

# Performance profiling
marimo run notebook.py --profile
```

## Enhanced Utility Commands

### Template Management
```bash
# Create new notebook from template
python scripts/create_dashboard.py name.py --template dashboard
python scripts/create_dashboard.py name.py --template analytics
python scripts/create_dashboard.py name.py --template form
python scripts/create_dashboard.py name.py --template realtime
python scripts/create_dashboard.py name.py --template ml_pipeline

# List available templates
python scripts/create_dashboard.py --list-templates
```

### Validation and Testing
```bash
# Basic notebook validation
python scripts/validate_notebook.py notebook.py

# Production-ready validation
python scripts/validate_notebook.py notebook.py --production

# Performance profiling
python scripts/validate_notebook.py notebook.py --profile

# Security scanning
python scripts/validate_notebook.py notebook.py --security-scan
```

### Jupyter Conversion
```bash
# Basic conversion
python scripts/convert_jupyter.py notebook.ipynb

# Conversion with validation
python scripts/convert_jupyter.py notebook.ipynb --validate

# Smart conversion with optimization
python scripts/convert_jupyter.py notebook.ipynb --optimize

# Batch conversion
python scripts/convert_jupyter.py *.ipynb --batch --output-dir converted/
```

### Deployment Tools
```bash
# Local deployment
python scripts/deploy_app.py app.py

# Build for production
python scripts/deploy_app.py app.py --build

# Deploy to specific platforms
python scripts/deploy_app.py app.py --platform huggingface
python scripts/deploy_app.py app.py --platform streamlit
python scripts/deploy_app.py app.py --platform fastapi

# Configure deployment settings
python scripts/deploy_app.py app.py --config deploy.yaml
```

### Performance Optimization
```bash
# Analyze notebook performance
python scripts/optimize_notebook.py notebook.py --analyze

# Apply automatic optimizations
python scripts/optimize_notebook.py notebook.py --optimize

# Generate optimization report
python scripts/optimize_notebook.py notebook.py --report --format json
```

## Configuration Options

### Global Marimo Configuration
```bash
# Set default editor
marimo config set editor vscode

# Configure default port
marimo config set port 2718

# Set auto-save interval
marimo config set autosave 30

# Enable/disable features
marimo config set features.experimental true
```

### Environment Variables
```bash
# Marimo server settings
export MARIMO_SERVER_HOST=0.0.0.0
export MARIMO_SERVER_PORT=2718
export MARIMO_SERVER_DEBUG=false

# Notebook execution
export MARIMO_TIMEOUT=300
export MARIMO_MEMORY_LIMIT="2GB"
export MARIMO_ENABLE_SANDBOX=true

# Development mode
export MARIMO_DEVELOP_MODE=true
export MARIMO_LOG_LEVEL=debug
```

## Batch Operations

### Multiple Notebook Processing
```bash
# Validate all notebooks in directory
python scripts/validate_notebook.py *.py --recursive

# Convert all Jupyter notebooks
python scripts/convert_jupyter.py notebooks/*.ipynb --batch

# Deploy multiple apps
python scripts/deploy_app.py apps/*.py --parallel --max-workers 4
```

### Directory Management
```bash
# Create project structure
python scripts/create_dashboard.py --project my_project --template full

# Clean generated files
python scripts/cleanup.py --target-cache --target-artifacts

# Archive old notebooks
python scripts/archive_notebooks.py --older-than 30days --destination archive/
```

## Integration with External Tools

### Git Integration
```bash
# Track notebook changes
git add notebook.py
git commit -m "Update notebook"

# Compare notebook versions
git diff HEAD~1 notebook.py

# Merge notebook changes
git merge feature-branch --no-edit
```

### Docker Integration
```bash
# Build Docker image
docker build -t marimo-app .

# Run in container
docker run -p 2718:2718 marimo-app

# Development with volume mount
docker run -p 2718:2718 -v $(pwd):/app marimo-app marimo edit app.py
```

### CI/CD Integration
```bash
# GitHub Actions
name: Test Marimo App
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install "marimo[recommended]"
      - run: marimo check notebooks/*.py
      - run: python scripts/validate_notebook.py notebooks/*.py --production
```

## Troubleshooting Commands

### Debug Mode
```bash
# Run with debug output
marimo edit notebook.py --debug
marimo run notebook.py --debug --log-level debug

# Check system requirements
marimo doctor

# Verbose error messages
python scripts/validate_notebook.py notebook.py --verbose
```

### Recovery Commands
```bash
# Recover corrupted notebook
marimo recover --backup notebook.py.backup

# Reset marimo configuration
marimo config reset

# Clear cache and temporary files
marimo cleanup --cache --temp
```