"""Merge integer time intervals, compute gaps and peak concurrency.

Semantics
---------
All intervals are **half-open** `[start, end)`: they include *start* but
exclude *end*.  Touching intervals such as `[0,2)` and `[2,4)` do **not**
overlap and must **not** be merged by ``peak_load`` (they are merged by
``merge_intervals`` because they share an endpoint).

Input validation
----------------
* ``intervals`` must be a list of ``[start, end]`` pairs where
  ``0 <= start < end`` and both values are plain ``int`` (``bool`` is
  rejected).
* ``gaps(intervals, start, end)`` additionally requires
  ``0 <= start < end`` and every interval to lie completely inside
  ``[start, end)``.
* Violations raise ``ValueError`` with a short message on stderr.
"""
import json, sys
from pathlib import Path


def _validate_interval(pair):
    """Raise ValueError if *pair* is not a valid ``[int, int]``."""
    if not isinstance(pair, (list, tuple)) or len(pair) != 2:
        raise ValueError("interval must be a two-element list")
    start, end = pair
    if isinstance(start, bool) or isinstance(end, bool):
        raise ValueError("bool values are not accepted")
    if not isinstance(start, int) or not isinstance(end, int):
        raise ValueError("interval values must be plain int")
    if start < 0 or start >= end:
        raise ValueError("must have 0 <= start < end")


def merge_intervals(intervals):
    """Return sorted list of merged tuples.

    Overlapping and touching intervals are merged into a single interval.
    Input is **not** mutated.
    """
    if not isinstance(intervals, list):
        raise ValueError("intervals must be a list")
    for pair in intervals:
        _validate_interval(pair)

    if not intervals:
        return []

    # Work on a sorted copy of (start, end) tuples
    sorted_iv = sorted((pair[0], pair[1]) for pair in intervals)
    merged = [sorted_iv[0]]

    for start, end in sorted_iv[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:  # overlap or touch
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))

    return merged


def gaps(intervals, start, end):
    """Return sorted list of uncovered tuples inside ``[start, end)``.

    Every interval in *intervals* must lie completely within ``[start, end)``.
    """
    # Validate start/end
    if isinstance(start, bool) or isinstance(end, bool):
        raise ValueError("start/end must be plain int")
    if not isinstance(start, int) or not isinstance(end, int):
        raise ValueError("start/end must be plain int")
    if start < 0 or start >= end:
        raise ValueError("must have 0 <= start < end")

    if not isinstance(intervals, list):
        raise ValueError("intervals must be a list")
    for pair in intervals:
        _validate_interval(pair)
        # Check interval is inside [start, end)
        if pair[0] < start or pair[1] > end:
            raise ValueError("interval must lie inside [start, end)")

    # Merge intervals first
    merged = merge_intervals(intervals)

    # Find uncovered regions
    result = []
    current = start
    for s, e in merged:
        if current < s:
            result.append((current, s))
        if e > current:
            current = e
    if current < end:
        result.append((current, end))

    return result


def peak_load(intervals):
    """Return maximum number of simultaneously active half-open intervals.

    Touching endpoints do **not** overlap (half-open semantics).
    ``[]`` returns ``0``.
    """
    if not isinstance(intervals, list):
        raise ValueError("intervals must be a list")
    for pair in intervals:
        _validate_interval(pair)

    if not intervals:
        return 0

    events = []
    for s, e in intervals:
        events.append((s, 1))   # interval starts
        events.append((e, -1))  # interval ends

    events.sort(key=lambda x: (x[0], x[1]))

    peak = current = 0
    for _, delta in events:
        current += delta
        if current > peak:
            peak = current

    return peak


# ── CLI ───────────────────────────────────────────────────────────────
def _cli():
    """Read JSON from stdin, print JSON result, exit 2 on invalid input."""
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
        intervals = data["intervals"]
        start = data["start"]
        end = data["end"]

        merged = merge_intervals(intervals)
        gap_list = gaps(intervals, start, end)
        pk = peak_load(intervals)

        result = {
            "merged": [list(t) for t in merged],
            "gaps": [list(t) for t in gap_list],
            "peak": pk,
        }
        print(json.dumps(result))
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    _cli()
