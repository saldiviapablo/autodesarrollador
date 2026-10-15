# intervals

## Overview

Python stdlib-only CLI utility that **merges integer time intervals**, **computes uncovered gaps** within a user-specified window, and **measures peak concurrency**.

## API

### `merge_intervals(intervals) -> List[Tuple[int, int]]`

Merge overlapping intervals. Returns a sorted list of `(start, end)` tuples.

**Notation:** intervals are **half-open** `[start, end)`.  
Two intervals touch when one's `start` equals the other's `end` (e.g. `[1, 3)` and `[3, 5)`).  
**Touching intervals are treated as non-overlapping** and are NOT merged.

**Example:**
```python
>>> merge_intervals([[1, 3], [2, 6], [8, 10]])
[(1, 6), (8, 10)]
```

### `gaps(intervals, start, end) -> List[Tuple[int, int]]`

Return sorted uncovered `(a, b)` tuples inside the window `[start, end)`.

**Constraints:**
- `start`, `end` must be **integers** (not `bool`), `0 <= start < end`.
- Every interval in `intervals` must lie within `[start, end)` or a `ValueError` is raised.

**Example:**
```python
>>> gaps([[2, 4], [6, 8]], 0, 10)
[(0, 2), (4, 6), (8, 10)]
```

### `peak_load(intervals) -> int`

Maximum number of **concurrently active** half-open intervals.  
Touching endpoints do **not** overlap. Empty input returns `0`.

**Example:**
```python
>>> peak_load([[0, 4], [1, 3], [2, 5]])
3
>>> peak_load([[0, 2], [2, 4]])
1  # touching, not overlapping
```

## CLI

```bash
python module.py
```

Reads JSON from stdin:
```json
{"intervals": [[1, 3], [3, 5]], "start": 0, "end": 6}
```

Outputs JSON to stdout:
```json
{"merged": [[1, 3], [3, 5]], "gaps": [[0, 1], [5, 6]], "peak": 1}
```

- Invalid JSON → exit code `2`, concise stderr message.
- Missing/invalid fields → exit code `2`, concise stderr message.

## Validation

All functions reject invalid input by raising `ValueError`:

| Invalid input | Reason |
|---|---|
| `True` / `False` | `bool` is not accepted as an integer |
| `1.5` (float) | Only `int` allowed |
| `[-1, 2]` | start must be >= 0 |
| `[2, 1]` | start < end violated |
| `[0, 1, 2]` | not a 2-element pair |
| `'bad'` | not a list of pairs |

## Installation

```bash
pip install -r requirements.txt
```

## Running tests

```bash
python test_module.py
python build.py
```

## Half-open interval semantics (summary)

- An interval `[a, b)` covers all integers `t` such that `a <= t < b`.
- **Overlap:** `[a, b)` overlaps `[c, d)` iff `c < b` AND `a < d`.
- **Touching:** `[a, b)` and `[b, c)` touch at `b` but do **not** overlap.
- **Peak concurrency** counts overlapping (not touching) intervals.
- **Merge** combines only overlapping intervals; touching intervals stay separate.
