# Troubleshooting Guide

## Common Issues

### Notebook Won't Run

**Problem**: Notebook fails to execute
**Solutions**:
- Check Python version compatibility (3.8+)
- Verify marimo installation: `pip install marimo`
- Run `marimo check` to validate notebook structure
- Check for circular dependencies in cell references

### Dependencies Not Found

**Problem**: ImportError for required packages
**Solutions**:
- Install missing dependencies: `pip install package_name`
- Check requirements.txt includes all needed packages
- Verify virtual environment is activated
- Use `pip freeze | grep package_name` to verify installation

### Reactive Updates Not Working

**Problem**: UI elements not updating when data changes
**Solutions**:
- Verify cell references are correct (`@cell` decorators)
- Check for missing dependency declarations
- Ensure variables are properly returned from cells
- Use `marimo check` to validate reactivity

### Performance Issues

**Problem**: Slow notebook execution
**Solutions**:
- Profile with `validate_notebook.py --profile`
- Add caching to expensive operations
- Break large cells into smaller ones
- Consider data sampling for large datasets

### Import Errors

**Problem**: Custom modules not found
**Solutions**:
- Add module directory to PYTHONPATH
- Use relative imports for local modules
- Check file naming conflicts with standard library
- Verify __init__.py files in package directories

## Debugging Techniques

### Cell-by-Cell Execution
```python
# Run individual cells for debugging
marimo run notebook.py --cell 5
```

### Variable Inspection
```python
# Print variable values
@cell
def debug_cell():
    x = complex_calculation()
    print(f"Debug: x = {x}")
    return x
```

### Error Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

@cell
def logged_operation():
    try:
        result = risky_operation()
        return result
    except Exception as e:
        logging.error(f"Operation failed: {e}")
        raise
```

## Validation Tools

### Notebook Structure Check
```bash
# Validate notebook structure
marimo check notebook.py
```

### Performance Profiling
```bash
# Profile execution time
python scripts/validate_notebook.py --profile notebook.py
```

### Security Scan
```bash
# Check for security issues
python scripts/validate_notebook.py --security notebook.py
```

## Getting Help

### Marimo Documentation
- [Official Documentation](https://marimo.io/docs)
- [API Reference](https://marimo.io/api)
- [Community Forum](https://github.com/marimo-team/marimo/discussions)

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `ImportError: cannot import name 'marimo'` | marimo not installed | `pip install marimo` |
| `AttributeError: module 'marimo' has no attribute 'ui'` | incorrect import | Use `import marimo as mo` |
| `TypeError: 'NoneType' object is not callable` | missing return | Ensure cells return values |
| `RecursionError: maximum recursion depth exceeded` | circular dependency | Check cell references |