"""Preflight documentation, frozen versions, historical evidence and secrets audit."""
import hashlib
import json
import pathlib
import re
import subprocess
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]


def command(*args):
    proc = subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=15)
    assert proc.returncode == 0, (args, proc.stderr)
    return (proc.stdout + proc.stderr).strip()


def original(path):
    proc = subprocess.run(["git", "show", "8502d79:" + path], cwd=ROOT,
                          capture_output=True, timeout=10)
    assert proc.returncode == 0, path
    return proc.stdout


def unchanged_text(path):
    # Git stores LF; this Windows checkout may use CRLF. Compare actual text.
    return (ROOT / path).read_text(encoding="utf-8-sig") == original(path).decode("utf-8-sig").replace("\r\n", "\n")


def main():
    checks = {}
    paths = ["00-README.md", "07-ROADMAP.md", "08-CAPACIDADES-NATIVAS-HERMES.md",
             "MANIFEST.md", "docs/IMPLEMENTATION-STATUS.md", "config/INSTALLATION-STATE.json"]
    texts = {p: (ROOT / p).read_text(encoding="utf-8-sig") for p in paths}
    for p in paths[:2]:
        assert "IN_PROGRESS" in texts[p]
        assert not re.search(r"Macrofase 7A[^\n]*\bPENDING\b(?!.*IN_PROGRESS)", texts[p])
        assert re.search(r"7A\.1[^\n]*PASS", texts[p])
        assert re.search(r"7A\.2[^\n]*PASS", texts[p]) or "7A.1–7A.2 PASS" in texts[p]
    for p in ["MANIFEST.md", "docs/IMPLEMENTATION-STATUS.md"]:
        assert "IN_PROGRESS" in texts[p] and "7A.1" in texts[p] and "7A.2" in texts[p]
    assert "T-7A-MEM-001/002" in texts[paths[2]]
    assert "IMPLEMENTADO Y VERIFICADO (7A.2 PASS" in texts[paths[2]]
    assert "**NO**" in next(line for line in texts[paths[2]].splitlines() if "**13. Extracción Documentos**" in line)
    state = json.loads(texts[paths[-1]])
    assert all(state["macrophases"][str(i)] == "PASS" for i in range(1, 7))
    assert state["macrophases"]["7A"] == "IN_PROGRESS"
    assert state["macrophases"]["7B"] == state["macrophases"]["8"] == "PENDING"
    assert all(state["subphases_7a"][f"7A.{i}"] == ("PASS" if i <= 2 else "PENDING") for i in range(1, 11))
    checks["canonical_state_coherence"] = "PASS"

    lock = yaml.safe_load((ROOT / "config/VERSIONS.lock").read_text(encoding="utf-8-sig"))
    assert unchanged_text("config/VERSIONS.lock")
    versions = {
        "python": command(lock["runtimes"]["python_main"]["executable"], "--version"),
        "llama": command(lock["inference"]["llama_cpp"]["executable"], "--version"),
        "node": command(lock["runtimes"]["node"]["executable"], "--version"),
        "qwen": command("C:/Program Files/nodejs/node.exe", lock["autonomous_agents"]["qwen_code"]["cli_entry"], "--version"),
        "hermes_commit": command("git", "-C", "C:/Users/Pc/AppData/Local/hermes/hermes-agent", "rev-parse", "HEAD"),
        "hermes_tag": command("git", "-C", "C:/Users/Pc/AppData/Local/hermes/hermes-agent", "describe", "--tags", "--exact-match", "HEAD"),
    }
    assert lock["runtimes"]["python_main"]["version"] in versions["python"]
    assert str(lock["inference"]["llama_cpp"]["build"]) in versions["llama"]
    assert lock["inference"]["llama_cpp"]["commit"] in versions["llama"]
    assert versions["node"] == "v" + lock["runtimes"]["node"]["version"]
    assert versions["qwen"] == lock["autonomous_agents"]["qwen_code"]["version"]
    assert versions["hermes_commit"] == lock["autonomous_agents"]["hermes"]["commit"]
    assert versions["hermes_tag"] == "v" + lock["autonomous_agents"]["hermes"]["version"]
    checks["installed_versions_match_unchanged_lock"] = "PASS"
    phase5 = "evidence/installation/qwen-code-phase05-summary.md"
    current = (ROOT / phase5).read_text(encoding="utf-8-sig")
    current = "\n".join(line for line in current.splitlines() if not line.startswith("> HISTORICAL SNAPSHOT") and not line.startswith("> Aclaración de preflight"))
    # Only the historical annotation and its blank separator may differ.
    assert [l for l in current.splitlines() if l] == [l for l in original(phase5).decode("utf-8-sig").splitlines() if l]
    checks["historical_phase5_content_preserved"] = "PASS"
    for phase in ("phase-7a1", "phase-7a2"):
        for f in (ROOT / "evidence" / phase).iterdir():
            if f.is_file():
                p = f.relative_to(ROOT).as_posix()
                assert unchanged_text(p), p
    checks["historical_7a1_7a2_evidence_unchanged"] = "PASS"
    for p in ["config/security.yaml", "scripts/hermes-pre-tool-hook.py", "scripts/inference-lock.ps1",
              "scripts/mcp-sandbox-server.py", "config/plugins/desarrollador-autonomo-health/__init__.py",
              "config/plugins/desarrollador-autonomo-health/plugin.yaml"]:
        assert unchanged_text(p), p
    security = yaml.safe_load((ROOT / "config/security.yaml").read_text(encoding="utf-8-sig"))
    hook = security["hooks"]["pre_tool_call"]
    mcp = security["mcp"]["servers"]["da_local_sandbox"]
    plugin = security["plugins"]["approved_plugins"]["desarrollador-autonomo-health"]
    for p, approved in [(hook["path"], hook["sha256"]), (mcp["script_path"], mcp["sha256"]),
                        (plugin["repo_dir"] + "/" + plugin["entrypoint"], plugin["sha256"]),
                        (plugin["repo_dir"] + "/plugin.yaml", plugin["manifest_sha256"])]:
        assert hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == approved, p
    checks["protected_components_unchanged"] = "PASS"
    inspection = ROOT / "evidence/inspection-7a-20261013-011310"
    for f in inspection.iterdir():
        content = f.read_text(encoding="utf-8-sig")
        assert not re.search(r"sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{20,}|-----BEGIN .*PRIVATE KEY-----", content), f
    checks["inspection_evidence_secret_scan"] = "PASS"
    config = yaml.safe_load((ROOT / "config/system.yaml").read_text(encoding="utf-8-sig"))
    assert config["chatgpt"]["allowed_domains"] == ["chatgpt.com"]
    assert [config["llama"][k] for k in ["alias", "host", "port", "ctx_size", "parallel"]] == ["qwen36", "127.0.0.1", 8080, 65536, 1]
    checks["runtime_config_preserved_and_domain_exact"] = "PASS"
    print(json.dumps({"status": "PASS", "checks": checks, "versions": versions,
                      "versions_lock_sha256": hashlib.sha256((ROOT / "config/VERSIONS.lock").read_bytes()).hexdigest()},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
