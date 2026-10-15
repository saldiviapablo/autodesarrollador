# catalog — Portable File Catalog Validator & Duplicate Detector

Validate a portable file catalog and report duplicates **without filesystem access**. All operations are pure Python in memory.

## API

### `catalog(entries) -> list[dict]`

Accepts a list of dicts with exactly three keys: `path`, `size`, `sha256`. Validates every field, rejects duplicates, and returns a **new** list sorted by `path`.

**Validation rules:**

| Field   | Contract |
|---------|----------|
| `path`  | Non-empty POSIX relative path. No backslash `\`, colon `:`, leading `/`, empty component (`//`), `.` or `..`, NUL `\x00`, or newline `\n`. Unicode is allowed (e.g. `ñ`, `中文`, `café`). |
| `size`  | Integer `>= 0`. `bool` is explicitly forbidden (`bool` is a subclass of `int` in Python). |
| `sha256`| Exactly 64 lowercase hexadecimal characters (`[0-9a-f]`). |

**Raises:** `ValueError` on any malformed entry, disallowed path, duplicate path, unexpected keys, or if `entries` is not a list of dicts.

**Invariants:**
- Never mutates the input list or its dicts (returns deep-copied results).
- Never accesses the filesystem.

### `duplicate_groups(entries) -> list[list[str]]`

Validates `entries` via `catalog()`, then groups paths sharing the same `(size, sha256)` tuple.

**Returns:** A list of lists. Each inner list contains paths (sorted lexicographically) for one duplicate group with `>= 2` members. The outer list is sorted lexicographically by the first path in each group. Returns `[]` when no duplicates exist.

**Example:**

```python
>>> from module import catalog, duplicate_groups
>>> entries = [
...     {'path': 'a.txt', 'size': 100, 'sha256': 'a' * 64},
...     {'path': 'b.txt', 'size': 200, 'sha256': 'b' * 64},
...     {'path': 'c.txt', 'size': 100, 'sha256': 'a' * 64},  # same size+hash as a.txt
...     {'path': 'd.txt', 'size': 300, 'sha256': 'c' * 64},
... ]
>>> catalog(entries)
[{'path': 'a.txt', ...}, {'path': 'b.txt', ...}, {'path': 'c.txt', ...}, {'path': 'd.txt', ...}]
>>> duplicate_groups(entries)
[['a.txt', 'c.txt']]
```

## Unicode handling

Paths may contain any Unicode characters except the forbidden control characters (NUL, newline, carriage-return). The function uses Python 3 native strings (UTF-8 internally). Sorting is by Unicode code point order, which is deterministic and reproducible.

**Examples:**

```python
>>> catalog([{'path': 'café.txt', 'size': 0, 'sha256': 'a' * 64}])
[{'path': 'café.txt', 'size': 0, 'sha256': 'a' * 64}]
>>> catalog([{'path': '中文/文件.txt', 'size': 0, 'sha256': 'a' * 64}])
[{'path': '中文/文件.txt', 'size': 0, 'sha256': 'a' * 64}]
```

## CLI

```bash
echo '[{"path":"readme.md","size":42,"sha256":"'"$(python -c 'print("a"*64)'"'")}]' | python module.py
```

**Input:** JSON array on stdin, e.g. `[{"path":"a","size":1,"sha256":"abc..."}, ...]`

**Output (stdout):** JSON object with two keys:
```json
{"catalog": [...], "duplicates": [...]}
```
`ensure_ascii=False` — Unicode characters are emitted as-is (not escaped).

**Exit codes:**
- `0` — Success; valid catalog produced.
- `2` — Invalid input (JSON decode error, validation error). Concise error message on stderr (no Python traceback).

**CLI error example:**

```bash
$ echo 'not json' | python module.py
error: Expecting value: line 1 column 1 (char 0)
# exit code: 2
```

## No filesystem I/O

Neither `catalog()` nor `duplicate_groups()` performs any filesystem access. They operate exclusively on in-memory data structures. This makes them safe for use in sandboxed environments, CI pipelines, or any context where filesystem access is restricted or undesirable.

## Quick start

```bash
# Install (no external deps required — uses only Python standard library)
# python 3.8+

# Run tests
python test_module.py

# Run build check (AST validation)
python build.py

# Use from CLI
echo '[{"path":"file.txt","size":100,"sha256":"a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1"}]' | python module.py
```
