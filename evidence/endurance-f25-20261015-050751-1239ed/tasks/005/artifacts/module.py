"""Merge integer time intervals, compute gaps and peak concurrency.

Semantics
---------
All intervals are **half-open** ``[start, end)``. Two intervals ``[a,b)`` and
``[b,c)`` touch at *b* but do **not** overlap — they are merged by
``merge_intervals`` / ``gaps`` because touching endpoints share a boundary
that eliminates any gap between them.  ``peak_load`` treats touching endpoints
as **non-overlapping** (concurrency does not increase at the shared point).

Input validation
----------------
- ``merge_intervals`` / ``peak_load`` accept a single positional argument: an
  iterable of interval pairs.  Each pair must be exactly two **int** (not bool)
  values ``0 <= start < end``.  Anything else raises ``ValueError``.
- ``gaps`` accepts ``(intervals, start, end)``.  ``start`` and ``end`` must be
  **int** (not bool) with ``0 <= start < end``.  Every interval in *intervals*
  must satisfy ``start <= interval[0]`` and ``interval[1] <= end``.  Invalid
  inputs raise ``ValueError``.

CLI
---
Run as a module: ``python module.py``
Reads a JSON object from stdin with keys ``intervals``, ``start``, ``end``.
Outputs a JSON object with keys ``merged``, ``gaps``, ``peak``.
On invalid input exits with code 2 and a concise stderr message.
"""

import sys
import json
import copy
from typing import List, Tuple


def _is_int(val: object) -> bool:
    """Return True if *val* is a plain ``int`` (not ``bool``)."""
    return isinstance(val, int) and not isinstance(val, bool)


def _validate_interval(pair: object) -> None:
    """Raise ``ValueError`` if *pair* is not a valid ``[start, end)``."""
    if not isinstance(pair, (list, tuple)):
        raise ValueError("interval must be a list or tuple")
    if len(pair) != 2:
        raise ValueError("interval must have exactly 2 elements")
    s, e = pair
    if not _is_int(s) or not _is_int(e):
        raise ValueError("interval endpoints must be int (not bool/float)")
    if s < 0 or s >= e:
        raise ValueError(f"invalid interval {pair}: need 0<=start<end")


def _validate_intervals(intervals: object) -> List[Tuple[int, int]]:
    """Validate and return *intervals* as a sorted list of tuples."""
    if intervals is None or isinstance(intervals, (bool, str)):
        raise ValueError("intervals must be a list/tuple of pairs")
    if not isinstance(intervals, (list, tuple)):
        raise ValueError("intervals must be a list/tuple of pairs")
    result: List[Tuple[int, int]] = []
    for pair in intervals:
        _validate_interval(pair)
        result.append((pair[0], pair[1]))
    result.sort()
    return result


def merge_intervals(intervals: object) -> List[Tuple[int, int]]:
    """Merge overlapping or touching integer intervals.

    Returns a new list of sorted ``(start, end)`` tuples.  The input is not
    mutated.  Touching intervals ``[a,b),[b,c)`` are merged into ``[a,c)``.

    Raises ``ValueError`` on invalid input.
    """
    validated = _validate_intervals(intervals)
    if not validated:
        return []

    merged: List[Tuple[int, int]] = [validated[0]]
    for start, end in validated[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            # Overlap or touch — extend
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def gaps(
    intervals: object,
    start: object,
    end: object,
) -> List[Tuple[int, int]]:
    """Return sorted uncovered tuples inside the half-open window ``[start, end)``.

    Requirements
    ------------
    * *start* and *end* must be **int** (not bool) with ``0 <= start < end``.
    * Every interval in *intervals* must lie completely inside ``[start, end)``.

    Returns a new list of ``(u, v)`` tuples representing gaps.  Touching
    intervals are treated as continuous (no gap between ``[a,b)`` and ``[b,c)``).

    Raises ``ValueError`` on invalid input.
    """
    if not _is_int(start) or not _is_int(end):
        raise ValueError("gaps start/end must be int (not bool/float)")
    if start < 0 or start >= end:
        raise ValueError(f"invalid gap window: need 0<=start<end, got ({start},{end})")

    validated = _validate_intervals(intervals)

    # Check every interval lies inside [start, end)
    for s, e in validated:
        if s < start or e > end:
            raise ValueError(
                f"interval ({s},{e}) lies outside window ({start},{end})"
            )

    merged = merge_intervals(intervals)
    result: List[Tuple[int, int]] = []
    cursor = start

    for s, e in merged:
        if s > cursor:
            result.append((cursor, s))
        cursor = max(cursor, e)

    if cursor < end:
        result.append((cursor, end))

    return result


def peak_load(intervals: object) -> int:
    """Return the maximum number of concurrently active half-open intervals.

    Touching endpoints do **not** overlap for concurrency purposes:
    ``[0,2)`` and ``[2,4)`` give peak 1.

    Returns ``0`` for an empty input.

    Raises ``ValueError`` on invalid input.
    """
    validated = _validate_intervals(intervals)
    if not validated:
        return 0

    events: List[Tuple[int, int]] = []
    for s, e in validated:
        events.append((s, 1))   # interval starts
        events.append((e, -1))  # interval ends

    # Sort by position; ends before starts at the same point
    events.sort(key=lambda x: (x[0], x[1]))

    peak = 0
    current = 0
    for _, delta in events:
        current += delta
        peak = max(peak, current)

    return peak


# ── CLI entry point ───────────────────────────────────────────────
def _cli() -> None:
    """Read JSON from stdin, print result to stdout. Exit 2 on error."""
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
        intervals = data["intervals"]
        start = data["start"]
        end = data["end"]
    except Exception as exc:
        print(f"invalid input: {exc}", file=sys.stderr)
        sys.exit(2)

    try:
        merged = merge_intervals(intervals)
        gap_result = gaps(intervals, start, end)
        peak = peak_load(intervals)
    except ValueError as exc:
        print(f"validation error: {exc}", file=sys.stderr)
        sys.exit(2)

    result = {
        "merged": [list(t) for t in merged],
        "gaps": [list(t) for t in gap_result],
        "peak": peak,
    }
    print(json.dumps(result))


if __name__ == "__main__":
    _cli()
