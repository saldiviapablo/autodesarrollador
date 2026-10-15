# intervals — Merge, gaps and peak concurrency

Python module (`module.py`) that provides three core functions for working
with integer half-open time intervals `[start, end)`.

## Half-open / touching semantics

Every interval is **half-open**: it includes `start` but **excludes** `end`.
Consequently, **touching endpoints do not overlap**.

| Intervals | Overlap? | Merged result |
|---|---|---|
| `[1, 3]` and `[3, 5]` | No (3 excluded from both) | `[1, 5]` — touched, so merged |
| `[1, 3]` and `[4, 6]` | No (gap at 3, 4) | `[1, 3]`, `[4, 6]` |
| `[1, 5]` and `[3, 7]` | Yes (3, 4 overlap) | `[1, 7]` |

> **Touching** (`end_a == start_b`) is treated as "merge" in `merge_intervals`.
> **Concurrency** in `peak_load` respects the half-open rule: `[1,3)` and `[3,5)` never overlap, so they contribute 1 to the peak, not 2.

## API

### `merge_intervals(intervals)`

Merges a list of `[start, end]` pairs.  Overlapping and touching intervals
are fused.  Returns a sorted list of tuples.  **Does not mutate** the input.

```python
>>> merge_intervals([[5, 8], [1, 3], [3, 5], [10, 12]])
[(1, 8), (10, 12)]
```

**Validation** — raises `ValueError` for:

- Non-list input
- Elements that are not 2-element lists/tuples
- Non-integer values (booleans, floats, strings)
- `start < 0` or `end < 0` or `start >= end`

### `gaps(intervals, start, end)`

Computes intervals within `[start, end)` that are **not** covered by any
input interval.  All input intervals must lie fully inside the window.

```python
>>> gaps([[2, 4], [4, 6], [8, 9]], 0, 10)
[(0, 2), (6, 8), (9, 10)]
```

**Validation** — raises `ValueError` for non-integer `start`/`end`,
`start >= end`, or intervals outside the window.

### `peak_load(intervals)`

Maximum number of **concurrently active** intervals at any point.
Uses half-open semantics — touching endpoints do not count as overlap.

```python
>>> peak_load([[0, 4], [1, 3], [2, 5]])
3
>>> peak_load([[0, 2], [2, 4]])   # touching, no overlap
1
```

## CLI usage

```bash
# Valid input
echo '{"intervals":[[1,3],[3,5]],"start":0,"end":6}' | python module.py
# → {"merged":[[1,5]],"gaps":[[0,1],[5,6]],"peak":1}

# Invalid input → exit code 2, concise error on stderr
echo 'bad' | python module.py; echo $?
# → 2
```

## Run tests

```bash
python test_module.py
python build.py
```
