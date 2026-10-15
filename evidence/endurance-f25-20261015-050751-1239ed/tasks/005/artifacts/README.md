# intervals

Merge integer time intervals, compute gaps and peak concurrency.

## API

### `merge_intervals(intervals)`

Merge overlapping or touching integer intervals.

- **Input**: iterable of `[start, end)` pairs. Each pair must contain two **int** values (not bool, not float) with `0 <= start < end`.
- **Output**: new list of sorted `(start, end)` tuples. Input is never mutated.
- **Touching semantics**: `[1,3)` and `[3,5)` are **touching** (share endpoint 3) and are merged into `(1,5)`.

### `gaps(intervals, start, end)`

Return sorted uncovered tuples inside the half-open window `[start, end)`.

- **Input**: `intervals` (same validation as above), `start` and `end` must be **int** (not bool) with `0 <= start < end`. Every interval must lie completely inside `[start, end)`.
- **Output**: list of `(u, v)` tuples representing gaps. Touching intervals are treated as continuous (no gap between `[a,b)` and `[b,c)`).
- **Example**: `gaps([[2,4],[4,6],[8,9]], 0, 10)` returns `[(0,2), (6,8), (9,10)]`.

### `peak_load(intervals)`

Return the maximum number of concurrently active half-open intervals.

- **Input**: same interval validation as `merge_intervals`.
- **Output**: integer >= 0. Returns 0 for empty input.
- **Touching semantics**: `[0,2)` and `[2,4)` do **not** overlap for concurrency purposes, so `peak_load([[0,2],[2,4]])` returns `1`.

## Input validation — `ValueError`

All functions raise `ValueError` on invalid input:

- `None`, `bool`, or non-list/tuple arguments.
- Interval pairs that are not exactly 2 elements.
- Endpoints that are not plain `int` (bool is rejected even though `bool` is a subclass of `int` in Python).
- Floats, strings, or any non-integer type.
- Intervals where `start < 0` or `start >= end`.
- For `gaps`: `start/end` outside `0 <= start < end`, or intervals lying outside the window.

## CLI usage

```bash
# Valid input
echo '{"intervals":[[1,3],[3,5]],"start":0,"end":6}' | python module.py
# Output: {"merged": [[1,5]], "gaps": [[0,1],[5,6]], "peak": 1}

# Invalid input — exit code 2
echo 'bad' | python module.py
```

The CLI reads a JSON object from stdin with keys `intervals`, `start`, `end`. It outputs a JSON object with keys `merged`, `gaps`, `peak`. On error it exits with code 2 and prints a concise message to stderr (no traceback).

## Examples

```python
from module import merge_intervals, gaps, peak_load

# Merge
merge_intervals([[5,8],[1,3],[3,5],[10,12]])  # [(1,8), (10,12)]

# Gaps
gaps([[2,4],[4,6],[8,9]], 0, 10)  # [(0,2), (6,8), (9,10)]

# Peak concurrency
peak_load([[0,4],[1,3],[2,5]])  # 3 (all three overlap at t=2)
peak_load([[0,2],[2,4]])        # 1 (touching, not overlapping)
```
