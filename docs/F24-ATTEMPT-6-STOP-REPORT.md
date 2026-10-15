# F24 ATTEMPT 6 — terminal STOP report

Date: 2026-10-15 (America/Buenos_Aires). F24 = FAIL. READY_FOR_F25 = NO. No ATTEMPT7, F25, F27/F28 or push.

## Resumed work and pre-START certification

The interrupted working tree was preserved, audited and completed. Transactional schema2 PREPARED/pre-send interruption/abort handling, owned-draft receipt validation, guarded rollback, conservative post-intent no_resend and strict Unicode guard passed deterministic suites. Empty/invalid/ambiguous ownership and forged cleanup receipts deny retry/clearing. Existing human reconciliation tests and the automatic reconciliation function remain compatible. Legacy schema1 records were not migrated.

ATTEMPT5's actual draft was recovered under LEGACY_PRE_SEND_RECOVERY before this E2E, with strict ownership/profile/domain/baseline/trace checks and three stable empty observations. Its ledger SHA remains `a19538782cfaf89052c6fd4123fc80a1143777d3998c66c13781dbe9baf30521`, send_attempts=0, historical UNKNOWN_DELIVERY. Current readouts label it legacy; no stored state was rewritten or recertified.

The controlled consultation `test-send-actuator-149e5c863a284648b50ad3cea075bf7c` passed from empty root/0/0: PREPARED before intent, one scoped submit, user+1, SENT_CONFIRMED before response wait, assistant+1, composer empty, UTF-8 response captured, COMPLETED and ALREADY_SENT retry with zero additional actions. Its budget remained 1/5. It did not certify the DOM extraction of retained hidden turns after leaving an existing conversation; that live defect was exposed by ATTEMPT6.

The isolated heartbeat fixture passed: one-second threshold only in the terminal fault fixture, normal recovery bytes/SHA equal the pre-fault snapshot (`81e792a5ea55716e5ade1f0201e7d02288b60da0d732bd7c8a57e959f8f8708a`), unchanged approval digest, actual START-Recover and technical SUCCESS. Production Watchdog and threshold were unchanged. Full harness preflight, runtime imports, native Qwen input binding, cleanup, UTF-8 and evaluator of the unchanged 28-gate catalog passed and were sealed. This was pre-START certification, not native E2E completion. Git was clean before creating ATTEMPT6.

## Actual new E2E

Run: `run-20261015-005747`; sandbox `sandbox/f24-attempt6-2bfe3e3f/project`. New contract/plan, one approval and new persistent clock; normal limits remained global2700/phase300/restart2/maxcycles5. Qwen alone edited invoice.py and README.md. Launcher, Prepare, admission, llama health, independent Supervisor, actual diagnostic FAIL, official WEB_FETCH, actual session/input-bound WEB_CONTEXT_DELIVERED, Worker correction, 13 immutable tests and approved build passed.

At harness elapsed492.00s, the sole owned Runner parent was deliberately crashed after checkpoint/tests/build. Watchdog confirmed PARENT_PROCESS_LOST at495.10s, and actual START-Recover began at495.12s. A second Supervisor and Worker succeeded, research was delivered again, and all tests/build passed again. The original clock bytes and all approval pins remained unchanged. No local inference overlap or manual target-code correction was introduced. Agent restart counters all remained zero; the single deliberate parent crash was not counted as agent restart credit.

## Failing gate and evidence

F24 consultation ID: `f24-a6-bb8c3e08d0684b80912466bce9011b1f`. Trace:

* 04:09:23.117Z BRIDGE_START.
* 04:09:24.171Z REQUEST_FRESH_CHAT, composer already empty.
* 04:09:24.187Z NEW_CHAT_NAVIGATION_START.
* 04:09:24.867Z NEW_CHAT_NAVIGATION_END.
* 04:09:28.053Z FAILURE FRESH_CHAT_NOT_EMPTY_OR_NOT_READY_NO_CLEAR.

The UI reached `https://chatgpt.com/` with an empty composer, no streaming, but `readConversation()` counted1 user and1 assistant node. Read-only inspection after cleanup proves both old nodes had zero width/height and no client rectangles (`rendered=false`). The extractor counts document-wide role nodes without distinguishing retained nonrendered messages from the current conversation. Those false1/1 counts rejected the required fresh0/0 baseline.

