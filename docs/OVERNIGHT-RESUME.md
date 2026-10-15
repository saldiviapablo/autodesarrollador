# Reanudación nocturna — fuente de continuidad

schema_version: 1.0
kind: MAINTENANCE_ORCHESTRATION_NOT_RUN_STATE
authorization: 2026-10-15 overnight user attachment 6bd9a034-9a1e-4e7e-b13b-7d840198a9f4
last_completed: F23 PASS; F24 ATTEMPT7 historical FAIL
active_phase: F24_ATTEMPT8_PREPARATION
last_cause: Reviewer instruction/data boundary; native transport and role verified correct
last_fix: Readonly evidence envelope, SHA input binding and strict single decision parser; isolated native Reviewer ACCEPTED
last_commit: 1796a93de2812606422dbef2f11b9c6da09574be
next_action: Create/commit fresh ATTEMPT8 harness and minimal admission; start new E2E with strengthened immutable 13-test fixture
run_pointer: None
updated_at: 2026-10-15T05:48:04.037230+00:00
no_push: True
new_failures: ['REVIEWER_INSTRUCTION_DATA_BOUNDARY', 'NONFINITE_NUMERIC_ACCEPTANCE_COVERAGE']
fixes: ['REVIEWER_CONTRACT_CERTIFIED', 'NONFINITE_ORACLE_EXPANDED_BEFORE_NEW_START']

Plan autorizado: F24 nuevo (28 gates) → F25 real2h → 4h (06 §33) → F26 → F27 piloto dedicado → F28 real6–8h → regresión/auditoría/cleanup final. Sin push ni inferencias simultáneas. La certificación aislada no cambia el FAIL histórico de ATTEMPT7.

Fuentes: runtime/overnight/STATE.json; evidence/overnight-reviewer-20261015/CERTIFIED.json; docs/REVIEWER-CONTRACT-FIX.md. Configuración qwen36/127.0.0.1:8080/ctx65536/parallel1. No reiniciar ningún run vencido ni reconciliar consultas históricas.
