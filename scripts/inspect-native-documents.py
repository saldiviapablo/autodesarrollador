"""Inventory and real native read_file calls in the installed Hermes runtime."""
import hashlib
import importlib.metadata
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, sys.argv[1])
os.environ["HERMES_DISABLE_LAZY_INSTALLS"] = "1"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
temp = ROOT / "sandbox/phase7a3-documents/temp"
temp.mkdir(parents=True, exist_ok=True)
os.environ["TMP"] = os.environ["TEMP"] = str(temp)
import tempfile
tempfile.tempdir = str(temp)

# This is inspection/extraction only: no LLM, hosted OCR, or external networking.
def no_network(event, args):
    if event in {"socket.connect", "socket.getaddrinfo"}:
        raise PermissionError("DOCUMENT_EXTRACTION_NETWORK_DENIED")


sys.addaudithook(no_network)
from tools import read_extract
from tools.file_tools import read_file_tool

fixture_root = ROOT / "sandbox/phase7a3-documents/fixtures"
packages = {}
for package in ["firecrawl-anydoc", "PyYAML", "pypdf", "openpyxl"]:
    try: packages[package] = importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError: packages[package] = None
records = []
for n, suffix in enumerate(["md", "json", "yaml", "docx", "xlsx", "pdf", "rtf"]):
    f = fixture_root / ("spec." + suffix)
    try:
        native = json.loads(read_file_tool(str(f), task_id="doc-inventory-7a3-" + suffix))
        passed = "DA_DOCUMENT_SPEC_7A3" in str(native.get("content", "")) and not native.get("error")
        records.append({"format": suffix, "status": "PASS" if passed else "FAIL", "result": native})
    except Exception as exc:
        records.append({"format": suffix, "status": "FAIL", "error": type(exc).__name__ + ": " + str(exc)})
report = {"test_id": "T-7A-DOC-001", "native_module": str(pathlib.Path(read_extract.__file__)),
          "native_source_sha256": hashlib.sha256(pathlib.Path(read_extract.__file__).read_bytes()).hexdigest(),
          "python": sys.version.split()[0], "packages_already_installed": packages,
          "records": records, "status": "PASS" if all(r["status"] == "PASS" for r in records) else "FAIL",
          "new_dependencies": [], "local_inferences": 0, "network_policy": "DENY", "lazy_installs": False}
output = ROOT / "evidence/phase-7a3/native-inventory.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": report["status"], "records": [{"format": r["format"], "status": r["status"], "error": r.get("error", r.get("result", {}).get("error"))} for r in records], "packages": packages}, indent=2))
