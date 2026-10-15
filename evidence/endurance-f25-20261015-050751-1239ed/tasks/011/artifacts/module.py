"""Merge integer time intervals, compute gaps and peak concurrency.

All intervals are half-open [start, end): they include start but exclude end.
Touching endpoints do NOT overlap (e.g. [1,3] and [3,5] are disjoint).
"""
import sys
import json


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _check_int(v, label):
    """Raise ValueError unless *v* is a genuine ``int`` (not ``bool``)."""
    if isinstance(v, bool) or not isinstance(v, int):
        raise ValueError(f"{label} must be an integer")


def _validate_intervals(intervals):
    """Validate that *intervals* is a list of [start, end] pairs with
    0 <= start < end where both are plain integers."""
    if not isinstance(intervals, list):
        raise ValueError("intervals must be a list")
    for iv in intervals:
        if not isinstance(iv, (list, tuple)) or len(iv) != 2:
            raise ValueError("each interval must be a [start, end] pair")
        start, end = iv
        _check_int(start, "start")
        _check_int(end, "end")
        if start < 0 or end < 0:
            raise ValueError("start and end must be >= 0")
        if start >= end:
            raise ValueError("start must be < end")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def merge_intervals(intervals):
    """Merge overlapping and touching intervals.

    Returns a sorted list of merged tuples.  Touching intervals
    (e.g. ``[1, 3]`` and ``[3, 5]``) are merged into one.
    **Does not mutate** *intervals*.
    """
    _validate_intervals(intervals)
    if not intervals:
        return []
    sorted_iv = sorted(intervals, key=lambda x: (x[0], x[1]))
    merged = [tuple(sorted_iv[0])]
    for start, end in sorted_iv[1:]:
        prev_start, prev_end = merged[-1]
        if start <= prev_end:          # overlap or touch
            merged[-1] = (prev_start, max(prev_end, end))
        else:
            merged.append((start, end))
    return merged


def gaps(intervals, start, end):
    """Compute uncovered intervals inside window ``[start, end)``.

    Requires *start* / *end* to be integer (not bool) with ``0 <= start < end``
    and every interval fully contained in ``[start, end)``.
    Returns a sorted list of uncovered tuples.
    """
    _check_int(start, "start")
    _check_int(end, "end")
    if start < 0 or end < 0:
        raise ValueError("start and end must be >= 0")
    if start >= end:
        raise ValueError("start must be < end")
    _validate_intervals(intervals)
    for iv in intervals:
        if iv[0] < start or iv[1] > end:
            raise ValueError("all intervals must be within [start, end)")
    merged = merge_intervals(intervals)
    result = []
    current = start
    for s, e in merged:
        if s > current:
            result.append((current, s))
        current = max(current, e)
    if current < end:
        result.append((current, end))
    return result


def peak_load(intervals):
    """Maximum number of concurrently active half-open intervals.

    Touching endpoints do **not** overlap.  Empty input returns ``0``.
    """
    _validate_intervals(intervals)
    if not intervals:
        return 0
    events = []
    for start, end in intervals:
        events.append((start, 1))     # interval starts
        events.append((end, -1))      # interval ends
    events.sort()
    max_load = 0
    current_load = 0
    for _, delta in events:
        current_load += delta
        if current_load > max_load:
            max_load = current_load
    return max_load


# ---------------------------------------------------------------------------
# CLI entry-point  (python module.py)
# ---------------------------------------------------------------------------

def _cli():
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
        iv = data["intervals"]
        s = data["start"]
        e = data["end"]
    except Exception:
        sys.stderr.write("invalid input\n")
        sys.exit(2)

    try:
        merged = merge_intervals(iv)
        g = gaps(iv, s, e)
        p = peak_load(iv)
    except ValueError:
        sys.stderr.write("validation error\n")
        sys.exit(2)

    out = {
        "merged": [list(t) for t in merged],
        "gaps": [list(t) for t in g],
        "peak": p,
    }
    sys.stdout.write(json.dumps(out) + "\n")


if __name__ == "__main__":
    _cli()
