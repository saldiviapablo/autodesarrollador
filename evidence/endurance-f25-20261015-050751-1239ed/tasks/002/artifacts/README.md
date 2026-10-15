# intervals

Merge integer time intervals, compute uncovered gaps, and measure peak concurrency.

## API

### `merge_intervals(intervals) -> list[tuple[int, int]]`

Accepts a list of `[start, end]` pairs and returns a sorted list of **merged**
tuples.  Overlapping intervals **and** touching intervals (e.g. `[1,3)` and
`[3,5)`) are merged into a single continuous interval.  The input list is **not
mutated**.

**Example**

```python
>>> merge_intervals([[5, 8], [1, 3], [3, 5], [10, 12]])
[(1, 8), (10, 12)]
```

### `gaps(intervals, start, end) -> list[tuple[int, int]]`

Returns the sorted list of **uncovered** sub-intervals inside the window
`[start, end)`.  Every interval in *intervals* must lie completely within the
window.

**Example**

```python
>>> gaps([[2, 4], [4, 6], [8, 9]], 0, 10)
[(0, 2), (6, 8), (9, 10)]
```

### `peak_load(intervals) -> int`

Returns the **maximum number of simultaneously active** half-open intervals.
Touching endpoints do **not** overlap because intervals are half-open
`[start, end)`.  An empty list returns `0`.

**Example**

```python
>>> peak_load([[0, 4], [1, 3], [2, 5]])
3
>>> peak_load([[0, 2], [2, 4]])  # touching, not overlapping
1
```

## Input validation — `ValueError`

All three functions validate their inputs and raise `ValueError` (exit code 2
via the CLI) when:

- `intervals` is not a list, or contains elements that are not two-element
  lists/tuples.
- Interval values are not plain `int` (``bool`` is rejected even though
  `bool` is a subclass of `int` in Python).
- `start >= end` or `start < 0`.
- For `gaps()`: an interval lies outside the requested `[start, end)` window,
  or `start/end` themselves are invalid.

## CLI usage

`module.py` reads JSON from **stdin** and writes a JSON object to **stdout**.

```bash
echo '{"intervals":[[1,3],[3,5]],"start":0,"end":6}' | python module.py
```

**Output**

```json
{
  "merged": [[1, 5]],
  "gaps": [[0, 1], [5, 6]],
  "peak": 1
}
```

Invalid input (malformed JSON, missing keys, bad values) produces a concise
error message on **stderr** and exits with code **2**.

## Half-open / touching semantics

All intervals are treated as **half-open** `[start, end)`:

| Aspect | Rule |
|--------|------|
| Membership | `t` belongs to `[a, b)` iff `a <= t < b` |
| Overlap | `[1,3)` and `[3,5)` → **no** overlap (3 is excluded from the first) |
| `merge_intervals` | Touching intervals **are** merged because they form a continuous span |
| `peak_load` | Touching intervals count as **concurrent = 1** (the end of one coincides with the start of the next, but they do not overlap) |
| `gaps` | The window is `[start, end)`; uncovered regions are reported as tuples |

### Worked example

```
Intervals:  [1,4), [3,6), [5,8)
Merged:     [1,8)                ← all three overlap at some point
Gaps [0,10): [(0,1), (8,10)]    ← nothing covers [0,1) or [8,10)
Peak:       3                    ← at t=5 both [3,6) and [5,8) are active (plus [1,4) ended at 4)
```

## Running tests and build

```bash
python test_module.py
python build.py
```

Both must exit with code 0.

## Constraints

- Python standard library only (no third-party dependencies).
- UTF-8 encoding without BOM.
- No modification of `test_module.py`, `build.py`, `.autopilot/`, or any
  external files.
