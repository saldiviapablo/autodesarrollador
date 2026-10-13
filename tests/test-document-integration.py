"""Verify the native payload boundary against the authoritative contract/state."""
import hashlib
import json
import pathlib
import subprocess
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
security = yaml.safe_load((ROOT / "config/security.yaml").read_text(encoding="utf-8-sig"))
config = yaml.safe_load((ROOT / "config/system.yaml").read_text(encoding="utf-8-sig"))
state = json.loads((ROOT / "sandbox/phase7a3-documents/.autopilot/STATE.json").read_text(encoding="utf-8-sig"))
contract = yaml.safe_load((ROOT / "sandbox/phase7a3-documents/.autopilot/RUN-CONTRACT.yaml").read_text(encoding="utf-8-sig"))
records = json.loads((ROOT / "evidence/phase-7a3/T-7A-DOC-002.json").read_text(encoding="utf-8-sig"))["data"]
assert all(value["run_id"] == state["run_id"] == contract["run_id"] for value in records.values())
assert contract["authorized"] is True
for path in ["config/security.yaml", "scripts/inference-lock.ps1", "scripts/hermes-pre-tool-hook.py",
             "scripts/hermes-memory-guard.ps1", "scripts/hermes-mcp-plugin-guard.ps1"]:
    check = subprocess.run(["git", "diff", "f133bab", "--", path], cwd=ROOT, capture_output=True, timeout=10)
    assert check.returncode == 0 and not check.stdout, path
assert hashlib.sha256((ROOT / security["hooks"]["pre_tool_call"]["path"]).read_bytes()).hexdigest() == security["hooks"]["pre_tool_call"]["sha256"]
assert [config["llama"][k] for k in ["alias", "host", "port", "ctx_size", "parallel"]] == ["qwen36", "127.0.0.1", 8080, 65536, 1]
report = {"test_id": "T-7A-DOC-006", "status": "PASS", "run_id": contract["run_id"],
          "native_tool_results_bound_to_contract_and_state": True, "protected_controls_unchanged": True,
          "local_inferences": 0, "supervisor_payload_trust": "UNTRUSTED_DOCUMENT_DATA", "full_llm_end_to_end_run_tested": False}
(ROOT / "evidence/phase-7a3/T-7A-DOC-006.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report))
