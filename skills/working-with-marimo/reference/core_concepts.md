# Marimo Core Concepts

## Reactive Programming Model

Marimo notebooks use a reactive execution model where changes automatically propagate through dependencies, unlike traditional notebooks that execute cells sequentially.

### Key Principles

- **Reactivity**: Variables automatically update when their dependencies change
- **Deterministic**: Each variable has a single source of truth
- **Stateless**: No hidden cell state that can cause inconsistencies

### Cell References

```python
# Cells reference each other through @ decorators
@cell
def cell_1():
    x = 10
    return x

@cell
def cell_2(x=cell_1):  # Direct dependency
    y = x * 2
    return y
```

## UI Elements

Marimo provides reactive UI elements that automatically update when their data changes:

```python
import marimo as mo

# Reactive slider
slider = mo.ui.slider(1, 100, value=50)

# Reactive dropdown
dropdown = mo.ui.dropdown(['A', 'B', 'C'], value='A')

# Display with automatic updates
slider
dropdown
```

## State Management

Marimo handles state automatically through cell dependencies:

- **Local State**: Variables within a cell scope
- **Global State**: Variables accessible across cells
- **UI State**: Interactive element states

## Performance Considerations

- **Lazy Evaluation**: Cells only run when dependencies change
- **Memoization**: Results cached to avoid redundant computation
- **Parallel Execution**: Independent cells can run simultaneously