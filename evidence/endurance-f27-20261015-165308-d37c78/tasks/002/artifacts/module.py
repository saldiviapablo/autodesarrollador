"""Synthetic execution-report utility — stdlib only.

Provides strict input validation, Decimal-based rounding with ROUND_HALF_UP,
normalisation, summarisation, and Markdown/JSON report rendering for CLI use.

Official reference: https://docs.python.org/3/library/decimal.html
"""
import copy
import json
import sys
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

_VALID_STATUSES = frozenset({"PASS", "FAIL", "BLOCKED", "TIMEOUT"})
_TWO_PLACES = Decimal("0.01")


def round_seconds(value):
    """Round *value* to two decimal places using ROUND_HALF_UP.

    Accepts str, int, or float (bool is rejected).  Returns a formatted
    string such as ``'1.01'`` or ``'0.00'`` — negative zero normalises to
    positive zero.  Rejects negative, out-of-range, non-finite, and
    non-numeric inputs with ValueError.
    """
    if isinstance(value, bool):
        raise ValueError(f"seconds must not be bool; got {type(value).__name__}")
    if not isinstance(value, (str, int, float)):
        raise ValueError(f"seconds must be str/int/float; got {type(value).__name__}")
    try:
        d = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"invalid seconds value: {value!r}")
    if not d.is_finite():
        raise ValueError(f"seconds must be finite; got {value!r}")
    if d < 0 or d > Decimal("1000000000000"):
        raise ValueError(f"seconds out of range [0, 1e12]; got {value!r}")
    rounded = d.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
    # Normalise negative zero → positive zero
    if rounded == 0:
        rounded = Decimal("0.00")
    return format(rounded, "f")


def _validate_record(rec):
    """Validate a single record dict; raises ValueError on any problem."""
    if not isinstance(rec, dict):
        raise ValueError(f"expected dict record; got {type(rec).__name__}")
    # Exact keys only — reject extra/missing
    if set(rec.keys()) != {"id", "status", "seconds"}:
        raise ValueError(f"record must have exactly keys id/status/seconds; got {set(rec.keys())}")

    # --- id ---
    raw_id = rec.get("id")
    if not isinstance(raw_id, str):
        raise ValueError(f"id must be str; got {type(raw_id).__name__}")
    stripped = raw_id.strip()
    if not stripped:
        raise ValueError("id must be a non-empty stripped string")
    if "\r" in stripped or "\n" in stripped or "\x00" in stripped:
        raise ValueError(f"id must not contain CR/LF/NUL; got {stripped!r}")

    # --- status ---
    status = rec.get("status")
    try:
        if status not in _VALID_STATUSES:
            raise ValueError(f"status must be PASS|FAIL|BLOCKED|TIMEOUT; got {status!r}")
    except TypeError:
        raise ValueError(f"status must be a string; got {type(status).__name__}")

    # --- seconds ---
    secs = rec.get("seconds")
    if isinstance(secs, bool):
        raise ValueError("seconds must not be bool")
    if not isinstance(secs, (str, int, float)):
        raise ValueError(f"seconds must be str/int/float; got {type(secs).__name__}")
    try:
        d = Decimal(str(secs))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"invalid seconds value: {secs!r}")
    if not d.is_finite():
        raise ValueError(f"seconds must be finite; got {secs!r}")
    if d < 0 or d > Decimal("1000000000000"):
        raise ValueError(f"seconds out of range [0, 1e12]; got {secs!r}")


