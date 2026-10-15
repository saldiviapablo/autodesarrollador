"""Interval arithmetic: merge, gaps, peak concurrency.

All intervals use half-open semantics [start, end).
Touching endpoints merge in merge_intervals but do not overlap in peak_load.
"""

import json
import sys
from typing import List, Tuple


def _check_int(v, label: str = "value") -> None:
    """Raise ValueError if *v* is a bool or not an int."""
    if isinstance(v, bool):
        raise ValueError(f"{label} must be int, not bool")
    if not isinstance(v, int):
        raise ValueError(f"{label} must be int")


def _check_non_negative_int(v, label: str = "value") -> None:
    """Raise ValueError if *v* is bool/non-int or < 0."""
    _check_int(v, label)
    if v < 0:
        raise ValueError(f"{label} must be >= 0")


def _validate_pair(pair, index: int) -> Tuple[int, int]:
    """Validate a single [start, end] pair and return (start, end)."""
    if not isinstance(pair, (list, tuple)):
        raise ValueError(f"interval[{index}] must be a list/tuple")
    if len(pair) != 2:
        raise ValueError(f"interval[{index}] must have exactly 2 elements")
    start, end = pair
    _check_non_negative_int(start, f"interval[{index}].start")
    _check_non_negative_int(end, f"interval[{index}].end")
    if start >= end:
        raise ValueError(
            f"interval[{index}]: start ({start}) must be < end ({end})"
        )
    return start, end


def merge_intervals(intervals: list) -> List[Tuple[int, int]]:
    """Merge overlapping and touching integer intervals.

    Args:
        intervals: list of [start, end] pairs where 0 <= start < end.

    Returns:
        Sorted list of merged tuples.  Does **not** mutate *intervals*.

    Semantics:
        - Touching intervals merge: [1,2] + [2,3] -> [(1,3)].
        - Overlapping intervals merge: [1,4] + [3,6] -> [(1,6)].
    """
    if not isinstance(intervals, (list, tuple)):
        raise ValueError("intervals must be a list")

    parsed: List[Tuple[int, int]] = []
    for i, iv in enumerate(intervals):
        parsed.append(_validate_pair(iv, i))

    if not parsed:
        return []

    parsed.sort()
    merged: List[Tuple[int, int]] = [parsed[0]]

    for start, end in parsed[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            # Overlapping or touching -> merge
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))

    return merged


def gaps(intervals: list, start: int, end: int) -> List[Tuple[int, int]]:
    """Compute uncovered segments in [start, end) given *intervals*.

    Args:
        intervals: list of [start, end] pairs, all fully contained in
                   [global_start, global_end).
        start: window start (integer >= 0).
        end: window end (integer > start).

    Returns:
        Sorted list of uncovered tuples within [start, end).

    Raises:
        ValueError: on invalid inputs or if any interval falls outside
                    the [start, end) window.
    """
    _check_non_negative_int(start, "start")
    _check_non_negative_int(end, "end")
    if start >= end:
        raise ValueError("start must be < end")

    merged = merge_intervals(intervals)

    # Verify every merged interval lies inside [start, end)
    for s, e in merged:
        if s < start or e > end:
            raise ValueError(
                f"interval ({s},{e}) outside window [{start},{end})"
            )

    # Collect uncovered segments within [start, end)
    result: List[Tuple[int, int]] = []
    cursor = start

    for s, e in merged:
        if s > cursor:
            result.append((cursor, s))
        cursor = max(cursor, e)

    if cursor < end:
        result.append((cursor, end))

    return result


def peak_load(intervals: list) -> int:
    """Maximum concurrent half-open intervals.

    Args:
        intervals: list of [start, end] pairs where 0 <= start < end.

    Returns:
        Integer peak concurrency.  Touching endpoints do **not** overlap.
        Returns 0 for empty input.

    Semantics:
        - [1,2] and [2,3] overlap count = 1 (half-open).
        - [0,4],[1,3],[2,5] overlap count = 3.
    """
    if not isinstance(intervals, (list, tuple)):
        raise ValueError("intervals must be a list")

    if not intervals:
        return 0

    parsed: List[Tuple[int, int]] = []
    for i, iv in enumerate(intervals):
        parsed.append(_validate_pair(iv, i))

    events: List[Tuple[int, int]] = []
    for start, end in parsed:
        events.append((start, 1))   # interval starts
        events.append((end, -1))    # interval ends

    # Sort by position; ends before starts at same position (half-open)
    events.sort(key=lambda x: (x[0], x[1]))

    peak = 0
    current = 0
    for _, delta in events:
        current += delta
        peak = max(peak, current)

    return peak


def _cli_main() -> None:
    """CLI entry-point: read JSON from stdin, write JSON to stdout."""
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print("invalid JSON input", file=sys.stderr)
        sys.exit(2)

    try:
        intervals = data["intervals"]
        start = data["start"]
        end = data["end"]
    except KeyError:
        print("missing required keys: intervals, start, end", file=sys.stderr)
        sys.exit(2)

    try:
        merged = merge_intervals(intervals)
        gap_result = gaps(intervals, start, end)
        peak = peak_load(intervals)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)

    output = {
        "merged": [list(t) for t in merged],
        "gaps": [list(t) for t in gap_result],
        "peak": peak,
    }
    print(json.dumps(output))


if __name__ == "__main__":
    _cli_main()
