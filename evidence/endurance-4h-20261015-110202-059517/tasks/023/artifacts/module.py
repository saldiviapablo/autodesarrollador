"""Merge integer time intervals, compute gaps and peak concurrency.

Semantics
---------
All intervals are **half-open** [start, end).  Touching intervals such as
[0, 2) and [2, 4) do **not** overlap — they share endpoint 2 but never
occupy the same point.  When merging, touching intervals *are* merged
because the union [0, 2) ∪ [2, 4) = [0, 4) is contiguous.

Peak concurrency counts how many half-open intervals cover each integer
t; two intervals touching at an endpoint never contribute simultaneously.

Examples
--------
>>> merge_intervals([[1, 3], [2, 4], [6, 8]])
[(1, 4), (6, 8)]

>>> gaps([[2, 4], [4, 6]], 0, 8)
[(0, 2), (6, 8)]

>>> peak_load([[0, 2], [1, 3], [2, 4]])
2  # [0,2) and [1,3) overlap; [2,4) touches but does not overlap with [1,3)
"""
import json
import sys
from pathlib import Path


def _validate_interval(interval):
    """Validate a single interval is a list/tuple of two ints (not bool) with 0<=start<end."""
    if not isinstance(interval, (list, tuple)):
        raise ValueError(f"interval must be a list or tuple, got {type(interval).__name__}")
    if len(interval) != 2:
        raise ValueError(f"interval must have exactly 2 elements, got {len(interval)}")
    start, end = interval
    if isinstance(start, bool) or isinstance(end, bool):
        raise ValueError("interval values must be int, not bool")
    if not isinstance(start, int) or not isinstance(end, int):
        raise ValueError("interval values must be int")
    if start < 0:
        raise ValueError(f"start must be >= 0, got {start}")
    if start >= end:
        raise ValueError(f"start must be < end, got [{start}, {end})")


def _validate_intervals(intervals):
    """Validate the entire intervals list."""
    if not isinstance(intervals, (list, tuple)):
        raise ValueError("intervals must be a list or tuple")
    for interval in intervals:
        _validate_interval(interval)


def merge_intervals(intervals):
    """Merge overlapping and touching integer intervals.

    Args:
        intervals: list of [start, end] pairs where 0 <= start < end and both are int (not bool).

    Returns:
        List of merged tuples sorted by start time.

    Raises:
        ValueError: if any interval is invalid.
    """
    _validate_intervals(intervals)

    if not intervals:
        return []

    # Work on a copy of sorted intervals
    sorted_intervals = sorted(intervals, key=lambda x: (x[0], x[1]))
    merged = [tuple(sorted_intervals[0])]

    for start, end in sorted_intervals[1:]:
        last_start, last_end = merged[-1]
        # Touching or overlapping: merge (half-open [start, end) with touching allowed)
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))

    return merged


def gaps(intervals, start, end):
    """Compute gaps (uncovered regions) within [start, end) window.

    Args:
        intervals: list of [start, end] pairs (valid, all within [start, end) window).
        start: integer start of window (not bool).
        end: integer end of window (not bool), start < end.

    Returns:
        List of gap tuples within the window not covered by any interval.

    Raises:
        ValueError: if arguments are invalid or intervals fall outside window.
    """
    # Validate start/end
    if isinstance(start, bool) or isinstance(end, bool):
        raise ValueError("start and end must be int, not bool")
    if not isinstance(start, int) or not isinstance(end, int):
        raise ValueError("start and end must be int")
    if start < 0 or start >= end:
        raise ValueError(f"window requires 0 <= start < end, got [{start}, {end})")

    _validate_intervals(intervals)

    # Check all intervals are within window
    for interval in intervals:
        iv_start, iv_end = interval
        if iv_start < start or iv_end > end:
            raise ValueError(
                f"interval [{iv_start}, {iv_end}) outside window [{start}, {end})"
            )

    # Merge intervals within window
    merged = merge_intervals(intervals)

    # Find gaps
    result = []
    current = start

    for iv_start, iv_end in merged:
        if iv_start > current:
            result.append((current, iv_start))
        current = max(current, iv_end)

    # Remaining gap after last interval
    if current < end:
        result.append((current, end))

    return result


def peak_load(intervals):
    """Compute maximum concurrent half-open intervals.

    Touching intervals [a, b) and [b, c) do NOT overlap.

    Args:
        intervals: list of [start, end] pairs (valid).

    Returns:
        Integer max concurrency. 0 for empty input.

    Raises:
        ValueError: if any interval is invalid.
    """
    _validate_intervals(intervals)

    if not intervals:
        return 0

    # Sweep-line: collect events
    events = []
    for start, end in intervals:
        events.append((start, 1))   # interval starts
        events.append((end, -1))    # interval ends

    # Sort by position; for ties, process ends (-1) before starts (1)
    # This ensures touching intervals don't count as overlapping
    events.sort(key=lambda x: (x[0], x[1]))

    max_load = 0
    current_load = 0
    for _, delta in events:
        current_load += delta
        max_load = max(max_load, current_load)

    return max_load


def _cli_main():
    """CLI entry point: read JSON from stdin, write JSON to stdout."""
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        sys.stderr.write("error: invalid JSON input\n")
        sys.exit(2)

    if not isinstance(data, dict):
        sys.stderr.write("error: JSON input must be an object\n")
        sys.exit(2)

    intervals = data.get("intervals")
    start = data.get("start")
    end = data.get("end")

    try:
        merged = merge_intervals(intervals)
        gap_list = gaps(intervals, start, end)
        peak = peak_load(intervals)
    except ValueError as exc:
        sys.stderr.write(f"error: {exc}\n")
        sys.exit(2)

    result = {
        "merged": [list(t) for t in merged],
        "gaps": [list(t) for t in gap_list],
        "peak": peak,
    }
    print(json.dumps(result))


if __name__ == "__main__":
    _cli_main()
