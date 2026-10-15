# intervals

Merge integer time intervals, compute uncovered gaps, and measure peak concurrency.

## Semantics

All intervals are **half-open** `[start, end)`: the start point is inclusive, the end point is exclusive.  
Consequences:

* **Touching endpoints do not overlap.** `[0, 2)` and `[2, 4)` are disjoint — they cover two unit slots but never share a point.
* Merging: touching intervals **are** merged (e.g. `[0,2)` + `[2,4)` → `[0,4)`).
* `peak_load`: only truly overlapping half-open intervals contribute to concurrency.

### Examples

```
merge_intervals([[0,2],[2,4]])        → [(0,4)]   # touching → merge
merge_intervals([[0,2],[3,5]])        → [(0,2),(3,5)]  # gap between
peak_load([[0,2],[2,4]])              → 1           # no overlap
peak_load([[0,4],[1,3]])              → 2           # [1,3) inside [0,4)
gaps([[2,4],[4,6]], 0, 8)            → [(0,2),(6,8)] # uncovered edges
```

## API

| Function | Signature | Returns |
|---|---|---|
| `merge_intervals` | `(intervals: list[tuple[int,int]]) → list[tuple[int,int]]` | Sorted merged tuples |
| `gaps` | `(intervals, start: int, end: int) → list[tuple[int,int]]` | Uncovered half-open tuples in `[start, end)` |
| `peak_load` | `(intervals) → int` | Max concurrent intervals (0 for empty) |

**Validation**: all public functions raise `ValueError` for invalid input (bools, non-integers, negative starts, `start >= end`, intervals outside the window for `gaps`).

## CLI

```bash
echo '{"intervals":[[1,3],[3,5]],"start":0,"end":6}' | python module.py
```

Output (JSON):

```json
{"merged":[[1,5]],"gaps":[[0,1],[5,6]],"peak":1}
```

Invalid input → exit code **2** with a concise error on stderr (no traceback).
