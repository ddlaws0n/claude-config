# UI Elements Reference

Marimo provides interactive UI elements in the `marimo.ui` namespace.

## Common Widgets

**Slider**
```python
slider = mo.ui.slider(start=1, end=100, step=1)
# Access value via slider.value
````

**Dropdown**

```python
dropdown = mo.ui.dropdown(["A", "B", "C"], value="A")
```

**Tables**

```python
# Interactive dataframe
table = mo.ui.table(df)
# Access selected rows via table.value
```

## State Management

UI elements are reactive. When a user interacts with a widget, all cells referencing that widget's variable are re-run.

```python
@app.cell
def __(mo):
    slider = mo.ui.slider(1, 10)
    slider
    return slider,

@app.cell
def __(slider):
    # This cell re-runs automatically when slider moves
    result = slider.value * 2
    return result,
```
