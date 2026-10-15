# intervals

Interval arithmetic for integer time ranges. Provides three core functions:

- **`merge_intervals(intervals)`** — Merge overlapping and touching intervals.
- **`gaps(intervals, start, end)`** — Compute uncovered segments within a window.
- **`peak_load(intervals)`** — Maximum concurrent half-open intervals.

## Semantics

All functions use **half-open interval** semantics `[start, end)`:

- The interval includes `start` but excludes `end`.
- Example: `[1, 3)` covers time points 1 and 2, but not 3.

### Touching endpoints

| Function | Behaviour | Example |
|---|---|---|
| `merge_intervals` | Touching intervals **merge** | `[1,2] + [2,3]` → `[(1,3)]` |
| `peak_load` | Touching endpoints **do not overlap** | `[1,2] + [2,3]` → peak = 1 |

### Input validation

- All interval endpoints must be **integers** (not `bool`, not float).
- Constraint: `0 <= start < end`.
- Invalid input raises **`ValueError`** with a concise message.
- CLI mode exits with **code 2** on validation errors.

## API

### `merge_intervals(intervals) -> List[Tuple[int, int]]`

Merges overlapping and touching intervals. Returns sorted list of tuples. Does **not** mutate the input list.

```python
>>> merge_intervals([[5, 8], [1, 3], [3, 5], [10, 12]])
[(1, 8), (10, 12)]
>>> merge_intervals([])
[]
```

### `gaps(intervals, start, end) -> List[Tuple[int, int]]`

Computes uncovered segments within `[start, end)`. All intervals must lie inside the window.

```python
>>> gaps([[2, 4], [4, 6], [8, 9]], 0, 10)
[(0, 2), (6, 8), (9, 10)]
>>> gaps([], 0, 3)
[(0, 3)]
>>> gaps([[0, 3]], 0, 3)
[]
```

### `peak_load(intervals) -> int`

Maximum number of concurrent active intervals at any point. Uses half-open semantics — touching endpoints do not overlap. Returns 0 for empty input.

```python
>>> peak_load([[0, 2], [2, 4]])
1
>>> peak_load([[0, 4], [1, 3], [2, 5]])
3
>>> peak_load([])
0
```

## CLI

Run as a Python module. Reads JSON from `stdin`, writes JSON to `stdout`.

**Input format:**
```json
{
  "intervals": [[1, 3], [3, 5]],
  "start": 0,
  "end": 6
}
```

**Output format:**
```json
{
  "merged": [[1, 5]],
  "gaps": [[0, 1], [5, 6]],
  "peak": 1
}
```

**Usage:**
```bash
python module.py
```

**Error handling:** Invalid JSON or validation errors produce a concise message on `stderr` and exit code **2**. No traceback is shown.

## Requirements

- Python 3.x (stdlib only).
- No external dependencies.

## Running tests

```bash
python test_module.py
python build.py
```
