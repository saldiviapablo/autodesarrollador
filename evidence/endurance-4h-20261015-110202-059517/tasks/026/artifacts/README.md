# intervals

Merge integer time intervals, compute gaps and peak concurrency.

## API

### `merge_intervals(intervals) → List[Tuple[int, int]]`

Merge overlapping and **touching** intervals into a sorted list of
disjoint `(start, end)` tuples.

* **Input:** list of `[start, end]` pairs where every element is a plain
  ``int`` (`bool` is rejected via ``ValueError``).
* **Semantics:** half-open intervals ``[start, end)``.  Touching intervals
  are merged (``[0,2)`` + ``[2,4)`` → ``[0,4)``).
* **Immutable:** the input list is never mutated.
* **Validation:** raises ``ValueError`` for non-list input, non-``int``
  endpoints (including ``bool``), ``start >= end``, or ``start < 0``.

```python
>>> merge_intervals([[5, 8], [1, 3], [3, 5], [10, 12]])
[(1, 8), (10, 12)]
```

### `gaps(intervals, start, end) → List[Tuple[int, int]]`

Return the uncovered portions of the window ``[start, end)`` after
merging *intervals*.

* **Input:**
  * *intervals* — list of valid `[s, e]` pairs, **all** of which must lie
    fully inside ``[start, end)``.
  * *start*, *end* — plain ``int``, ``0 <= start < end``.
* **Semantics:** half-open intervals.  Touching intervals are merged
  before computing gaps.
* **Validation:** raises ``ValueError`` for invalid windows, endpoints
  outside the window, or non-``int`` / ``bool`` arguments.

```python
>>> gaps([[2, 4], [4, 6], [8, 9]], 0, 10)
[(0, 2), (6, 8), (9, 10)]
```

### `peak_load(intervals) → int`

Return the maximum number of simultaneously active half-open intervals.

* **Touching endpoints do not overlap:** ``[0,2)`` and ``[2,4)`` contribute
  at most **1** concurrent interval.
* Returns ``0`` for an empty list.

```python
>>> peak_load([[0, 4], [1, 3], [2, 5]])
3
>>> peak_load([[0, 2], [2, 4]])
1
```

## CLI

```bash
echo '{"intervals":[[1,3],[3,5]],"start":0,"end":6}' | python module.py
```

**Output:**

```json
{"merged": [[1, 5]], "gaps": [[0, 1], [5, 6]], "peak": 1}
```

Invalid input → exit code **2** with a concise one-line message on stderr
(no Python traceback).

## Half-open interval semantics

Every interval ``[start, end)`` includes its start point and excludes its
end point.  Two intervals that merely **touch** at a boundary (e.g.
``[0,2)`` and ``[2,4)``) do **not** overlap, but they **are merged** by
`merge_intervals` and `gaps` because the boundary point ``2`` is already
covered.

| Intervals | Overlap? | Merged? | Peak |
|-----------|----------|---------|------|
| ``[0,2)`` + ``[2,4)`` | No (touching) | Yes | 1 |
| ``[0,2)`` + ``[1,3)`` | Yes (overlap) | Yes | 2 |
| ``[0,2)`` + ``[3,5)`` | No (gap) | No | 1 |

## Running tests

```bash
python test_module.py
python build.py
```

Both must exit with code 0.
