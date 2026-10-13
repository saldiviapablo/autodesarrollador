"""Native Hermes navigation/snapshot under a contract and static read-only policy."""
import argparse
import hashlib
import importlib.util
import json
import os
import pathlib
import sys
import tempfile
import uuid
import time
from urllib.parse import urlsplit

ROOT = pathlib.Path(__file__).resolve().parents[1]
site_packages = os.environ.get("DA_BROWSER_NATIVE_SITE_PACKAGES", "")
if site_packages:
    sys.path.insert(0, site_packages)
sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")

# The parent must assign the kernel job before the worker may spawn a browser.
ready_file = os.environ.get("DA_BROWSER_JOB_READY_FILE", "")
if ready_file:
    ready = pathlib.Path(ready_file)
    if not ready.resolve().is_relative_to(ROOT / "runtime/browser-jobs"):
        raise RuntimeError("BROWSER_JOB_SCOPE_MISMATCH")
    deadline = time.monotonic() + 5
    while not ready.exists() and time.monotonic() < deadline: time.sleep(0.01)
    if not ready.exists() or ready.read_text().strip() != str(os.getpid()):
        raise RuntimeError("BROWSER_JOB_NOT_ASSIGNED")
else:
    raise RuntimeError("BROWSER_JOB_REQUIRED")


def yaml_load(path):
    from ruamel.yaml import YAML
    return YAML(typ="safe").load(path.read_text(encoding="utf-8-sig"))


def allowed_url(url, domains):
    try:
        parsed = urlsplit(url)
        return parsed.scheme == "https" and parsed.hostname in domains and not parsed.username and not parsed.password
    except ValueError:
        return False


def run(url, project_path):
    config = yaml_load(ROOT / "config/system.yaml")
    policy = config["native_browser"]
    if not policy["enabled"] or policy["headed"] or policy["use_real_profile"] or policy["cloud_provider"] != "local":
        return {"status": "DENY", "reason": "NATIVE_BROWSER_POLICY_INVALID"}
    if not allowed_url(url, policy["allowed_domains"]): return {"status": "DENY", "reason": "DOMAIN_BLOCKED"}
    if str(project_path).startswith("\\\\"): return {"status": "DENY", "reason": "PROJECT_SCOPE_DENIED"}
    project = pathlib.Path(os.path.abspath(project_path))
    if not project.is_relative_to(ROOT): return {"status": "DENY", "reason": "PROJECT_SCOPE_DENIED"}
    project = project.resolve(strict=True)
    if not project.is_relative_to(ROOT): return {"status": "DENY", "reason": "PROJECT_SCOPE_DENIED"}
    contract_path = project / ".autopilot/RUN-CONTRACT.yaml"
    if not contract_path.resolve().is_relative_to(project): return {"status": "DENY", "reason": "CONTRACT_PATH_ESCAPE"}
    contract = yaml_load(contract_path)
    import jsonschema
    jsonschema.validate(contract, json.loads((ROOT / "schemas/run-contract.schema.json").read_text(encoding="utf-8-sig")))
    if contract["authorized"] is not True or pathlib.Path(contract["project_root"]).resolve() != project:
        return {"status": "DENY", "reason": "CONTRACT_SCOPE_DENIED"}
    native = pathlib.Path(policy["native_source_dir"])
    if hashlib.sha256((native / "tools/browser_tool.py").read_bytes()).hexdigest() != policy["native_module_sha256"]:
        return {"status": "DENY", "reason": "NATIVE_BROWSER_INTEGRITY_MISMATCH"}
    action_file = ROOT / policy["action_policy_path"]
    action = json.loads(action_file.read_text(encoding="utf-8-sig"))
    if action != {"default": "deny", "allow": ["launch", "navigate", "snapshot", "get", "close"]}:
        return {"status": "DENY", "reason": "NATIVE_BROWSER_ACTION_POLICY_MISMATCH"}
    for key in list(os.environ):
        if key.startswith(("AGENT_BROWSER_", "BU_CDP_")) or key in {"CAMOFOX_URL", "BROWSER_CDP_URL", "HERMES_PROFILE", "BROWSERBASE_API_KEY", "BROWSERBASE_PROJECT_ID", "BROWSER_USE_API_KEY", "FIRECRAWL_API_KEY"}:
            os.environ.pop(key, None)
    work_root = project / ".autopilot/native-browser"
    if not work_root.resolve().is_relative_to(project): return {"status": "DENY", "reason": "BROWSER_TEMP_ESCAPE"}
    work_root.mkdir(parents=True, exist_ok=True)
    task = "governed-browser-" + uuid.uuid4().hex
    browser = None
    result = {}
    with tempfile.TemporaryDirectory(prefix="browser-" + str(os.getpid()) + "-", dir=work_root) as work:
        profile = pathlib.Path(work) / "hermes-profile"; profile.mkdir()
        (profile / "config.yaml").write_text('browser:\n  backend: "off"\n  cloud_provider: local\n  engine: chrome\n  headed: false\n  use_real_profile: false\n  allow_private_urls: false\nsecurity:\n  allow_lazy_installs: false\n', encoding="utf-8")
        os.environ.update(HERMES_HOME=str(profile), HERMES_DISABLE_LAZY_INSTALLS="1", TMP=work, TEMP=work, TMPDIR=work,
                          AGENT_BROWSER_ALLOWED_DOMAINS=",".join(policy["allowed_domains"]), AGENT_BROWSER_CONTENT_BOUNDARIES="1",
                          AGENT_BROWSER_MAX_OUTPUT=str(policy["max_output_chars"]), AGENT_BROWSER_HEADED="false",
                          AGENT_BROWSER_EXECUTABLE_PATH=policy["chromium_executable"], AGENT_BROWSER_ACTION_POLICY=str(action_file))
        tempfile.tempdir = work
        sys.path.insert(0, str(native))
        from tools import browser_tool as browser
        from tools.browser_tool_lifecycle import cleanup_browser
        try:
            nav = json.loads(browser.browser_navigate(url, task_id=task))
            if not nav.get("success"):
                result = {"status": "ERROR", "reason": nav.get("error", "NAVIGATION_FAILED")}
            elif not allowed_url(nav["url"], policy["allowed_domains"]):
                result = {"status": "DENY", "reason": "REDIRECT_DOMAIN_BLOCKED"}
            else:
                snap = json.loads(browser.browser_snapshot(full=True, task_id=task))
                if not snap.get("success"):
                    result = {"status": "ERROR", "reason": "SNAPSHOT_FAILED"}
                else:
                    result = {"status": "SUCCESS", "source": "hermes_native_browser", "run_id": contract["run_id"],
                              "url": nav["url"], "title": nav.get("title"), "trust": "UNTRUSTED_EXTERNAL_DATA",
                              "content": "<UNTRUSTED_EXTERNAL_DATA>\n" + snap.get("snapshot", "")[:policy["max_output_chars"]] + "\n</UNTRUSTED_EXTERNAL_DATA>",
                              "local_inferences": 0, "cloud_provider": "local", "used_real_profile": False}
        finally:
            cleanup_browser(task)
            result["native_sessions_remaining"] = len(browser._active_sessions)
    result["cleanup_ok"] = not list(work_root.glob("browser-" + str(os.getpid()) + "-*"))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--url", required=True); parser.add_argument("--project", required=True)
    args = parser.parse_args()
    try: report = run(args.url, args.project)
    except Exception as exc: report = {"status": "ERROR", "reason": type(exc).__name__}
    print(json.dumps(report, ensure_ascii=False))
