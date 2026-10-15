# intervals

Merge integer time intervals, compute gaps and peak concurrency.

## API

### `merge_intervals(intervals)`

Merge overlapping and **touching** integer intervals.

- **Input:** `list[list[int, int]]` where each pair satisfies `0 <= start < end`.
- **Output:** `list[tuple[int, int]]` sorted by start time.
- **Semantics:** Intervals are **half-open** `[start, end)`. Touching intervals
  such as `[0, 2)` and `[2, 4)` are merged into `[0, 4)` because their union
  is contiguous.
- **Immutability:** Does not mutate the input list.
- **Validation:** Raises `ValueError` for invalid input (bools, floats,
  negative values, start >= end, wrong types).

**Example:**

```python
>>> merge_intervals([[1, 3], [2, 4], [6, 8]])
[(1, 4), (6, 8)]
>>> merge_intervals([[5, 8], [1, 3], [3, 5], [10, 12]])
[(1, 8), (10, 12)]
```

### `gaps(intervals, start, end)`

Compute uncovered regions (gaps) within the half-open window `[start, end)`.

- **Input:**
  - `intervals`: valid list of intervals, all contained within `[start, end)`.
  - `start`: integer, `0 <= start`.
  - `end`: integer, `start < end`.
  - `start` and `end` must be `int` (not `bool`).
- **Output:** `list[tuple[int, int]]` of uncovered sub-ranges within the window.
- **Validation:** Raises `ValueError` if `start >= end`, if `start`/`end` are
  not int, or if any interval falls outside the window.

**Example:**

```python
>>> gaps([[2, 4], [4, 6], [8, 9]], 0, 10)
[(0, 2), (6, 8), (9, 10)]
>>> gaps([[0, 3]], 0, 3)
[]
```

### `peak_load(intervals)`

Compute maximum concurrent intervals. Touching endpoints do **not** overlap.

- **Input:** `list[list[int, int]]` of valid intervals.
- **Output:** `int` — maximum number of intervals covering any point. `0` for
  empty input.
- **Semantics:** Half-open `[start, end)`. `[0, 2)` and `[2, 4)` touch at 2
  but never overlap, so peak = 1.

**Example:**

```python
>>> peak_load([[0, 2], [2, 4]])
1
>>> peak_load([[0, 4], [1, 3], [2, 5]])
3
>>> peak_load([])
0
```

## CLI Usage

Read JSON from stdin, write JSON to stdout:

```bash
echo '{"intervals":[[1,3],[3,5]],"start":0,"end":6}' | python module.py
```

Output:

```json
{"merged": [[1, 5]], "gaps": [[0, 1], [5, 6]], "peak": 1}
```

Invalid input (malformed JSON, bad types, `ValueError` in validation) exits
with code `2` and a concise error message on stderr.

## Validation Rules

| Input | Valid? | Reason |
|-------|--------|--------|
| `[0, 5]` | ✅ | int, 0 <= start < end |
| `[True, 5]` | ❌ | bool rejected |
| `[0, 1.5]` | ❌ | float rejected |
| `[-1, 3]` | ❌ | negative start |
| `[5, 5]` | ❌ | start == end |
| `[5, 3]` | ❌ | start > end |

## Run Tests

```bash
python test_module.py
python build.py
```

Both must exit with code 0.
