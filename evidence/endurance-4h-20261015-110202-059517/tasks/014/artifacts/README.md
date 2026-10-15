# intervals — Merge, gaps, and peak concurrency

Utility module for merging integer time intervals, computing uncovered gaps, and determining peak concurrency.

## API

### `merge_intervals(intervals)`

Merges overlapping and touching intervals from a list of `[start, end)` pairs.

- **Input:** `intervals` — list of 2-element lists/tuples `[start, end]` where `0 <= start < end` and both are `int` (not `bool`).
- **Output:** List of sorted merged tuples.
- **Semantics:** Half-open intervals `[start, end)`. Touching intervals (e.g. `[1,3)` and `[3,5)`) are **merged** into one (`[1,5)`).
- **Immutability:** Does not mutate the input list.
- **Errors:** Raises `ValueError` on invalid input.

**Example:**
```python
>>> merge_intervals([[5, 8], [1, 3], [3, 5], [10, 12]])
[(1, 8), (10, 12)]
```

### `gaps(intervals, start, end)`

Returns sorted uncovered `[s, e)` tuples within the window `[start, end)`.

- **Input:** 
  - `intervals` — list of valid intervals, all must lie entirely within `[start, end)`.
  - `start` — window start (int, not bool, `>= 0`).
  - `end` — window end (int, not bool, `> start`).
- **Output:** List of sorted uncovered tuples.
- **Errors:** Raises `ValueError` if window is invalid or any interval lies outside the window.

**Example:**
```python
>>> gaps([[2, 4], [4, 6], [8, 9]], 0, 10)
[(0, 2), (6, 8), (9, 10)]
```

### `peak_load(intervals)`

Computes the maximum number of concurrent half-open intervals.

- **Input:** `intervals` — list of valid interval pairs.
- **Output:** Integer peak concurrency (0 for empty input).
- **Semantics:** Half-open `[s, e)`. Touching endpoints do **not** overlap.

**Example:**
```python
>>> peak_load([[0, 4], [1, 3], [2, 5]])
3
>>> peak_load([[0, 2], [2, 4]])
1  # touching, not overlapping
```

## Half-open / Touching Semantics

All functions use **half-open interval** semantics `[start, end)`:
- The start point is **included**.
- The end point is **excluded**.
- Touching intervals like `[1, 3)` and `[3, 5)` do **not** overlap in `peak_load` (peak = 1).
- Touching intervals **are merged** in `merge_intervals` (merged result: `[1, 5)`).

This matches standard interval arithmetic and ensures consistent behavior across all three functions.

## CLI Usage

Reads JSON from `stdin`, outputs JSON to `stdout`:

```bash
echo '{"intervals":[[1,3],[3,5]],"start":0,"end":6}' | python module.py
```

**Output:**
```json
{"merged": [[1, 5]], "gaps": [[0, 1], [5, 6]], "peak": 1}
```

**Error handling:** Invalid JSON or invalid intervals produce a concise error message on `stderr` and exit with code **2**.

## Requirements

- Python 3.x (stdlib only)
- No external dependencies
