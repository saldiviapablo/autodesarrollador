# F24 ATTEMPT 6 — admission stopped

ATTEMPT 6 was not created or started. The single controlled ChatGPT test failed before delivery; F24 remains FAIL and READY_FOR_F25 is NO.

## Delivery stop

The new actuator passed A–L deterministic tests: composer-local scope, unrelated global buttons, physical Enter fallback selected before intent, hash/conversation/streaming/focus guards, immutable method, one action, no cross-method fallback and irreversible confirmed sends. Existing delivery, UTF-8/domain, idempotency and human-reconciliation tests passed; the automatic reconciliation function remains unchanged.

Read-only inspection of Chrome PID 16576 verified the dedicated persistent HERMES-CHATGPT profile. The historical prompt SHA was `449d9d63fff353617d1d5f0f54ce75cf61186f1e8f2251586a8455a119ce056e`. Exactly one local submit and a focused composer were present. No UI writes or sends occurred during this inspection.

Controlled test `test-send-actuator-735b2b7cc7ad4173b62227a5d45a3f46` used the normal sanitizer, budget wrapper, ledger and bridge. The bridge navigated to the root URL to request a new conversation, but that navigation retained ATTEMPT5's draft. `PREEXISTING_COMPOSER_NO_SEND` stopped execution before inserting test text, selecting an actuator or recording intent. Trace: BRIDGE_START 2026-10-15T01:19:31.204Z; FAILURE 01:19:35.957Z; CLEANUP 01:19:36.050Z. Zero DELIVERY_INTENT, mouse or Enter events; send_attempts=0. The controlled test ledger remains UNKNOWN_DELIVERY/no_resend. No retry or reconciliation was performed. No response or real actuator delivery was validated. After navigation the historical composer hash still matched; focus was lost, which would independently prohibit Enter until legitimately focused in a future authorized preparation.

The causal defect is that root navigation does not guarantee a fresh empty composer. The existing safety guard worked. No second test conversation or ATTEMPT6/7 was attempted after this failure.

## Separate harness preflight failure

Fourteen preflight groups plus actual-runtime dependency imports passed. The cleanup suite failed its disk-recovery probe: its deliberately stale `heartbeat_stale_seconds=1` remained in the recovered probe and another HEARTBEAT_STALE interrupted it; expected technical_status SUCCESS was not reached. Its immutable report/events and stderr are preserved. Syntax-lock and native-Qwen-input checks were not reached; the preflight is FAIL and unsealed. No retest, budget extension, timeout modification or relaxed assertion was used.

The newly added controlled-test PowerShell source initially lacked a UTF-8 BOM, so Windows PowerShell 5 decoded its Unicode literal incorrectly. This was not the delivery stop: no test prompt was inserted. Executed source and actual prompt bytes are preserved; a BOM was added for future correct decoding, without executing another test. Production UTF-8 source/DOM/hash checks remain mandatory.

## Preservation and cleanup

All 955 historical files, including previous ledgers, ATTEMPT5 sandbox/evidence and previous preflight, retain exact SHA-256. ATTEMPT5 ledger SHA remains `a19538782cfaf89052c6fd4123fc80a1143777d3998c66c13781dbe9baf30521`; send_attempts=0. No old state, clock, budget, ledger or sandbox was modified. F23 PASS and previous classifications remain historical. The 28-gate catalog SHA remains `690949c59fbf278f1863a35f4b27b07f3ab3b99960420c939a628625fc526953`.

Six protected hashes, including the actual model, llama-server, hook, MCP and both plugin copies, match. No installations or version updates occurred. qwen36/127.0.0.1:8080/ctx65536/parallel1 remain unchanged; no local inference was run for this admission.

Final cleanup independently verified the controlled test, completion unit fixture and eight cleanup fixtures: zero owned process survivors, no metadata locks, Run Mutex and Inference Mutex FREE, no 8080/9119 listeners. The controlled-test STATE is ABORTED, clearly labelled as a closed probe; it does not claim full Runner completion. Preexisting Chrome remains open. F24 ATTEMPT6 metrics, Worker, web, recovery, Reviewer, Completion Gate and report are NOT_RUN; prior F24 metrics were preserved. No F25/F27/F28 or push.

## Results

```text
SEND_ACTUATOR_FIX = PASS_DETERMINISTIC / LIVE_NOT_VALIDATED
LIVE_UI_PRECHECK = PASS
PRIMARY_SEND_METHOD = COMPOSER_SCOPED_SUBMIT
ENTER_FALLBACK_TEST = PASS_DETERMINISTIC
CONTROLLED_REAL_SEND = FAIL / PREEXISTING_COMPOSER_NO_SEND
F24_HARNESS_PREFLIGHT = FAIL / cleanup recovery HEARTBEAT_STALE
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
CHATGPT_SEND_METHOD = NOT_RUN
CHATGPT_SENT = NOT_RUN
CHATGPT_RESPONSE = NOT_RUN
REVIEWER = NOT_RUN
COMPLETION_GATE = NOT_RUN
RAM_MIN = NOT_RUN
PAGEFILE_MAX = NOT_RUN
VRAM_MAX = NOT_RUN
CHATGPT_PHYSICAL_ACTIONS = 0
CLEANUP = PASS
F24 = FAIL (historical ATTEMPT5 retained; ATTEMPT6 NOT_RUN)
READY_FOR_F25 = NO
```

Evidence: `evidence/f24-attempt6-preflight-20261014/FINAL.json`, `PREFLIGHT.json`, `live-ui-precheck.json`, `live-ui-after-stop.json`, `controlled-send/`, `cleanup/`, `cleanup-final.json`, `integrity-final.json` and `history-before.json`. Infrastructure commit: 8c01b07; closure commit follows in local Git. No push.
