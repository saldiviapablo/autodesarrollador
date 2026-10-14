# F24 — corrección Worker bloqueada por presupuesto temporal

STATUS: BLOCKED_REQUIRES_HUMAN. Worker no iniciado; invoice.py no editado por Codex.

La autorización permite corregir los dos incumplimientos mediante Qwen Code,
pero exige STOP si fuera necesario modificar un presupuesto congelado.
La validación de la aprobación original PASS; sus hashes/digest siguen intactos.

RUN-PLAN fija global_timeout_seconds=2700 y phase_timeout_seconds=300.
El reloj persistido de run-20261014-020920 empezó el 2026-10-14 a las
02:09:22.8396032 -03:00. Deadline efectivo: 02:54:22.8396032 -03:00, vencido.
El límite del contrato de 120 minutos también está vencido; el plan aplica
el límite más estricto de 45 minutos. El reloj cuenta tiempo de pared y no
descuenta la espera humana.

RESTARTS conserva worker=1, supervisor=0, reviewer=0, llama=0; restart_budget=2.
Hay margen de un restart, pero no queda tiempo global. Ciclos/progreso tampoco
están agotados. runner/run.ps1 restaura el reloj original y runner/core.ps1
aplica GLOBAL_TIMEOUT. tests/test-phase22.py certifica la preservación del
deadline tras recuperación. No se ejecutó ese test nuevamente.

No existe crédito temporal aprobado para una corrección Worker F24. El harness
de mantenimiento Reviewer F23 usa un reloj separado; reutilizarlo aquí con
Started=Now eludiría el presupuesto global. No se cambió PLAN, contrato,
reloj, aprobación, guardrails ni contadores. No se invocó el Worker directamente
para evitar el control del Runner. Se detuvo antes de iniciar inferencia.

El alcance de corrección y los cinco casos obligatorios se prepararon en
worker-correction-scope-not-dispatched.json, con la evidencia de los fallos
anteriores. No fueron despachados. Tests anteriores y todos los FAIL se preservan.
ChatGPT permanece COMPLETED; no hubo consulta, reconciliación, web,
launcher, crash ni recovery.

```text
WORKER_CORRECTION = BLOCKED / GLOBAL_TIMEOUT
ZERO_WEIGHT = FAIL (previo, sin cambios)
NEGATIVE_AMOUNT = FAIL (previo, sin cambios)
FULL_TESTS = NOT_RUN (históricos PASS)
BUILD = NOT_RUN (histórico PASS)
REVIEWER = NOT_RUN
COMPLETION_GATE = NOT_RUN
F24 = FAIL
CLEANUP = PASS
READY_FOR_F25 = NO
```

Cleanup: cero procesos propios supervivientes, Inference Lock y run mutex FREE,
sin locks/lease pendientes, puertos 8080/9119 libres. Chrome preexistente intacto.
STATE terminal BLOCKED_REQUIRES_HUMAN actualizado mediante State Manager normal;
presupuesto de ChatGPT, métricas, código y artefactos de Worker sin cambios.

Git infraestructura: evidencia/estado en commit local separado, sin push.
Sandbox conserva el diff preexistente de README.md e invoice.py, sin aprobarlo
ni ocultarlo. No hay nuevas dependencias ni actualizaciones.

EVIDENCE: evidence/f24-worker-correction-budget-blocked-20261014/.
BACKUP: backups/f24-worker-correction-budget-blocked-20261014/.
NEXT PHASE: ninguna; requiere decisión explícita sobre el presupuesto vencido.
