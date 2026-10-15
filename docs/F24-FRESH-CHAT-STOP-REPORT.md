# F24 — STOP after real New Chat retained the historical draft

ATTEMPT 6 was not created or started. The explicit condition in the current request requires STOP if New Chat does not produce an empty composer. That happened. No ATTEMPT7, F25 or push.

## What changed and was verified

The bridge requests the actual UI New Chat action for `--new-conversation`; it no longer treats navigation to `/` as proof of freshness. A unique visible editable composer, strict domain, root/new conversation identity, 0/0 turns, no streaming and an empty composer are checked before reserving the consultation ledger. The existing scoped submit/Enter selection, intent-before-one-action and exact turn/hash send proof remain unchanged. It never clears a retained draft.

Deterministic fresh-chat, send actuator A–L, delivery and single-click tests passed before the live check. PowerShell 5 parsed the controlled-send source using its existing UTF-8 BOM and produced the exact expected UTF-8 prompt bytes. No encoding change was needed.

The first preparation failed before navigation because an offscreen `aria-label=Nuevo chat` control masked the visible text-labelled navigation control. Read-only geometry/hit-testing demonstrated this defect. Before START, the selector was fixed to filter by hit-test before choosing a semantic candidate; its regression case passed. This failed preparation and the original identity were preserved. The same test ID was used for the repaired preparation, with no ledger yet reserved and normal budget accounting retained (no credits/reset).

## Live STOP

Test ID: `test-send-actuator-153deadd913e4bdfbbc081196d7f1c63`.

One mouse press/release pair was dispatched to the unique visible hit-tested New Chat navigation control. Post-action inspection still found the historical prompt, 0 user turns, 0 assistant turns, no streaming and URL `https://chatgpt.com/`. Its composer SHA remained `449d9d63fff353617d1d5f0f54ce75cf61186f1e8f2251586a8455a119ce056e`.

The bridge returned `FRESH_CHAT_NOT_EMPTY_OR_NOT_READY_NO_CLEAR`. The trace proves one New Chat navigation action, zero send-action events, zero DELIVERY_INTENT, zero SENT_CONFIRMED and no reserved test ledger. No test prompt was inserted, no draft was cleared or overwritten, no send method was selected and no response was requested. No further UI action or retry occurred after this refusal. Transport acknowledgement of navigation does not prove that ChatGPT created a new conversation.

ATTEMPT5's ledger is unchanged, including send_attempts=0 and UNKNOWN_DELIVERY/no_resend. Its SHA remains `a19538782cfaf89052c6fd4123fc80a1143777d3998c66c13781dbe9baf30521`. No reconciliation occurred.

## Heartbeat fixture correction: implemented, not certified

The proposed probe correction preserves the normal plan bytes before the artificial one-second injection and leaves the fault fixture terminal. A separate recovery fixture must have exactly those normal bytes/hash and retain its normal approval digest across recovery. No production heartbeat policy, Watchdog logic, timeout or budget was changed. This probe was not executed after the explicit fresh-chat STOP, so HEARTBEAT_RECOVERY_FIX is NOT_VERIFIED and the full preflight is NOT_RUN/unsealed. No live recovery success is claimed. The 28-gate catalog remains unchanged; there is no gate29.

## Cleanup and preservation

4,146 historical files retain exact SHA-256, including earlier admission failures and old sandbox/ledger evidence. All six protected component hashes were recomputed with streaming reads and match, including the actual GGUF model, llama-server, hook, MCP and both plugin copies. The 28-gate catalog SHA remains `690949c59fbf278f1863a35f4b27b07f3ab3b99960420c939a628625fc526953`.

Final cleanup verifies no own process survivors, no new metadata locks, Run Mutex FREE, Inference Mutex FREE and no listeners on 8080/9119. The dedicated preexisting Chrome remains open. The controlled test's STATE is ABORTED; its logical query reservations were preserved. No local inference, installations or updates were performed; qwen36/127.0.0.1:8080/ctx65536/parallel1 remain unchanged. All F24 E2E stages and metrics for ATTEMPT6 are NOT_RUN; prior measurements remain untouched.

## Requested results

```text
FRESH_CHAT_LOGIC = PASS_DETERMINISTIC / LIVE_FRESHNESS_FAIL
CONTROLLED_REAL_SEND = FAIL / FRESH_CHAT_NOT_EMPTY_OR_NOT_READY_NO_CLEAR
HEARTBEAT_RECOVERY_FIX = IMPLEMENTED / NOT_VERIFIED_AFTER_STOP
F24_HARNESS_PREFLIGHT = NOT_RUN / FRESH_CHAT_STOP
ATTEMPT_6_RUN_ID = NOT_CREATED
DURATION = NOT_RUN
WORKER = NOT_RUN
WEB_FETCH = NOT_RUN
WEB_CONTEXT_DELIVERED = NOT_RUN
TESTS = NOT_RUN
BUILD = NOT_RUN
RECOVERY_DETECTION = NOT_RUN
START_RECOVER = NOT_RUN
CONTINUATION = NOT_RUN
FRESH_CHAT_READY = FAIL
CHATGPT_SEND_METHOD = NOT_SELECTED
CHATGPT_PHYSICAL_ACTIONS = 0
CHATGPT_SENT = NOT_RUN
CHATGPT_RESPONSE = NOT_RUN
REVIEWER = NOT_RUN
COMPLETION_GATE = NOT_RUN
RAM_MIN = NOT_RUN
PAGEFILE_MAX = NOT_RUN
VRAM_MAX = NOT_RUN
CLEANUP = PASS
F24 = FAIL / historical ATTEMPT5 preserved; ATTEMPT6 NOT_RUN
READY_FOR_F25 = NO
```

Evidence: `evidence/f24-admission-repair-20261014/`: FINAL.json, controlled-send/ (including failed preparation, native state and both traces), live-before.json, live-after-new-chat.json, new-chat-controls.json, controlled-source-utf8.json, deterministic-checks.json, cleanup-final.json, integrity-final.json and history-before.json. Backups: `backups/f24-admission-repair-20261014/manifest.json`. Infrastructure commit: 7281c4e. A separate local closure commit records this report and evidence. No push.
