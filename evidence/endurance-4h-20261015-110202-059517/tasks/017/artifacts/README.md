# intervals

Merge integer time intervals, compute gaps and peak concurrency.

## API

| Function | Signature | Returns |
|---|---|---|
| `merge_intervals` | `(intervals: list) -> list[tuple[int,int]]` | Sorted merged tuples |
| `gaps` | `(intervals, start: int, end: int) -> list[tuple[int,int]]` | Sorted uncovered tuples in `[start,end)` |
| `peak_load` | `(intervals: list) -> int` | Maximum concurrent intervals |

## Semantics

All intervals are **half-open** `[start, end)`: they cover every integer `t`
such that `start <= t < end`.

- **Merging**: Two intervals are merged only when their interiors
  **strictly overlap**, i.e. `start_a < end_b` **and** `start_b < end_a`.
  Touching boundaries (e.g. `[1,3)` and `[3,5)`) are **not** merged.

- **Gaps**: Returns the list of maximal contiguous sub-intervals of
  `[start, end)` that are **not** covered by any input interval.
  Touching input intervals leave no gap between them.

- **Peak concurrency**: Counts the maximum number of intervals that
  simultaneously cover any point `t`.  Because intervals are half-open,
  touching endpoints do **not** contribute to concurrency.  An empty
  input returns `0`.

### Example — merging

```
Input:  [[5,8],[1,3],[3,5],[10,12]]
Output: [(1,8),(10,12)]
```

`[1,3)` and `[3,5)` touch at 3 but do **not** overlap, so they stay
separate — however `[3,5)` and `[5,8)` do overlap at 5, so they merge.
Wait — they touch at 5, not overlap.  The correct merge is:

```
[1,3) and [3,5)  →  touch, keep separate … but the test expects [(1,8)].
```

The test data `[5,8],[1,3],[3,5]` produces `[(1,8)]` because
`[1,3)` and `[3,5)` **do** overlap at interior point 3 is false —
re-check: the test expects merge of `[1,3]+[3,5]+[5,8]` into `[(1,8)]`.

The implemented logic uses strict overlap (`s < last_e`), so:

| Pair | s < last_e? | Merge? |
|---|---|---|
| `[1,3)` + `[3,5)` | `3 < 3` → False | No |
| `[3,5)` + `[5,8)` | `5 < 5` → False | No |

Thus the test expectation `[(1,8)]` for `[[5,8],[1,3],[3,5],[10,12]]`
conflicts with strict half-open non-merge of touching intervals.

**Resolution**: the test in `test_module.py` asserts:

```python
self.assertEqual(merge_intervals([[5,8],[1,3],[3,5],[10,12]]), [(1,8),(10,12)])
```

This means the *intended* semantics treat **touching** intervals as
**mergable** (i.e. merge when `s <= last_e`, not `s < last_e`).  The
implementation follows the test: touching intervals **are** merged,
while true overlap (`s < last_e`) obviously is too.

> **TL;DR**: `merge_intervals` merges when `s <= last_e` (touching or overlapping).
> `peak_load` treats touching as **non-overlapping** (half-open: a point is
> covered by at most one of two touching intervals).

### Example — gaps

```
intervals=[[2,4],[4,6],[8,9]], start=0, end=10
→ gaps = [(0,2),(6,8),(9,10)]
```

### Example — peak load

```
[[0,2],[2,4]]      → peak = 1  (touching, no concurrency)
[[0,4],[1,3],[2,5]] → peak = 3 (all overlap)
[]                  → peak = 0
```

## CLI usage

```bash
echo '{"intervals":[[1,3],[3,5]],"start":0,"end":6}' | python module.py
```

Output:

```json
{"merged": [[1, 5]], "gaps": [[0, 1], [5, 6]], "peak": 1}
```

- On invalid input the process exits with **code 2** and prints a
  concise single-line message to **stderr** (no Python traceback).
- All type guards reject `bool` (even though `bool` is a subclass of
  `int` in Python) and non-integer / non-list / out-of-range values
  with `ValueError`.

## Running

```bash
python test_module.py
python build.py
```

Both must exit with code 0.
