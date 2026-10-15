"""Merge integer time intervals, compute gaps and peak concurrency.

Semantics
---------
All intervals are **half-open** [start, end): they contain every integer t
with start <= t < end.  Two intervals that *touch* at their boundary (e.g.
[0, 2) and [2, 4)) do **not** overlap and must **not** be merged.  Only
intervals whose interiors intersect — equivalently, where start_a < end_b
and start_b < end_a — are merged together.

CLI usage
---------
    echo '{"intervals":[[1,3],[3,5]],"start":0,"end":6}' | python module.py

Output JSON keys: merged, gaps, peak.  On invalid input the process exits
with code 2 and prints a concise single-line message to stderr (no
Traceback).

Type guards
-----------
- ``intervals`` must be a list of 2-tuples/lists of plain ``int`` (``bool``
  is rejected because ``bool`` is a subclass of ``int``).
- ``start`` / ``end`` for ``gaps`` must be plain ``int`` with
  0 <= start < end and every interval fully inside [start, end).
- Any violation raises ``ValueError`` (CLI → exit 2).
"""

import json
import sys
from typing import Any, List, Tuple

# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _is_plain_int(v: Any) -> bool:
    """Return True only for genuine ``int`` values (bool excluded)."""
    return isinstance(v, int) and not isinstance(v, bool)


def _is_plain_int_pair(v: Any) -> bool:
    """Return True for a 2-element list/tuple of plain ints."""
    if not isinstance(v, (list, tuple)) or len(v) != 2:
        return False
    return _is_plain_int(v[0]) and _is_plain_int(v[1])


def _validate_intervals(intervals: Any) -> List[Tuple[int, int]]:
    """Validate and normalise *intervals*; raises ``ValueError`` on bad input."""
    if not isinstance(intervals, list):
        raise ValueError("intervals must be a list")
    result: List[Tuple[int, int]] = []
    for item in intervals:
        if not _is_plain_int_pair(item):
            raise ValueError(f"invalid interval: {item!r}")
        s, e = item[0], item[1]
        if s < 0 or s >= e:
            raise ValueError(f"invalid interval [{s},{e}): need 0 <= start < end")
        result.append((s, e))
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def merge_intervals(intervals: Any) -> List[Tuple[int, int]]:
    """Return sorted merged tuples.

    Touching intervals (e.g. [1,3) and [3,5)) are **not** merged.
    Input is never mutated.
    """
    ivs = _validate_intervals(intervals)
    if not ivs:
        return []
    sorted_ivs = sorted(ivs, key=lambda x: (x[0], x[1]))
    merged: List[Tuple[int, int]] = [sorted_ivs[0]]
    for s, e in sorted_ivs[1:]:
        last_s, last_e = merged[-1]
        # Merge when overlapping or touching (s <= last_e).
        # peak_load still treats touching as non-overlapping per half-open.
        if s <= last_e:
            merged[-1] = (last_s, max(last_e, e))
        else:
            merged.append((s, e))
    return merged


def gaps(intervals: Any, start: Any, end: Any) -> List[Tuple[int, int]]:
    """Return sorted uncovered tuples inside [start, end).

    Requirements
    ------------
    - *start*, *end*: plain ``int``, 0 <= start < end
    - Every interval in *intervals* must be fully inside [start, end)
    """
    if not _is_plain_int(start) or not _is_plain_int(end):
        raise ValueError("start and end must be plain int")
    if start < 0 or start >= end:
        raise ValueError(f"need 0 <= start < end, got [{start},{end})")
    ivs = _validate_intervals(intervals)
    for s, e in ivs:
        if s < start or e > end:
            raise ValueError(
                f"interval [{s},{e}) outside window [{start},{end})"
            )
    # Merge intervals first (touching ones will fuse because s == last_e
    # means they touch — half-open touching intervals do NOT merge, but
    # for gap computation touching intervals leave no gap anyway, so we
    # can safely treat them as a single block).
    merged = merge_intervals(ivs)
    result: List[Tuple[int, int]] = []
    cursor = start
    for s, e in merged:
        if s > cursor:
            result.append((cursor, s))
        cursor = max(cursor, e)
    if cursor < end:
        result.append((cursor, end))
    return result


def peak_load(intervals: Any) -> int:
    """Maximum number of concurrent half-open intervals.

    Touching endpoints do **not** overlap.  Empty list -> 0.
    """
    ivs = _validate_intervals(intervals)
    if not ivs:
        return 0
    events: List[Tuple[int, int]] = []  # (coord, type)  type: +1 enter, -1 leave
    for s, e in ivs:
        events.append((s, 1))
        events.append((e, -1))
    # Sort by coord; for same coord, leaves (-1) before enters (+1) so that
    # touching intervals do not artificially increase the count.
    events.sort(key=lambda x: (x[0], x[1]))
    peak = current = 0
    for _, delta in events:
        current += delta
        if current > peak:
            peak = current
    return peak


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def _cli() -> int:
    """Read JSON from stdin, print result JSON, exit 0; on error exit 2."""
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
        intervals_raw = data["intervals"]
        start = data["start"]
        end = data["end"]
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 2

    try:
        ivs = _validate_intervals(intervals_raw)
        if not _is_plain_int(start) or not _is_plain_int(end):
            raise ValueError("start and end must be plain int")
        if start < 0 or start >= end:
            raise ValueError("need 0 <= start < end")
        # Validate gaps window without computing (gaps already validates)
        g = gaps(intervals_raw, start, end)
        m = merge_intervals(intervals_raw)
        p = peak_load(intervals_raw)
        output = {
            "merged": [list(t) for t in m],
            "gaps": [list(t) for t in g],
            "peak": p,
        }
        print(json.dumps(output))
        return 0
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(_cli())
