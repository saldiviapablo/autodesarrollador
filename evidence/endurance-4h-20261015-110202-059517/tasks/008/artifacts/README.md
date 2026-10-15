# intervals

Merge integer time intervals, compute gaps and peak concurrency.

## Semantics

All intervals are **half-open** `[start, end)`: the start point is **included**
and the end point is **excluded**.

### Touching intervals

Touching intervals such as `[1, 3)` and `[3, 5)` do **not** overlap — their
endpoints meet but never share a point.  However, `merge_intervals` **merges**
them because their union covers a contiguous span of integers.

### Peak load

`peak_load` counts maximum concurrent intervals using half-open logic.
Touching intervals never overlap; `[0, 2)` and `[2, 4)` contribute at most
`1` to the peak.

## API

| Function | Description |
|---|---|
| `merge_intervals(intervals)` | Return sorted merged `[(start, end), …]` tuples. Input is never mutated. |
| `gaps(intervals, start, end)` | Return uncovered integer segments inside the half-open window `[start, end)`. |
| `peak_load(intervals)` | Maximum number of concurrently-active intervals. Returns `0` for empty input. |

### Validation

All functions accept only plain `int` values for interval bounds.  `bool`,
floats, `None`, and out-of-range inputs raise `ValueError` with a concise
message.

- `merge_intervals`: each element must be `[start, end]` with `0 <= start < end`.
- `gaps`: additionally requires `0 <= start < end` for the window and every
  interval must lie strictly inside `[start, end)`.
- `peak_load`: same interval validation as `merge_intervals`.

## CLI usage

```bash
# Valid input
echo '{"intervals":[[1,3],[3,5]],"start":0,"end":6}' | python module.py
# Output: {"merged":[[1,5]],"gaps":[[0,1],[5,6]],"peak":1}

# Invalid input → exit code 2, concise stderr (no Traceback)
echo 'bad json' | python module.py
```

### Example: merge overlapping intervals

```python
>>> from module import merge_intervals
>>> merge_intervals([[5,8],[1,3],[3,5],[10,12]])
[(1, 8), (10, 12)]
```

### Example: gaps

```python
>>> from module import gaps
>>> gaps([[2,4],[4,6],[8,9]], 0, 10)
[(0, 2), (6, 8), (9, 10)]
```

### Example: peak load

```python
>>> from module import peak_load
>>> peak_load([[0,2],[2,4]])        # touching → peak 1
1
>>> peak_load([[0,4],[1,3],[2,5]])  # all overlap → peak 3
3
```