This is a remaining DOM-counting defect, not an ambiguous send. No F24 ledger was reserved, no prompt inserted, no PREPARED or DELIVERY_INTENT, no send method selected and zero mouse-send/Enter actions. Only one New Chat navigation occurred. No logical retry, reconciliation or further physical action followed. The native generic BLOCKED_REQUIRES_HUMAN/no_resend classification was preserved. No bridge/source fix was attempted after START, as required. Reviewer and Completion Gate were not reached; all28 native gates therefore did not pass.

## Metrics, cleanup and integrity

Native finalized duration699.24654s (11m39.25s); total harness708.91890s including setup6.59891s and final observation/cleanup. No phase/global budget extension. RAM minimum6.2265625MiB, pagefile maximum2.30023575GiB, VRAM maximum4507MiB, llama maximum working set20950.582MiB,138 resource samples. The maximum streak below150MiB was one sample; the existing sustained-critical guard did not trigger. The low RAM sample remains in the original metrics and was not replaced.

Native and independent cleanup PASS: zero owned survivors, metadata lock removed, Run/Inference mutex FREE,8080/9119 without listeners. Preexisting Chrome HERMES-CHATGPT remains open. STATE is terminal BLOCKED_REQUIRES_HUMAN and evidence is preserved.

All46 approval hashes,4185 historical files, immutable acceptance/build files, the original clock and six protected hashes (including freshly streamed actual GGUF, llama-server, hook, MCP and both plugins) match. No frozen source changed after START. qwen36/127.0.0.1:8080/ctx65536/parallel1 and Hermes0.21.6 remain unchanged; no dependencies, updates or push. Historical failures and all prior measurements remain intact.

## Requested results

```text
PARTIAL_WORK_RESUMED = YES
ROOT_CAUSE_FIXED = PRE_SEND PASS / FRESH_CHAT_DOM_COUNTER FAIL
PRE_SEND_STATE_MACHINE = PASS
FALSE_UNKNOWN_DELIVERY_FIXED = PASS
OWNED_DRAFT_ROLLBACK = PASS
LEGACY_ATTEMPT5_DRAFT_RECOVERY = PASS
HISTORICAL_LEDGER_UNCHANGED = YES
FRESH_CHAT_FIX = FAIL / hidden old turns counted after navigation
UNICODE_GUARD = PASS
HEARTBEAT_RECOVERY_FIX = PASS
DETERMINISTIC_TESTS = PASS
CONTROLLED_REAL_SEND = PASS
F24_HARNESS_PREFLIGHT = PASS (pre-START certification; native E2E failed)
ATTEMPT_6_RUN_ID = run-20261015-005747
DURATION = 699.2465400695801
WORKER = SUCCESS
WEB_FETCH = PASS
WEB_CONTEXT_DELIVERED = PASS
TESTS = PASS / 13 immutable tests in both segments
BUILD = PASS
RECOVERY_DETECTION = PASS
START_RECOVER = PASS
CONTINUATION = PASS
CHATGPT_SEND_METHOD = NOT_SELECTED
CHATGPT_PHYSICAL_ACTIONS = 0
CHATGPT_SENT = FAIL / FRESH_CHAT_NOT_EMPTY_OR_NOT_READY_NO_CLEAR
CHATGPT_RESPONSE = NOT_RUN
REVIEWER = NOT_RUN
COMPLETION_GATE = NOT_EVALUATED
RAM_MIN_MiB = 6.2265625
PAGEFILE_MAX_GiB = 2.3002357482910156
VRAM_MAX_MiB = 4507
CLEANUP = PASS
INTEGRITY = PASS
F24 = FAIL / BLOCKED_REQUIRES_HUMAN
READY_FOR_F25 = NO
```

The working tree is committed clean at closure (verify with local Git). Commits for implementation/certification: `ca74d12`, `5b4834d`; heartbeat fixture source was already implemented in `7281c4e`. A separate terminal-evidence commit follows. The native final evaluator was not run after the block; `FROZEN-GATE-STATUS-PARTIAL.json` explicitly records incomplete/failed gates instead of claiming28/28 PASS.

Evidence: `evidence/f24-transaction-cert-20261014/` for certification and `evidence/phase-24-attempt-6-20261014/` for the actual run, byte-identical native exports, Worker diff, resource samples, checkpoint/crash/recovery, failed bridge traces, read-only DOM visibility, cleanup and integrity. `capture-manifest.json` maps exported files to original hashes.
