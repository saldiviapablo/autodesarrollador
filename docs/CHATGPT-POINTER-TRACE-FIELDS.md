# Pointer trace field preservation

Before A11 START, inspection found that Trace.emit filtered out the four primitive fields used by the new strict pointer-probe rollback validation. Fake trace callbacks in earlier selection tests had not exercised the serializer. This could conservatively block pre-send cleanup after a later failure; no unsafe resend was enabled.

Only the trace allowlist changes: non_send_probe,send_attempts,physical_actions,available. Delivery states, budgets, post-intent rules and reconciliation remain byte-identical outside that single list. Unknown fields remain omitted.13 deterministic pointer cases now exercise the actual fsynced Trace writer, preserve its raw fixture and validate it through the productive rollback predicate;10 related suites PASS. No browser, ledger production mutation, local inference or send.

Evidence: evidence/chatgpt-pointer-trace-fields-20261015/CERTIFIED.json and pointer-persisted.trace.jsonl. A11 original admission is preserved and must be resealed before approval/START. No prior attempt is resumed or relabeled PASS.
