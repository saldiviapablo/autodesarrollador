# catalog

Validate a portable file catalog and report duplicates — **without filesystem access**.

## Installation

No external dependencies required.  Python 3.6+ is sufficient.

## Usage

```python
from module import catalog, duplicate_groups

entries = [
    {"path": "docs/a.txt", "size": 1024, "sha256": "a" * 64},
    {"path": "src/b.txt", "size": 1024, "sha256": "a" * 64},
    {"path": "tmp/c.txt", "size": 512,  "sha256": "b" * 64},
]

validated = catalog(entries)
# → [{"path": "docs/a.txt", ...}, {"path": "src/b.txt", ...}, ...]

duplicates = duplicate_groups(validated)
# → [["docs/a.txt", "src/b.txt"]]
```

## CLI

```bash
echo '[{"path":"z","size":1,"sha256":"a"*64}]' | python module.py
# → {"catalog":[...],"duplicates":[]}
```

Reads a JSON array from **stdin**, writes ``{"catalog": ..., "duplicates": ...}`` to **stdout** with ``ensure_ascii=False``.  Exits **0** on success, **2** on validation error (concise message on stderr, no traceback).

## Contract

### `catalog(entries)`

| Aspect    | Detail |
|-----------|--------|
| **Input**  | ``entries`` — a list of dicts, each with exactly the keys ``path``, ``size``, ``sha256``. |
| **Output** | A **new** list of dicts sorted by ``path`` (ascending).  Input is never mutated. |
| **Errors** | Raises ``ValueError`` on malformed entries or duplicate paths. |

#### Path validation

- Must be a non-empty string.
- POSIX relative: **no** leading slash, **no** backslash, **no** colon.
- **No** empty components (``a//b`` is invalid), **no** ``.`` or ``..`` components.
- **No** NUL (``\x00``) or newline (``\n``) characters.
- **Unicode is fully supported** (e.g. ``ñ``, ``中文``, ``📄``).

#### Size validation

- Must be an ``int`` ≥ 0.
- ``bool`` is explicitly forbidden (``isinstance(True, int)`` is ``True`` in Python).
- Floats such as ``1.5`` are rejected.

#### SHA-256 validation

- Must be exactly 64 lowercase hexadecimal characters.
- Uppercase letters, wrong length, or non-hex characters are rejected.

#### Duplicate-path detection

- If two or more entries share the same ``path``, a ``ValueError`` is raised immediately.

### `duplicate_groups(entries)`

| Aspect    | Detail |
|-----------|--------|
| **Input**  | A *validated* catalog (output of ``catalog``). |
| **Output** | A list of groups; each group is a sorted list of ``path`` strings that share the same ``(size, sha256)`` pair. |
| **Filter** | Only groups with ``>= 2`` members are included. |
| **Sorting** | Paths within each group are sorted lexicographically; groups are sorted by their first element. |

## Examples

### Duplicate detection

```python
entries = [
    {"path": "a", "size": 100, "sha256": "aa" * 32},
    {"path": "z", "size": 100, "sha256": "aa" * 32},
    {"path": "b", "size": 200, "sha256": "bb" * 32},
    {"path": "c", "size": 200, "sha256": "bb" * 32},
    {"path": "unique", "size": 300, "sha256": "cc" * 32},
]

duplicate_groups(catalog(entries))
# → [["a", "z"], ["b", "c"]]
```

### Unicode paths

```python
entries = [
    {"path": "ñ/b.txt", "size": 42, "sha256": "ff" * 32},
    {"path": "a.txt",   "size": 42, "sha256": "ff" * 32},
]

catalog(entries)
# → [{"path": "a.txt", ...}, {"path": "ñ/b.txt", ...}]
```

### Rejected inputs

``ValueError`` is raised for:

| Invalid value                | Reason                        |
|------------------------------|-------------------------------|
| ``path = ""``                | Empty string                  |
| ``path = "/x"``              | Leading slash                 |
| ``path = "../x"``            | ``..`` component              |
| ``path = "./a"``             | ``.`` component               |
| ``path = "a//b"``            | Empty component               |
| ``path = "C:x"``             | Colon (Windows drive letter)  |
| ``path = "a\\b"``            | Backslash                     |
| ``path = "a\nb"``            | Newline                       |
| ``size = True``              | Bool forbidden                |
| ``size = -1``                | Negative                      |
| ``size = 1.5``               | Float                         |
| ``sha256 = "A" * 64``        | Uppercase hex                 |
| ``sha256 = "a" * 63``        | Wrong length                  |
| duplicate ``path`` values    | Duplicate path                |
| dict with extra keys         | Exact key set required        |

## No filesystem I/O

This module performs **zero** filesystem operations.  All validation and duplicate detection is performed entirely in memory.  It is suitable for auditing portable catalogs without touching disk.

## Running tests and build

```bash
python test_module.py
python build.py
```

Both must exit 0.
