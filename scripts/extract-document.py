"""Contract-bound admission and offline extraction via the frozen Hermes read_file.

The parent uses the installed native Python, controls wall time and captures JSON.
No parsing fallback or new extraction dependency is introduced here.
"""
import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import pathlib
import sys
import tempfile
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


class Denied(Exception):
    pass


def contained(path, root):
    try: path.relative_to(root); return True
    except ValueError: return False


def load_yaml(path):
    from ruamel.yaml import YAML
    return YAML(typ="safe").load(path.read_text(encoding="utf-8-sig"))


def run(input_path, project_path):
    cfg = load_yaml(ROOT / "config/system.yaml")
    policy = cfg["document_extraction"]
    if not policy["enabled"] or policy["allow_network"] or policy["allow_subprocess_from_parser"] or not policy["reject_macros"]:
        raise Denied("DOCUMENT_POLICY_INVALID")
    if str(project_path).startswith(("\\\\", "\\??\\")): raise Denied("NETWORK_PROJECT_PATH_DENIED")
    project_lexical = pathlib.Path(os.path.abspath(project_path))
    if not contained(project_lexical, ROOT): raise Denied("PROJECT_OUTSIDE_INFRASTRUCTURE_SCOPE")
    project = project_lexical.resolve(strict=True)
    if not contained(project, ROOT): raise Denied("PROJECT_OUTSIDE_INFRASTRUCTURE_SCOPE")
    contract_path = project / ".autopilot/RUN-CONTRACT.yaml"
    if not contained(contract_path.resolve(), project): raise Denied("CONTRACT_PATH_ESCAPE")
    contract = load_yaml(contract_path)
    import jsonschema
    jsonschema.validate(contract, json.loads((ROOT / "schemas/run-contract.schema.json").read_text(encoding="utf-8-sig")))
    if contract["authorized"] is not True or pathlib.Path(contract["project_root"]).resolve() != project:
        raise Denied("CONTRACT_NOT_AUTHORIZED_OR_SCOPE_MISMATCH")
    raw_path = pathlib.Path(input_path)
    if str(input_path).startswith(("\\\\", "\\??\\")): raise Denied("NETWORK_PATH_DENIED")
    lexical = pathlib.Path(os.path.abspath(project / raw_path if not raw_path.is_absolute() else raw_path))
    if not contained(lexical, project): raise Denied("DOCUMENT_PATH_ESCAPE")
    target = lexical.resolve(strict=True)
    if not contained(target, project): raise Denied("DOCUMENT_PATH_ESCAPE")
    if not target.is_file(): raise Denied("DOCUMENT_NOT_REGULAR_FILE")
    if target.suffix.lower() not in policy["allowed_formats"]: raise Denied("DOCUMENT_FORMAT_DENIED")
    if target.stat().st_size > policy["max_file_bytes"]: raise Denied("DOCUMENT_SIZE_LIMIT")
    data = target.read_bytes()
    if target.suffix.lower() in {".docx", ".xlsx"}:
        with zipfile.ZipFile(target) as z:
            entries = z.infolist()
            if sum(e.file_size for e in entries) > policy["max_expanded_zip_bytes"]:
                raise Denied("DOCUMENT_ZIP_SIZE_LIMIT")
            for entry in entries:
                name = entry.filename.lower()
                if "vbaproject" in name or name.endswith((".exe", ".dll", ".ps1", ".js")):
                    raise Denied("DOCUMENT_MACRO_OR_EXECUTABLE_DENIED")
                if name.endswith((".xml", ".rels")):
                    xml = z.read(entry).upper()
                    if b"<!DOCTYPE" in xml or b"<!ENTITY" in xml:
                        raise Denied("DOCUMENT_XML_ENTITY_DENIED")
    native_root = pathlib.Path(policy["native_source_dir"]).resolve(strict=True)
    native_file = native_root / "tools/read_extract.py"
    if hashlib.sha256(native_file.read_bytes()).hexdigest() != policy["native_read_extract_sha256"]:
        raise Denied("NATIVE_EXTRACTOR_INTEGRITY_MISMATCH")
    if hashlib.sha256((native_root / "tools/file_tools.py").read_bytes()).hexdigest() != policy["native_file_tools_sha256"]:
        raise Denied("NATIVE_FILE_TOOL_INTEGRITY_MISMATCH")
    version = load_yaml(ROOT / "config/VERSIONS.lock")["document_extraction"]["firecrawl_anydoc"]
    if importlib.metadata.version("firecrawl-anydoc") != version: raise Denied("NATIVE_PARSER_VERSION_MISMATCH")
    sec = load_yaml(ROOT / "config/security.yaml")
    hook_path = ROOT / sec["hooks"]["pre_tool_call"]["path"]
    if hashlib.sha256(hook_path.read_bytes()).hexdigest() != sec["hooks"]["pre_tool_call"]["sha256"]:
        raise Denied("HOOK_INTEGRITY_MISMATCH")
    spec = importlib.util.spec_from_file_location("approved_document_sanitizer", hook_path)
    hook = importlib.util.module_from_spec(spec); spec.loader.exec_module(hook)
    os.environ["HERMES_DISABLE_LAZY_INSTALLS"] = "1"
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    os.environ["HERMES_HOME"] = cfg["hermes"]["profile_dir"]
    sys.path.insert(0, str(native_root))
    from tools.file_tools import read_file_tool
    from tools.read_extract import extract_document_bytes
    temp_root = project / ".autopilot/temp"
    if not contained(temp_root.resolve(), project): raise Denied("TEMP_PATH_ESCAPE")
    temp_root.mkdir(parents=True, exist_ok=True)
    read_processes = []
    read_backend_active = [False]
    def offline(event, args):
        if event in {"socket.connect", "socket.getaddrinfo", "os.system"}:
            raise Denied("DOCUMENT_PARSER_NETWORK_OR_PROCESS_DENIED")
        if event == "subprocess.Popen":
            # On Windows Hermes uses its trusted file backend to fetch bytes.
            # Permit that backend only before parsing; the document converter
            # (including anydoc) can never start a process or an installer.
            if not read_backend_active[0]: raise Denied("DOCUMENT_PARSER_PROCESS_DENIED")
            executable = args[0] or (args[1][0] if isinstance(args[1], (list, tuple)) else "trusted-file-backend")
            read_processes.append(pathlib.Path(str(executable)).name)
    sys.addaudithook(offline)
    with tempfile.TemporaryDirectory(prefix=f"document-{os.getpid()}-", dir=temp_root) as work:
        tempfile.tempdir = work
        os.environ["TMP"] = os.environ["TEMP"] = work
        if target.suffix.lower() in {".docx", ".xlsx", ".pdf", ".rtf"}:
            # The official bytes API is the same converter read_file calls;
            # fetching the already-admitted bytes avoids a Windows shell read
            # while preserving all native document parsing logic.
            native = {"content": extract_document_bytes(data, str(target)), "extracted_document": True}
        else:
            read_backend_active[0] = True
            try:
                native = json.loads(read_file_tool(str(target), limit=5000, task_id="document-" + contract["run_id"]))
            finally:
                read_backend_active[0] = False
        if native.get("error") or not native.get("content") or native.get("success") is False:
            detail, _ = hook.sanitize_text(str(native.get("error") or native.get("note") or native.get("message") or native))
            raise Denied("NATIVE_EXTRACTION_FAILED: " + detail[:500])
        if "[NEEDS OCR" in native["content"] or "[EXTRACTION COVERAGE WARNING" in native["content"]:
            raise Denied("DOCUMENT_INCOMPLETE_NEEDS_OCR")
        text, redacted = hook.sanitize_text(native["content"])
        if len(text) > policy["max_output_chars"] or native.get("truncated"):
            raise Denied("DOCUMENT_OUTPUT_LIMIT")
        return {"status": "SUCCESS", "source": "hermes_native_read_file", "run_id": contract["run_id"],
                "document": str(target.relative_to(project)), "document_sha256": hashlib.sha256(data).hexdigest(),
                "trust": "UNTRUSTED_DOCUMENT_DATA", "content": "<UNTRUSTED_DOCUMENT_DATA>\n" + text + "\n</UNTRUSTED_DOCUMENT_DATA>",
                "secrets_redacted": bool(redacted), "local_inferences": 0, "new_dependencies": [], "cleanup_ok": True,
                "native_read_backend_processes": read_processes, "parser_processes_allowed": False}


def cleanup_ok(project_path):
    try:
        project = pathlib.Path(project_path).resolve()
        temp_root = project / ".autopilot/temp"
        if not contained(project, ROOT) or not contained(temp_root.resolve(), project):
            return True  # No temporary resource was admitted in this scope.
        return not list(temp_root.glob(f"document-{os.getpid()}-*"))
    except OSError:
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True); parser.add_argument("--project", required=True)
    args = parser.parse_args()
    try: result = run(args.input, args.project)
    except Denied as exc: result = {"status": "DENY", "reason": str(exc), "cleanup_ok": True}
    except Exception as exc: result = {"status": "ERROR", "reason": type(exc).__name__, "cleanup_ok": True}
    result["cleanup_ok"] = cleanup_ok(args.project)
    print(json.dumps(result, ensure_ascii=False))
