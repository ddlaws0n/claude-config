# Marimo Code Structure Examples

## Basic Notebook Template

```python
import marimo

__generated_with = "0.8.0"
app = marimo.App(width="full")

@app.cell
def __():
    import marimo as mo
    import pandas as pd
    import plotly.express as px
    return mo, pd, px

@app.cell
def __(mo):
    mo.md("# 🚀 Interactive Dashboard")
    return

@app.cell
def __(mo, pd):
    # Reactive data loading
    data = pd.read_csv("data.csv")

    # Interactive controls
    controls = mo.ui.dictionary({
        "metric": mo.ui.dropdown(["revenue", "users", "conversion"]),
        "date_range": mo.ui.date_range(),
        "segment": mo.ui.multiselect(["all", "mobile", "desktop"])
    })

    return data, controls

@app.cell
def __(data, controls, mo, px):
    # Reactive visualization
    filtered_data = data[
        (data["date"] >= controls.value["date_range"][0]) &
        (data["date"] <= controls.value["date_range"][1]) &
        (data["segment"].isin(controls.value["segment"] if "all" not in controls.value["segment"] else data["segment"].unique()))
    ]

    chart = px.line(
        filtered_data,
        x="date",
        y=controls.value["metric"],
        title=f"{controls.value['metric'].title()} Over Time"
    )

    mo.ui.plotly(chart)
    return chart, filtered_data

if __name__ == "__main__":
    app.run()
```

## Cell Reference Patterns

### Basic Cell Definition
```python
@app.cell
def __():
    # Imports and setup
    import pandas as pd
    import marimo as mo
    return pd, mo
```

### Cell with Dependencies
```python
@app.cell
def __(data, mo):
    # This cell depends on 'data' and 'mo' from previous cells
    filtered = data[data['column'] > 0]
    mo.md(f"Found {len(filtered)} records")
    return
```

### Reactive UI Elements
```python
@app.cell
def __(mo):
    slider = mo.ui.slider(0, 100, value=50)
    dropdown = mo.ui.dropdown(['A', 'B', 'C'])
    return slider, dropdown

@app.cell
def __(slider, dropdown, mo):
    # React to UI changes
    selected_value = slider.value
    selected_option = dropdown.value
    mo.md(f"Slider: {selected_value}, Dropdown: {selected_option}")
    return
```