# Dependencies and Installation

This guide covers all required dependencies for working with marimo notebooks and templates.

## Core Requirements

### Essential Installation
```bash
uv add "marimo[recommended]"  # Main marimo package with recommended extras
```

## Template Dependencies

### Dashboard Templates
```bash
# Interactive visualizations and data handling
uv add plotly pandas altair
```

### Analytics Templates
```bash
# Statistical analysis and data science
uv add scipy scikit-learn seaborn
```

### Machine Learning Pipeline Templates
```bash
# ML algorithms and preprocessing
uv add scikit-learn xgboost lightgbm
```

### Deployment Utilities
```bash
# Web deployment and model serving
uv add huggingface_hub fastapi uvicorn
```

### Optional Dependencies

#### Advanced Visualization
```bash
uv add matplotlib seaborn bokeh
```

#### Data Processing
```bash
uv add polars pyarrow openpyxl
```

#### Web Integration
```bash
uv add requests httpx beautifulsoup4
```

#### Database Connectivity
```bash
uv add sqlalchemy psycopg2-binary pymongo redis
```

#### Testing and Validation
```bash
uv add pytest pytest-asyncio coverage
```

## Environment Setup

### Create New Project
```bash
# Initialize new marimo project
mkdir my_marimo_project
cd my_marimo_project
uv init
uv add "marimo[recommended]"
```

### Virtual Environment
```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Using traditional approach
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

## Development Tools

### IDE Extensions
- **VS Code**: Marimo extension for syntax highlighting
- **PyCharm**: Python plugin with marimo support
- **Jupyter**: Marimo kernel integration

### Browser Requirements
- Modern browser with JavaScript enabled
- Recommended: Chrome, Firefox, Safari, Edge

## Version Compatibility

| Marimo Version | Python Minimum | Key Features |
|---------------|----------------|--------------|
| 0.8.x | 3.8+ | Latest features, stable API |
| 0.7.x | 3.8+ | Stable production version |
| 0.6.x | 3.8+ | Legacy compatibility |

## Troubleshooting Dependencies

### Common Issues

**Import Errors**
```bash
# Check installation
uv list | grep marimo

# Reinstall if needed
uv remove marimo
uv add "marimo[recommended]"
```

**Virtual Environment Issues**
```bash
# Verify environment
which python
python --version

# Reset environment
rm -rf .venv
uv venv
```

**Platform-Specific Issues**
```bash
# macOS: Install XCode tools if needed
xcode-select --install

# Linux: Install system dependencies
sudo apt-get install python3-dev  # Ubuntu/Debian
sudo yum install python3-devel    # CentOS/RHEL

# Windows: Install Microsoft C++ Build Tools
# Download from visualstudio.microsoft.com
```