def normalize(records):
    """Validate, normalise and return *new* records sorted by id.

    - Each *records* item must be a dict with exactly the keys ``id``,
      ``status``, ``seconds``.
    - IDs are stripped, validated for forbidden chars, and checked for
      uniqueness (after stripping).
    - ``seconds`` is quantised to two decimal places via
      ``Decimal(str(value)).quantize(Decimal('0.01'), ROUND_HALF_UP)``.
    - The input list and its elements are never mutated.

    Returns a list of new dicts sorted by ``id``.
    Raises ValueError on any invalid input.
    """
    if not isinstance(records, list):
        raise ValueError(f"records must be list; got {type(records).__name__}")

    seen_ids = set()
    normalised = []
    for rec in records:
        _validate_record(rec)
        new_rec = {
            "id": rec["id"].strip(),
            "status": rec["status"],
            "seconds": round_seconds(rec["seconds"]),
        }
        # uniqueness after strip
        if new_rec["id"] in seen_ids:
            raise ValueError(f"duplicate id after strip: {new_rec['id']!r}")
        seen_ids.add(new_rec["id"])
        normalised.append(new_rec)

    normalised.sort(key=lambda r: r["id"])
    return normalised


def summarize(records):
    """Produce a full report summary from raw *records*.

    Returns a dict with keys ``records``, ``counts``, ``total_seconds``,
    ``max_seconds``.  Uses exact Decimal arithmetic for totals and max.
    Empty input → all counts 0, total/max ``'0.00'``.
    Raises ValueError on any invalid input.
    """
    normed = normalize(records)
    counts = {"PASS": 0, "FAIL": 0, "BLOCKED": 0, "TIMEOUT": 0}
    total = Decimal("0")
    max_d = Decimal("0")

    for rec in normed:
        counts[rec["status"]] += 1
        d = Decimal(rec["seconds"])
        total += d
        if d > max_d:
            max_d = d

    if not normed:
        return {
            "records": [],
            "counts": counts,
            "total_seconds": "0.00",
            "max_seconds": "0.00",
        }

    return {
        "records": normed,
        "counts": counts,
        "total_seconds": format(total.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP), "f"),
        "max_seconds": format(max_d.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP), "f"),
    }


def _escape_pipe(s):
    """Escape ``|`` in *s* so Markdown table cells stay well-formed."""
    return s.replace("|", r"\|")


def markdown(summary):
    """Render *summary* as a Markdown report.

    Layout:
      1. ``# Execution report``
      2. Total / Max seconds
      3. Two-column status table (PASS, FAIL, BLOCKED, TIMEOUT)
      4. Three-column records table sorted by id (pipes in IDs escaped)
    """
    lines = ["# Execution report"]
    lines.append(f"Total seconds: {summary['total_seconds']}")
    lines.append(f"Max seconds: {summary['max_seconds']}")
    lines.append("")

    # Status table
    lines.append("| Status | Count |")
    lines.append("|--------|-------|")
    for status in ("PASS", "FAIL", "BLOCKED", "TIMEOUT"):
        lines.append(f"| {status} | {summary['counts'][status]} |")
    lines.append("")

    # Records table
    lines.append("| ID | Status | Seconds |")
    lines.append("|----|--------|---------|")
    for rec in summary["records"]:
        esc_id = _escape_pipe(rec["id"])
        lines.append(f"| {esc_id} | {rec['status']} | {rec['seconds']} |")

    return "\n".join(lines) + "\n"


# ── CLI ───────────────────────────────────────────────────────────────
def _cli():
    """Minimal stdlib CLI: read stdin JSON → JSON or Markdown on stdout."""
    args = sys.argv[1:]
    markdown_mode = False

    for a in args:
        if a == "--markdown":
            markdown_mode = True
        else:
            print(f"Unknown option: {a}", file=sys.stderr)
            sys.exit(2)

    try:
        data = sys.stdin.read()
        records = json.loads(data)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"Invalid JSON input: {exc}", file=sys.stderr)
        sys.exit(2)

    # Validate top-level container
    if not isinstance(records, list):
        print("Input must be a JSON list", file=sys.stderr)
        sys.exit(2)

    try:
        summary = summarize(records)
    except ValueError as exc:
        print(f"Validation error: {exc}", file=sys.stderr)
        sys.exit(2)

    if markdown_mode:
        sys.stdout.write(markdown(summary))
    else:
        json.dump(summary, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")


if __name__ == "__main__":
    _cli()
