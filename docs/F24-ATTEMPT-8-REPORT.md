# F24 ATTEMPT8 — historical FAIL

Run `run-20261015-025148`, 842.3879520893097s. Native Runner: BLOCKED_REQUIRES_HUMAN_CHATGPT_ERROR_NO_RESEND. Ledger: PRE_SEND_ABORTED, send_attempts0, no DELIVERY_INTENT. This was a preparation failure, not ambiguous physical delivery.

Worker SUCCESS, immutable13 tests/build PASS before and after recovery; web context bound to native input/session; checkpoint/crash/Watchdog/START-Recover/continued Supervisor and Worker PASS. First correction exceeded native300s budget, normal restart1of2 retained. No source or clock changed after START.

ChatGPT inserted expected text in the active composer but the legacy global .ProseMirror reader selected a hidden retained editor and read empty text. Read-only inspection proves legacy reader empty while active actuator reads the entire expected prompt on root0/0. Encoding guard correctly stopped BEFORE intent/send. Reviewer, Completion Gate and logical retry NOT_RUN. The28 required gates therefore did not PASS; full evaluator inputs were not produced.

Cleanup and integrity PASS: zero own survivors/locks/listeners8080/9119, InferenceMutexFREE; preexisting Chrome preserved.48 approved pins,5673 historical files, immutable tests/original clock and6 protected components unchanged. No updates/dependencies/push. Actual metrics remain in resources-live.json and FINAL.json; RAMmin480.140625MiB, pagefilemax2.246772766GiB, VRAMmax4451MiB.

Evidence: `evidence/phase-24-attempt-8-20261015/`; byte-identical native export manifest and ledger/traces; SUMMARY, FINAL, stage-results, integrity-final, cleanup-independent and composer-mismatch-readonly. Preserve this FAIL. Isolate/certify active-composer fix before a fresh attempt.
