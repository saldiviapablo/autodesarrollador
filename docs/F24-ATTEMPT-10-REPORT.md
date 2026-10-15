# F24 ATTEMPT10 — historical FAIL

F24 ATTEMPT10 **FAIL**, run `run-20261015-035008`, 1128.75s. Worker/tests13/build/web/recovery y continuación PASS. Ledger COMPLETED,1 envío físico, respuesta recuperada read-only con SHA exacto; retry lógico posterior ALREADY_SENT/+0. Fallo final del clasificador: CodeMirror de la respuesta confundido con composer. Reviewer/Completion NOT_RUN;28 gates no aprobados. Cleanup/integridad PASS; F25 pendiente.

```json
{
  "F24": "FAIL",
  "attempt": 10,
  "run_id": "run-20261015-035008",
  "duration_seconds": 1128.7521667480469,
  "native_status": "BLOCKED_REQUIRES_HUMAN_CHATGPT_SENT_CONFIRMED_NO_RESEND",
  "root_cause": "assistant CodeMirror contenteditable was counted as a second composer",
  "ledger": "COMPLETED",
  "physical_sends": 1,
  "response_recovered_readonly_hash_match": true,
  "logical_retry_after_stop": "ALREADY_SENT",
  "additional_sends": 0,
  "reviewer": "NOT_RUN",
  "completion_gate": "NOT_RUN",
  "full28_gate": "FAIL / INPUTS_INCOMPLETE",
  "cleanup": "PASS",
  "integrity": "PASS",
  "source_files": 244,
  "restarts": {
    "llama": 0,
    "supervisor": 0,
    "reviewer": 0,
    "worker": 2
  },
  "RAM_MIN_MIB": 583.8828125,
  "PAGEFILE_MAX_GIB": 2.778167724609375,
  "VRAM_MAX_MIB": 4415,
  "F25_started": false,
  "no_push": true
}
```

Nuevo run/sandbox/plan/contrato/aprobación/ID/reloj normal2700s; fase300/restart2/maxcycles5 intactos. Qwen fue el único editor de invoice.py/README;13 tests/build inmutables desde antes de START. Dos Worker native wall-clock failures consumieron los dos reinicios normales; stdout/stderr originales archivados en role-failure-archive/19 y23. No crédito ni reset. Tras tests/build/checkpoint, crash propio controlado, Watchdog y START-Recover ejecutaron nuevo Supervisor/Worker/tests/build preservando contador2 y reloj.

La consulta sí se envió una vez por Enter; SENT_CONFIRMED precedió a espera de respuesta. La respuesta se recibió y el ledger llegó a COMPLETED. El post-check composer_empty devolvió false porque había2 contenteditables renderizados: un CodeMirror de la respuesta y el composer verdadero vacío. No hubo entrega ambigua. final-live-readonly.json prueba ambos nodos. Respuesta actual recuperada sin interacción, SHA idéntico al ledger; no se cambió ledger ni evidencia nativa. El retry lógico posterior no modifica ledger ni envía nada. Los artefactos posteriores no convierten el run fallido en PASS.

244 fuentes de admisión,49 pins de aprobación,6343 archivos históricos, tests/reloj y6 componentes protegidos verificados antes del cierre documental. Modelo qwen36/127.0.0.1:8080/ctx65536/parallel1; Hermes0.21.6 intacto. Cero procesos propios huérfanos, locks/8080/9119 libres y mutex de inferencia FREE. Browser preexistente preservado; guard de suspensión sólo por hilo liberado. Métricas originales conservadas. Sin dependencias/updates/push.

Aislar identidad del composer, excluir editores de mensajes/código y certificar con CodeMirror real antes de otro E2E limpio. Evidencia: evidence/phase-24-attempt-10-20261015/; capturas nativas byte idénticas, SUMMARY/FINAL/stage-results, recovery, source/integrity/cleanup y response-recovery-readonly.
