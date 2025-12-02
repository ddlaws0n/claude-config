# Integration Guides

## Pandas Integration

### Data Analysis Workflow
```python
import pandas as pd
import marimo as mo

@cell
def load_data():
    df = pd.read_csv('data.csv')
    return df

@cell
def analyze_data(df=load_data):
    summary = {
        'shape': df.shape,
        'columns': df.columns.tolist(),
        'dtypes': df.dtypes.value_counts()
    }
    return summary
```

### Reactive Filtering
```python
@cell
def create_filters(df=load_data):
    return {
        'category': mo.ui.dropdown(df['category'].unique()),
        'date_range': mo.ui.date_range()
    }

@cell
def filtered_data(df=load_data, filters=create_filters):
    mask = df['category'] == filters['category'].value
    return df[mask]
```

## SQL Integration

### Database Operations
```python
import sqlite3
import marimo as mo

@cell
def execute_query(query: str):
    conn = sqlite3.connect('database.db')
    result = pd.read_sql_query(query, conn)
    conn.close()
    return result
```

### Interactive SQL
```python
@cell
def sql_interface():
    query_editor = mo.ui.code_editor(
        language='sql',
        placeholder='Enter SQL query...'
    )
    return query_editor

@cell
def run_query(editor=sql_interface):
    return execute_query(editor.value)
```

## Deployment Integration

### Docker Configuration
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
EXPOSE 8000
CMD ["marimo", "run", "app.py", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables
```python
import os
import marimo as mo

@cell
def load_config():
    return {
        'database_url': os.getenv('DATABASE_URL'),
        'api_key': os.getenv('API_KEY')
    }
```

## External Services

### REST API Integration
```python
import requests
import marimo as mo

@cell
def api_client():
    base_url = "https://api.example.com"
    return requests.Session()
```

### WebSocket Integration
```python
import websockets
import asyncio
import marimo as mo

@cell
async def websocket_client():
    async with websockets.connect('ws://localhost:8765') as ws:
        return await ws.recv()
```