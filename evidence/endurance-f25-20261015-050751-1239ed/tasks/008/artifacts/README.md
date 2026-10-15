# intervals — Merge, gaps, and peak concurrency

Python utility for merging integer time intervals, computing uncovered gaps,
and determining peak concurrency.

## API

### `merge_intervals(intervals)`

Merge overlapping and touching half-open intervals `[start, end)`.

- **Input:** list of `[start, end)` pairs (integers, `0 <= start < end`)
- **Output:** sorted list of merged tuples
- **Raises:** `ValueError` on invalid input (including bools as integers)
- **Immutability:** does not mutate the input list
- **Touching semantics:** intervals that touch (e.g. `(1, 4)` and `(4, 6)`) are merged into one.

**Example**

```python
>>> merge_intervals([(1, 4), (4, 6), (7, 8)])
[(1, 6), (7, 8)]

>>> merge_intervals([(0, 2), (2, 4)])
[(0, 4)]
```

### `gaps(intervals, start, end)`

Compute uncovered time within a window `[start, end)` relative to the given intervals.

- **Input:** 
  - `intervals`: list of `[start, end)` pairs
  - `start, end`: window boundaries (integers, `0 <= start < end`)
- **Output:** sorted list of uncovered `[start, end)` tuples within the window
- **Raises:** `ValueError` on invalid input or if intervals fall outside the window
- **Touching semantics:** touching intervals are merged before computing gaps.

**Example**

```python
>>> gaps([(2, 4), (4, 6)], 0, 8)
[(0, 2), (6, 8)]

>>> gaps([], 0, 3)
[(0, 3)]
```

### `peak_load(intervals)`

Compute maximum concurrent intervals using half-open `[start, end)` semantics.

- **Input:** list of `[start, end)` pairs (integers)
- **Output:** integer maximum concurrency; `0` for empty input
- **Raises:** `ValueError` on invalid input
- **Touching semantics:** touching endpoints do **not** overlap.  
  E.g. `(0, 2)` and `(2, 4)` → `peak_load == 1`.

**Example**

```python
>>> peak_load([(0, 2), (1, 3), (2, 4)])
2

>>> peak_load([(0, 2), (2, 4)])
1
```

## Validation

All functions reject:

- Non-integer values (floats, strings)
- `bool` values (even though `bool` is a subclass of `int` in Python)
- Intervals where `start >= end` or `start < 0`
- Wrong types (e.g., passing a string instead of a list)

Invalid input raises `ValueError` with a concise message.

## CLI

`module.py` reads JSON from **stdin** and outputs JSON to **stdout**.

**Input format**

```json
{
  "intervals": [[1, 3], [3, 5]],
  "start": 0,
  "end": 6
}
```

**Output format**

```json
{
  "merged": [[1, 5]],
  "gaps": [[0, 1], [5, 6]],
  "peak": 1
}
```

**Run**

```bash
echo '{"intervals":[[1,3],[3,5]],"start":0,"end":6}' | python module.py
```

**Error handling**

- Invalid JSON → exit code `2`, concise error to stderr
- Invalid intervals/window → exit code `2`, concise error to stderr
- No `Traceback` in error output

## Testing

```bash
python test_module.py
python build.py
```

Both must exit with code `0`.
