# intervals

Merge integer time intervals, compute gaps and peak concurrency.

## API

### `merge_intervals(intervals)`

Merge overlapping and touching intervals. Returns a new sorted list of `(start, end)` tuples.

- Intervals are **half-open** `[start, end)` — end is exclusive.
- Touching intervals (e.g. `[1,3)` and `[3,5)`) are merged into `[1,5)`.
- Does **not** mutate the input list.
- Raises `ValueError` on invalid input (non-int, bool, negative start, start >= end).

```python
>>> merge_intervals([[5, 8], [1, 3], [3, 5], [10, 12]])
[(1, 8), (10, 12)]
```

### `gaps(intervals, start, end)`

Return sorted uncovered tuples within the window `[start, end)`.

- `start`, `end` must be plain `int` with `0 <= start < end`.
- Every interval must lie completely inside the window.
- Raises `ValueError` on invalid input or out-of-range intervals.

```python
>>> gaps([[2, 4], [4, 6], [8, 9]], 0, 10)
[(0, 2), (6, 8), (9, 10)]
```

### `peak_load(intervals)`

Maximum number of concurrent half-open intervals. Touching endpoints do **not** overlap. Empty → `0`.

```python
>>> peak_load([[0, 2], [2, 4]])
1
>>> peak_load([[0, 4], [1, 3], [2, 5]])
3
```

## CLI

```bash
echo '{"intervals":[[1,3],[3,5]],"start":0,"end":6}' | python module.py
```

Output (JSON):

```json
{"merged": [[1, 5]], "gaps": [[0, 1], [5, 6]], "peak": 1}
```

Invalid input → exit code `2` with concise error on stderr (no traceback).

## Semantics

- **Half-open intervals**: `[start, end)` includes `start`, excludes `end`.
- **Touching**: `[a,b)` and `[b,c)` touch at `b` but do not overlap.
  - `merge_intervals` merges them (contiguous).
  - `peak_load` counts them as non-overlapping (concurrency = 1 at the touch point).
- **Immutability**: `merge_intervals` and `gaps` return new lists; original input is never mutated.
