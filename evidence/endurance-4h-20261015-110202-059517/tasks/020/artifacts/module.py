"""Interval merge / gap / peak-load utility (stdlib only).

All intervals are half-open [start, end): touching endpoints do **not**
overlap — e.g. [0,2) and [2,4) are disjoint.
"""

import json
import sys
from typing import List, Tuple


def _validate_interval(pair) -> bool:
    """Return True when *pair* is a valid [start, end) integer interval."""
    if not isinstance(pair, (list, tuple)) or len(pair) != 2:
        return False
    start, end = pair
    # Reject bools (bool is subclass of int)
    if isinstance(start, bool) or isinstance(end, bool):
        return False
    if not isinstance(start, int) or not isinstance(end, int):
        return False
    if start < 0 or start >= end:
        return False
    return True


def _validate_intervals(intervals) -> None:
    """Raise ValueError when *intervals* is not a list of valid pairs."""
    if not isinstance(intervals, list):
        raise ValueError("intervals must be a list")
    for pair in intervals:
        if not _validate_interval(pair):
            raise ValueError(f"invalid interval: {pair!r}")


def merge_intervals(intervals: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Merge overlapping / touching integer half-open intervals.

    Returns sorted list of merged tuples.  Does **not** mutate *intervals*.
    """
    _validate_intervals(intervals)

    if not intervals:
        return []

    # Work on a copy of sorted intervals
    sorted_ivs = sorted(intervals, key=lambda p: (p[0], p[1]))
    merged: List[Tuple[int, int]] = [tuple(sorted_ivs[0])]

    for start, end in sorted_ivs[1:]:
        last_start, last_end = merged[-1]
        # Half-open: touch (start == last_end) => merge
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))

    return merged


def gaps(intervals: List[Tuple[int, int]], start: int, end: int) -> List[Tuple[int, int]]:
    """Return sorted uncovered half-open tuples inside [start, end).

    Requirements:
    - *start* / *end* must be int (not bool), 0 <= start < end
    - Every interval in *intervals* must lie entirely inside [start, end)
    """
    # Validate start/end
    if isinstance(start, bool) or isinstance(end, bool):
        raise ValueError("start and end must be integers (not bool)")
    if not isinstance(start, int) or not isinstance(end, int):
        raise ValueError("start and end must be integers")
    if start < 0 or start >= end:
        raise ValueError(f"0 <= start < end required, got ({start}, {end})")

    _validate_intervals(intervals)

    # Check every interval is inside the window
    for pair in intervals:
        s, e = pair
        if s < start or e > end:
            raise ValueError(
                f"interval {pair!r} is outside window [{start},{end})"
            )

    # Merge intervals first
    merged = merge_intervals(intervals)

    # Compute uncovered regions within [start, end)
    result: List[Tuple[int, int]] = []
    cursor = start

    for s, e in merged:
        if s > cursor:
            result.append((cursor, s))
        cursor = max(cursor, e)

    if cursor < end:
        result.append((cursor, end))

    return result


def peak_load(intervals: List[Tuple[int, int]]) -> int:
    """Maximum concurrent half-open intervals; touching endpoints do **not** overlap.

    Empty list -> 0.
    """
    _validate_intervals(intervals)

    if not intervals:
        return 0

    # Sweep-line: +1 at start, -1 at end
    events = []
    for s, e in intervals:
        events.append((s, 1))   # interval opens
        events.append((e, -1))  # interval closes

    # Sort by coordinate; closes before opens at same point
    # (half-open: [a,b) and [b,c) don't overlap)
    events.sort(key=lambda x: (x[0], x[1]))

    peak = 0
    current = 0
    for _, delta in events:
        current += delta
        peak = max(peak, current)

    return peak


def _cli_main():
    """Read stdin JSON {\"intervals\":[...],\"start\":int,\"end\":int} and print result JSON."""
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print("invalid JSON", file=sys.stderr)
        sys.exit(2)

    if not isinstance(data, dict):
        print("input must be a JSON object", file=sys.stderr)
        sys.exit(2)

    for key in ("intervals", "start", "end"):
        if key not in data:
            print(f"missing key: {key}", file=sys.stderr)
            sys.exit(2)

    try:
        merged = merge_intervals(data["intervals"])
        gap_result = gaps(data["intervals"], data["start"], data["end"])
        peak = peak_load(data["intervals"])
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)

    result = {
        "merged": [list(t) for t in merged],
        "gaps": [list(t) for t in gap_result],
        "peak": peak,
    }
    print(json.dumps(result))


if __name__ == "__main__":
    _cli_main()
