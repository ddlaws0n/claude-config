# Marimo Advanced Features

## Reactive UI Components

### Interactive Plots
```python
import marimo as mo
import plotly.express as px

@cell
def create_interactive_plot():
    df = px.data.iris()
    fig = px.scatter(df, x='sepal_width', y='sepal_length', color='species')
    return mo.ui.plotly(fig)
```

### Forms and Controls
```python
# Multi-step forms
form = mo.ui.form({
    'name': mo.ui.text(label="Name"),
    'age': mo.ui.slider(18, 100, label="Age"),
    'preferences': mo.ui.checkbox(['A', 'B', 'C'])
})

# File uploads
file_upload = mo.ui.file()
```

## Data Integration

### Database Connections
```python
import sqlite3
import marimo as mo

@cell
def connect_database():
    conn = sqlite3.connect('data.db')
    return conn
```

### API Integration
```python
import requests
import marimo as mo

@cell
def fetch_api_data():
    response = requests.get('https://api.example.com/data')
    return response.json()
```

## Real-time Updates

### Auto-refresh
```python
@cell
def live_data():
    # Auto-refresh every 30 seconds
    return get_latest_data()

# Configure auto-refresh
live_data() every 30
```

### Streaming Data
```python
import asyncio
import marimo as mo

@cell
async def stream_data():
    async for data in stream_source():
        yield data
```

## Custom Components

### Component Creation
```python
import marimo as mo

def custom_component(data):
    """Create custom UI component."""
    return mo.html(f"<div class='custom'>{data}</div>")

# Use in cells
@cell
def display_custom():
    return custom_component("Hello World")
```

## Performance Optimization

### Caching
```python
import marimo as mo

@cache  # Cache results
def expensive_operation(data):
    return complex_calculation(data)
```

### Lazy Loading
```python
@cell
def load_large_dataset():
    # Load only when needed
    return pandas.read_csv('large_file.csv')
```