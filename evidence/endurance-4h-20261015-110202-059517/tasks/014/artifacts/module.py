"""Merge integer time intervals, compute gaps and peak concurrency.

All intervals use half-open semantics [start, end): the start point is
included and the end point is excluded. Touching intervals (e.g. [1,3)
and [3,5)) do NOT overlap and therefore are NOT merged.
"""
import json
import sys
from pathlib import Path


def _validate_interval(pair):
    """Validate a single interval: must be exactly (int, int) and not bool,
    with 0 <= start < end."""
    if not isinstance(pair, (list, tuple)) or len(pair) != 2:
        raise ValueError(f"interval must be a 2-element list/tuple, got {pair!r}")
    start, end = pair
    for v in (start, end):
        if isinstance(v, bool) or not isinstance(v, int):
            raise ValueError(f"interval elements must be int (not bool), got {v!r}")
    if start < 0:
        raise ValueError(f"start must be >= 0, got {start}")
    if start >= end:
        raise ValueError(f"start must be < end, got ({start}, {end})")


def _validate_intervals(intervals):
    """Validate that intervals is a list of valid interval pairs."""
    if not isinstance(intervals, list):
        raise ValueError(f"intervals must be a list, got {intervals!r}")
    for iv in intervals:
        _validate_interval(iv)


def merge_intervals(intervals):
    """Return sorted merged tuples from a list of [start, end) intervals.

    Overlapping and touching intervals are merged into one.
    Does not mutate the input list.

    Raises ValueError on invalid input.
    """
    _validate_intervals(intervals)
    if not intervals:
        return []

    # Work on a copy to avoid mutating input
    sorted_ivs = sorted(intervals, key=lambda x: (x[0], x[1]))
    merged = [tuple(sorted_ivs[0])]

    for start, end in sorted_ivs[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            # Overlapping or touching: merge
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))

    return merged


def gaps(intervals, start, end):
    """Return sorted uncovered [s, e) tuples within the window [start, end).

    Args:
        intervals: list of [start, end) intervals.
        start: window start (int, not bool, >= 0).
        end: window end (int, not bool, > start).

    Every interval must lie entirely within [start, end).

    Raises ValueError on invalid input.
    """
    # Validate start/end
    for v, name in ((start, "start"), (end, "end")):
        if isinstance(v, bool) or not isinstance(v, int):
            raise ValueError(f"{name} must be int (not bool), got {v!r}")
    if start < 0:
        raise ValueError(f"start must be >= 0, got {start}")
    if start >= end:
        raise ValueError(f"start must be < end, got ({start}, {end})")

    _validate_intervals(intervals)

    # Check every interval is inside [start, end)
    for iv in intervals:
        iv_start, iv_end = iv
        if iv_start < start or iv_end > end:
            raise ValueError(
                f"interval {iv} is outside window [{start}, {end})"
            )

    # Filter intervals to those inside the window (already validated above)
    sorted_ivs = sorted(intervals, key=lambda x: (x[0], x[1]))

    uncovered = []
    current = start

    for iv_start, iv_end in sorted_ivs:
        if iv_start > current:
            uncovered.append((current, iv_start))
        current = max(current, iv_end)

    if current < end:
        uncovered.append((current, end))

    return uncovered


def peak_load(intervals):
    """Return maximum concurrent half-open intervals.

    Touching endpoints do NOT overlap (half-open semantics [s, e)).
    Returns 0 for empty input.

    Raises ValueError on invalid input.
    """
    _validate_intervals(intervals)
    if not intervals:
        return 0

    # Create events: (+1 at start, -1 at end)
    events = []
    for start, end in intervals:
        events.append((start, 1))   # interval starts
        events.append((end, -1))    # interval ends

    # Sort by time; for half-open semantics, end (-1) comes before start (+1)
    # when times are equal, so touching intervals don't overlap.
    events.sort(key=lambda x: (x[0], x[1]))

    max_load = 0
    current_load = 0
    for _, delta in events:
        current_load += delta
        max_load = max(max_load, current_load)

    return max_load


if __name__ == "__main__":
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
        intervals = data["intervals"]
        start = data["start"]
        end = data["end"]

        merged = merge_intervals(intervals)
        gap_list = gaps(intervals, start, end)
        peak = peak_load(intervals)

        result = {
            "merged": [list(t) for t in merged],
            "gaps": [list(t) for t in gap_list],
            "peak": peak,
        }
        print(json.dumps(result))
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)
