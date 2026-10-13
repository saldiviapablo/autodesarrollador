"""Real native browser probe in a fresh, bounded headless profile."""
import json
import os
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
sys.path.insert(0, sys.argv[1])
scratch = ROOT / "sandbox/phase7a4-browser"
for key in list(os.environ):
    if key.startswith(("AGENT_BROWSER_", "BU_CDP_")):
        os.environ.pop(key, None)
profile = scratch / "hermes-profile"
profile.mkdir(parents=True, exist_ok=True)
(profile / "config.yaml").write_text('browser:\n  backend: "off"\n  cloud_provider: local\n  engine: chrome\n  headed: false\n  use_real_profile: false\n  allow_private_urls: false\nsecurity:\n  allow_lazy_installs: false\n', encoding="utf-8")
os.environ["HERMES_HOME"] = str(profile)
os.environ["HERMES_DISABLE_LAZY_INSTALLS"] = "1"
os.environ["AGENT_BROWSER_ALLOWED_DOMAINS"] = "docs.python.org"
os.environ["AGENT_BROWSER_CONTENT_BOUNDARIES"] = "1"
os.environ["AGENT_BROWSER_MAX_OUTPUT"] = "50000"
os.environ["AGENT_BROWSER_HEADED"] = "false"
os.environ["AGENT_BROWSER_PROFILE"] = str(scratch / "browser-profile")
os.environ["AGENT_BROWSER_EXECUTABLE_PATH"] = str(pathlib.Path(sys.argv[1]).parent / "tools/chromium-1208/chrome-win64/chrome.exe")
policy = scratch / "action-policy.json"
policy.write_text(json.dumps({"default": "deny", "allow": ["launch", "navigate", "snapshot", "get", "close"]}), encoding="utf-8")
os.environ["AGENT_BROWSER_ACTION_POLICY"] = str(policy)
for key in ["BROWSERBASE_API_KEY", "BROWSERBASE_PROJECT_ID", "BROWSER_USE_API_KEY", "FIRECRAWL_API_KEY", "CAMOFOX_URL", "BROWSER_CDP_URL", "AGENT_BROWSER_CDP", "HERMES_PROFILE"]:
    os.environ.pop(key, None)
temp = scratch / "temp"
temp.mkdir(parents=True, exist_ok=True)
tempfile.tempdir = str(temp)
for key in ["TMP", "TEMP", "TMPDIR"]: os.environ[key] = str(temp)
from tools import browser_tool as browser
from tools.browser_tool_lifecycle import cleanup_browser
from tools.browser_tool_install import check_browser_requirements

task = "phase7a4-native-probe"
result = {"local_inferences": 0}
try:
    result["native_requirements_ready"] = check_browser_requirements()
    nav = json.loads(browser.browser_navigate("https://docs.python.org/3/library/json.html", task_id=task))
    result["navigation"] = {k: v for k, v in nav.items() if k != "snapshot"}
    if nav.get("success"):
        snapshot = json.loads(browser.browser_snapshot(full=True, task_id=task))
        text = snapshot.get("snapshot", "")
        result["snapshot"] = {"success": snapshot.get("success"), "has_json_documentation": "JSON" in text, "excerpt": text[:1000]}
        denied = json.loads(browser.browser_navigate("https://example.com/", task_id=task))
        result["non_allowlisted_native_navigation"] = denied
        eval_denied = json.loads(browser.browser_console(expression="document.title", task_id=task))
        result["evaluation_policy_denied"] = eval_denied
        result["status"] = "PASS" if result["native_requirements_ready"] and snapshot.get("success") and "JSON" in text and not denied.get("success") and not eval_denied.get("success") else "FAIL"
    else: result["status"] = "FAIL"
except Exception as exc:
    result["status"] = "FAIL"; result["error"] = type(exc).__name__ + ": " + str(exc)
finally:
    cleanup_browser(task)
    result["native_sessions_remaining"] = len(browser._active_sessions)
    out = ROOT / "evidence/phase-7a4/native-probe.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
