# Manifiesto del Sistema
## Proyecto: Desarrollador Autónomo

**Versión de especificación:** 2.0
**Estado:** APROBADO / FROZEN PARA IMPLEMENTACIÓN DE MACROFASE 7A
**Baseline:** Establecido en Fase 2 (Backup y Baseline) y congelado para Macrofase 7A
**Host de ejecución:** Windows 11 Pro (Build 26200, 64 bits)

---

# 1. Documentación Oficial

El sistema se rige formalmente por la siguiente documentación técnica canónica (en orden de precedencia operativa):

1. **`AGENTS.md`**: Reglas permanentes y precedencia obligatoria para agentes de IA (Antigravity, Codex, etc.).
2. **`04-AUTONOMIA-Y-SEGURIDAD.md`**: Políticas de seguridad, límites de workspace, anti-loop y guardrails.
3. **`01-OBJETIVOS-Y-REQUISITOS.md`**: Especificación funcional y criterios de aceptación globales.
4. **`02-ARQUITECTURA.md`**: Arquitectura del sistema, supervisión, serialización y ciclo de vida.
5. **`03-MEMORIA-Y-CONTINUIDAD.md`**: Jerarquía de verdad, persistencia de estado (.autopilot), sesiones y recuperación.
6. **`08-CAPACIDADES-NATIVAS-HERMES.md`**: Catálogo canónico, gobernanza y matriz de capacidades nativas de Hermes.
7. **`05-INSTALACION-Y-CONFIGURACION.md`**: Requisitos de entorno, configuración central y directivas de despliegue.
8. **`06-PRUEBAS-Y-CRITERIOS-DE-EXITO.md`**: Catálogo de pruebas, criterios de éxito y Completion Gate.
9. **`07-ROADMAP.md`**: Orden cronológico obligatorio de implementación por macrofases (1 a 8).
10. **`00-README.md`**: Visión general del proyecto y filosofía de trabajo.

---

# 2. Arquitectura Base y Separación de Capas

La cadena de trabajo aprobada es:

```text
USUARIO (Aprobación única)
    │
    ▼
HERMES SUPERVISOR (Orquestador principal)
    │
    ├──────────────────────────┐
    ▼                          ▼
QWEN CODE CLI           HERMES REVIEWER
(Coding Worker)      (Auditor independiente)
    │                          │
    └──────────┬───────────────┘
               │ [Serializado vía Inference Lock]
               ▼
LLAMA.CPP (127.0.0.1:8080)
    │
    ▼
Qwen3.6-35B-A3B Q4_K_M (64K context)
    │
    ▼
PROYECTO + GIT LOCAL
```

### Capas del Sistema:
1. **HERMES CAPABILITY LAYER:** Memoria persistente (Nivel 2), Skills reutilizables (Memoria procedimental), servidores MCP, plugins de herramientas, Browser Automation nativo, Bot Mode (Supervisor, Reviewer, Researcher), subagentes jerárquicos, Git Worktrees, Cron y Jobs sin agente, extracción documental (`Prefer Native When Verified`), Gateway y Web Dashboard (superficie administrativa y observabilidad en `127.0.0.1:9119` por defecto, configurable).
2. **DETERMINISTIC CONTROL LAYER (Autoritativa):** `RUN-CONTRACT.yaml`, `STATE.json`, `EVENTS.jsonl`, checkpoints inmutables, Security Guard, Progress Guard, Inference Lock (.NET Mutex cross-process, `parallel = 1`), Runner de ciclo de vida, Watchdog de procesos, Completion Gate y Cleanup garantizado.

### Modelo de Memoria:
- **Nivel 1 (Operativo Autoritativo):** Filesystem, Git, tests/builds, `STATE.json`, `RUN-CONTRACT.yaml`, `EVENTS.jsonl`. Prevalece sobre cualquier otro nivel.
- **Nivel 2 (Memoria Persistente Hermes):** Lecciones aprendidas, preferencias técnicas y patrones estables. Consultiva; no puede declarar estado de tests o archivos.
- **Nivel 3 (Memoria de Sesión):** Conversación activa y contexto transitorio. Auxiliar y volátil.
- **Memoria Procedimental (Skills):** SOPs estandarizados en Markdown. No pueden alterar directivas de seguridad.

---

# 3. Configuración Qwen Principal

Configuración base oficial validada:

```text
Binario: C:\AI\llama.cpp\llama-server.exe
Modelo: C:\Users\Pc\.cache\huggingface\hub\models--ggml-org--Qwen3.6-35B-A3B-GGUF\snapshots\baec3ebee244827cda0f4557eafa8b28f7545fa6\Qwen3.6-35B-A3B-Q4_K_M.gguf
Alias: qwen36
Host: 127.0.0.1
Puerto: 8080

Parámetros validados:
--ctx-size 65536
--parallel 1
--cpu-moe
--n-gpu-layers 99
--flash-attn on
--cache-type-k q8_0
--cache-type-v q8_0
--jinja
```

---

# 4. Estado Actual de Implementación por Macrofases

- **Macrofase 1 (Baseline e Inventario - Fases 0 a 4):** **PASS**
- **Macrofase 2 (Qwen Code CLI - Fase 5):** **PASS**
- **Macrofase 3 (Hermes Agent - Fase 6):** **PASS**
- **Macrofase 4 (Integración Hermes ↔ Qwen Code - Fases 7 a 9):** **PASS**
- **Macrofase 5 (Memoria y Continuidad - Fases 10 a 12):** **PASS**
- **Macrofase 6 (Web, ChatGPT, Seguridad y Anti-Loop - Fases 13 a 16):** **PASS**
- **Macrofase 7A (Hermes Native Capabilities - Subfases 7A.1 a 7A.10):** **PASS** (`7A.1 — Memoria Persistente + Skills`: **PASS**; `7A.2 — MCP + Plugins`: **PASS**; `7A.3 — Document Extraction`: **PASS**; `7A.4 — Native Browser`: **PASS**; `7A.5 — Bot Mode + Subagentes`: **PASS**; `7A.6 — Git Worktrees`: **PASS**; `7A.7 — Cron + No-Agent Jobs`: **PASS**; `7A.8 — Native Dashboard`: **PASS**; `7A.9 — Gateway`: **PASS**; `7A.10 — Controlled Auto-update`: **PASS**; `ChatGPT Idempotency`: **PASS**; `regression gate`: **PASS**). Preflight correctivo aprobado en commit `f133bab`.
- **Macrofase 7B (Runner Autónomo Nocturno - Fases 17 a 22):** **PASS**
- **Macrofase 8 (Validación Final - Fases23 a28):** **IN_PROGRESS**; F23/F24/F25/4H/F26 PASS; F27/F28 pendientes

---

# 5. Regla Fundamental de Verificación

> **Las capacidades, flags y versiones específicas deben verificarse siempre contra el software y las herramientas realmente instaladas en el host, y nunca asumirse ciegamente por documentación teórica.**

Actualización operativa 2026-10-13T16:00:00.067794-03:00: Macrofase7B IN_PROGRESS; F17 (Runner) PASS; evidence/phase-17/. 7A permanece PASS.

Actualización operativa 2026-10-13T16:18:30.312213-03:00: Macrofase7B IN_PROGRESS; F18 (Watchdog) PASS; evidence/phase-18/. 7A permanece PASS.

Actualización operativa 2026-10-13T16:23:57.480503-03:00: Macrofase7B IN_PROGRESS; F19 (Launcher) PASS; evidence/phase-19/. 7A permanece PASS.

Actualización operativa 2026-10-13T16:37:16.325404-03:00: Macrofase7B IN_PROGRESS; F20 (Completion Gate) PASS; evidence/phase-20/. 7A permanece PASS.

Actualización operativa 2026-10-13T16:40:23.240900-03:00: Macrofase7B IN_PROGRESS; F21 (Reportes) PASS; evidence/phase-21/. 7A permanece PASS.

Actualización operativa 2026-10-13T16:58:45.255234-03:00: Macrofase7B IN_PROGRESS; F22 (Cleanup garantizado) PASS; evidence/phase-22/. 7A permanece PASS.

Informe canónico 7B: docs/MACROPHASE-7B-FINAL-REPORT.md. Evidencia: evidence/phase-17/ a phase-22/, evidence/e2e-7b/, evidence/regression-7b-final/. Estado: PASS; Macrofase 8 PENDING.

## Validación histórica Macrofase 8 — intento 1

Preflight PASS. F23 FAIL: SECURITY_REGRESSION en Prepare; rechazo de junction posterior a escrituras fuera del proyecto declarado. F24–F26 y 2h/4h NOT_RUN por gate anterior FAIL. Cleanup PASS, inferencias locales 0. Certificaciones anteriores preservadas como historial, no como prueba de este caso nuevo. READY FOR REAL PILOT NO. Informe: docs/MACROPHASE-8-STOP-REPORT.md.

## Validación histórica Macrofase 8 — intento 2

Prepare fix PASS (b6e421b). PREPARE_ZERO_WRITE_ON_DENY y casos A–H PASS. F23 integral FAIL / SECURITY_REGRESSION: T-F23-PATHGUARD-EXISTING-TARGET-JUNCTION devuelve ALLOW para destino canónico fuera del proyecto. No se efectuó escritura. F24–F26, 2h/4h y regression final NOT_RUN por gate F23 FAIL. Cleanup e integridad PASS; inferencias locales 0. READY FOR REAL PILOT NO. Informe: docs/MACROPHASE-8-STOP-REPORT-ATTEMPT-2.md. Intento 1 y STOP-REPORT original intactos.

## Validación del fix Macrofase 8 — intento 3

Path Guard fix PASS: destino físico central, A–J READ/WRITE PASS, Prepare/MCP/plugin/Runner smokes PASS. Histórico FAIL de intentos 1/2 intacto. F23 integral IN_PROGRESS; F24–F28 NOT_RUN hasta su gate. READY FOR REAL PILOT NO. Informe del fix: docs/PATH-GUARD-FIX.md.

## Estado actual Macrofase 8 — bloqueo del intento 3

Path Guard fix PASS (6e0a507), A–J READ/WRITE y Prepare/MCP/plugin/Runner smokes PASS. F23 integral FAIL / BLOCKED_REQUIRES_HUMAN: consulta real ChatGPT UNKNOWN_DELIVERY persiste tras reconciliación, sin reenvío. Web real obtenida; agentes y recovery de runtime NOT_RUN. F24–F28 y regression final NOT_RUN. Cleanup/locks/integridad PASS. READY FOR REAL PILOT NO. Informe: docs/MACROPHASE-8-BLOCKED-REPORT-ATTEMPT-3.md.

## Reconciliación humana F23 — 2026-10-14

DELIVERY_NOT_OCCURRED confirmado por inspección humana. Mismo ID f23-ee298529568f4f8b94f4dd16f90a0be4, un único nuevo envío físico autorizado, user +1 / assistant +1, respuesta capturada y composer vacío. Retry lógico ALREADY_SENT / 0 envíos adicionales. Budget permanece 1. Reconciliación PASS; F23 se reanuda en el mismo sandbox. F24–F28 no iniciadas. docs/F23-HUMAN-RECONCILIATION.md; evidence/f23-human-reconciliation/.

## Estado histórico F23 antes del fix del transporte — 2026-10-14

Reconciliación humana PASS, consulta COMPLETED mismo ID, retry ALREADY_SENT / 0 envíos nuevos. F23 reanudada: tests/build y recovery real PASS; Reviewer FAIL por argumentos CLI mal transportados, único reinicio agotado. F23 FAIL / MANDATORY_TEST_FAILED; F24–F28 y regression final NOT_RUN. Cleanup/integridad PASS; Chrome preexistente del usuario conservado abierto. READY FOR REAL PILOT NO. docs/F23-RESUME-STOP-REPORT-20261014.md.

## Cierre del transporte Reviewer y F23 — 2026-10-14

Transporte nativo stdin UTF-8 PASS; Reviewer real ACCEPTED; Completion Gate y F23 PASS. Histórico FAIL preservado. Macrofase 8 IN_PROGRESS; F24–F26 pendientes; F27/F28 no iniciadas. READY FOR REAL PILOT NO. docs/HERMES-REVIEWER-PROMPT-FIX.md; evidence/hermes-prompt-transport-20261014/.

## Parada vigente F24 — 2026-10-14

F23 PASS y fix Reviewer PASS (d7ee477). F24 FAIL / MANDATORY_TEST_FAILED: adaptador del launcher no alcanzó el Runner; no regresión del producto demostrada. Diagnóstico del adaptador PASS sin repetir F24 real. F25/4H/F26 y regression final NOT_RUN por gate fallido. Cleanup PASS; F27/F28 no iniciadas. READY FOR REAL PILOT NO. docs/F24-ADAPTER-STOP-REPORT-20261014.md; evidence/phase-24-20261014/.

## Continuación F24 — fix del adaptador — 2026-10-14

Adaptador F24 PASS (A–H, ejecución única, UTF-8, vacío, exit code, stdout/stderr y deny de metacaracteres). F23 PASS preservada. F24 intento 2 pendiente de corrida real; Macrofase 8 IN_PROGRESS. F25/4H/F26 NOT_RUN; F27/F28 no iniciadas. docs/F24-LAUNCHER-ADAPTER-FIX.md.

## Estado vigente — F24 intento 2 — 2026-10-14

Adaptador F24 A–H PASS (fea2a71). F23 PASS preservada. F24 real intento 2 FAIL / BLOCKED_REQUIRES_HUMAN: launcher/Runner/Supervisor/Worker, tests/build, checkpoint, crash y Watchdog ejecutados; ChatGPT UNKNOWN_DELIVERY, un intento, sin reenvío. Reviewer final/Completion Gate no alcanzados. F25/4H/F26 y regression final NOT_RUN. Cleanup e integridad PASS. READY FOR REAL PILOT NO. docs/F24-ATTEMPT-2-BLOCKED-REPORT.md.

## Estado vigente — F24 ATTEMPT 3 — 2026-10-14

ATTEMPT 2 (run-20261014-020920) cerrado como FAIL / GLOBAL_TIMEOUT; sus 216 archivos, sandbox, STATE, reloj y presupuestos permanecen intactos. ATTEMPT 3 nuevo run-20261014-143502: launcher/Prepare/preflight/aprobación única, Supervisor, Worker SUCCESS tras 2 reinicios normales, 13 tests/build, checkpoint y crash/Watchdog PASS. Consulta nueva f24-a3-run-20261014-143502-bfca6e98 UNKNOWN_DELIVERY / NO RESEND; F24 FAIL / BLOCKED_REQUIRES_HUMAN. Recovery E2E posterior al crash, Reviewer final y Completion Gate NOT_RUN. Fetch web oficial PASS; lectura de WEB.json por Worker no demostrada. Duración nativa 920.52s dentro de 2700s, sin ampliación. Cleanup/integridad PASS. F23 PASS conservada. READY_FOR_F25 NO; F25–F28 no iniciadas. Informe: docs/F24-ATTEMPT-3-STOP-REPORT.md; evidence/phase-24-attempt-3-20261014/.

## Estado vigente — F24 ATTEMPT 4 — 2026-10-14

Fronteras A/B/C y smokes previos PASS (aabf021, 7de9bf9, c846e2a). Nuevo run-20261014-201149: Prepare/preflight/aprobación/launcher/Supervisor/diagnóstico FAIL inicial/fetch/entrega explícita PASS. Worker TIMEOUT y un reinicio normal 1/2; Worker final SUCCESS con 13 tests/build PASS en sus herramientas, pero consumo web NOT_PROVEN (marcador/SHA ausentes). Runner STOP RESEARCH_CONSUMPTION_NOT_PROVEN; F24 FAIL / MANDATORY_TEST_FAILED. Crash/START-Recover E2E/ChatGPT/Reviewer/Completion Gate NOT_RUN. Consulta nueva no ejecutada, cero envíos. Duración 729.54s; límites 2700/fase300/restart2/maxcycles5 sin ampliar. Cleanup/integridad PASS, 419 archivos históricos intactos. ATTEMPT3 permanece HISTORICAL FAIL / BLOCKED_REQUIRES_HUMAN y su ledger no se tocó. F23 PASS; READY_FOR_F25 NO; F25/F27/F28 no iniciadas. docs/F24-ATTEMPT-4-STOP-REPORT.md; evidence/phase-24-attempt-4-20261014/.

## Estado vigente — F24 ATTEMPT 5 — 2026-10-14

WEB_GATE_FIX PASS, F24_HARNESS_PREFLIGHT PASS, 28 gates congelados (8c8bfdf; runtime import fix c2b1268, previo a Prepare/START). Run nuevo run-20261014-210131: Worker SUCCESS, web fetch/context delivered PASS, 13 tests/build PASS antes y después de crash/Watchdog/START-Recover/continuación reales PASS. ChatGPT FAIL por SEND_BUTTON_UNAVAILABLE_OR_AMBIGUOUS antes de click: 0 envíos, ledger UNKNOWN_DELIVERY/no_resend, reserva 1/5 preservada. Reviewer/Completion Gate NOT_RUN. F24 FAIL / BLOCKED_REQUIRES_HUMAN. Duración 684.78s, límites 2700/fase300/restart2/maxcycles5 intactos, cero reinicios de agentes. Cleanup/integridad PASS; 629 archivos históricos intactos, ATTEMPT4 mantiene FAIL histórico y ATTEMPT3 no reconciliada/reenvíada. No corrección post-START, reenvío, ATTEMPT6 ni F25/F27/F28. READY_FOR_F25 NO. docs/F24-ATTEMPT-5-STOP-REPORT.md; evidence/phase-24-attempt-5-20261014/.

## Estado vigente — admisión F24 ATTEMPT 6 detenida — 2026-10-14

Actuador ChatGPT A–L y UI read-only PASS; prueba real controlada FAIL antes de envío: navegar a raíz conservó el borrador histórico, PREEXISTING_COMPOSER_NO_SEND, 0 intentos físicos. No retry/reconciliación. Preflight del harness FAIL por HEARTBEAT_STALE repetido en probe de recovery/cleanup. ATTEMPT6 NOT_RUN, sin nuevo run/clock/aprobación; no ATTEMPT7. ATTEMPT5 y 955 archivos históricos intactos. Cleanup final e integridad PASS; F24 conserva FAIL; READY_FOR_F25 NO. Informe: docs/F24-ATTEMPT-6-ADMISSION-STOP-REPORT.md; evidence/f24-attempt6-preflight-20261014/.

## Estado vigente — Nuevo chat conserva borrador; STOP — 2026-10-14

Fix de aislamiento UI implementado y deterministas PASS. Un click de navegación Nuevo chat no produjo composer vacío: FRESH_CHAT_READY FAIL, hash histórico intacto. 0 envíos, 0 DELIVERY_INTENT, ledger de prueba no reservado; ATTEMPT5 sin cambios/reconciliación. STOP explícito; heartbeat fixture corregido pero NOT_VERIFIED, preflight completo NOT_RUN, ATTEMPT6 NOT_CREATED/NOT_RUN. Cleanup e integridad PASS (4146 archivos y 6 componentes protegidos). F24 conserva FAIL; READY_FOR_F25 NO; no ATTEMPT7/F25/F27/F28/push. docs/F24-FRESH-CHAT-STOP-REPORT.md; evidence/f24-admission-repair-20261014/.

## Estado vigente — F24 ATTEMPT 6 — 2026-10-15

Working tree parcial retomado. Transaction/legacy recovery/UTF-8/heartbeat/controlled send/preflight PASS (ca74d12,5b4834d); Git limpio antes de START. Nuevo run-20261015-005747: Worker SUCCESS, web fetch/context delivered,13 tests/build, checkpoint/crash/Watchdog/START-Recover/continuación PASS. Fresh-chat FAIL: en root vacío el contador incluyó turnos antiguos no renderizados (1/1); 0 envíos y ledger F24 no reservado. Sin fix/retry/reconciliación tras START. Reviewer/Completion Gate NOT_RUN. F24 FAIL / BLOCKED_REQUIRES_HUMAN; 699.25s, límites2700/300/restart2/cycles5 intactos. Cleanup/integridad PASS;46 pins y4185 archivos históricos intactos. READY_FOR_F25 NO; no ATTEMPT7/F25/F27/F28/push. docs/F24-ATTEMPT-6-STOP-REPORT.md; evidence/phase-24-attempt-6-20261014/.

## Estado vigente — F24 ATTEMPT 7 — 2026-10-15

F24 ATTEMPT7 **FAIL**; run `run-20261015-014509`, duración 1062.94s. Worker SUCCESS; web fetch/context PASS/PASS; 13 tests/build PASS/PASS; crash/Watchdog/START-Recover/continuación PASS/PASS/PASS. ChatGPT COMPLETED, método COMPOSER_ENTER_KEY, acciones físicas 1; Reviewer FAIL / NO_ACCEPTED_DECISION; Completion Gate FAILED. Cleanup e integridad PASS; historial intacto. READY_FOR_F25 NO; F25 y ATTEMPT8 no iniciados. docs/F24-ATTEMPT-7-REPORT.md; evidence/phase-24-attempt-7-20261015/.

## Estado vigente — F24 ATTEMPT 8 — 2026-10-15

F24 ATTEMPT8 **FAIL**; run `run-20261015-025148`, duración 842.39s. Worker SUCCESS; 13 tests/build PASS/PASS; web y continuación real PASS/PASS; ChatGPT PRE_SEND_ABORTED, cero envíos; Reviewer y Completion Gate NOT_RUN. Cleanup/integridad PASS. Los28 gates no aprobaron: ejecución detenida antes de completar sus inputs. Intentos anteriores conservan sus FAIL históricos. F25 pendiente; aislar/fijar/certificar selector composer antes de nuevo E2E. docs/F24-ATTEMPT-8-REPORT.md; evidence/phase-24-attempt-8-20261015/

## Estado vigente — F24 ATTEMPT9 — 2026-10-15

F24 ATTEMPT9 **FAIL**, run `run-20261015-031335`, 1062.11s, gates incompletos (PASS no demostrado); Worker SUCCESS; tests/build PASS/PASS; web/continuación PASS/PASS; ChatGPT PRE_SEND_ABORTED, envíos 0, retry NOT_RUN, adicionales None; Reviewer NOT_ACCEPTED_OR_NOT_RUN; Completion NOT_RUN; cleanup/integridad PASS. F25 pendiente. docs/F24-ATTEMPT-9-REPORT.md; evidence/phase-24-attempt-9-20261015/

## Estado vigente — F24 ATTEMPT10 — 2026-10-15

F24 ATTEMPT10 **FAIL**, run `run-20261015-035008`, 1128.75s. Worker/tests13/build/web/recovery y continuación PASS. Ledger COMPLETED,1 envío físico, respuesta recuperada read-only con SHA exacto; retry lógico posterior ALREADY_SENT/+0. Fallo final del clasificador: CodeMirror de la respuesta confundido con composer. Reviewer/Completion NOT_RUN;28 gates no aprobados. Cleanup/integridad PASS; F25 pendiente. docs/F24-ATTEMPT-10-REPORT.md; evidence/phase-24-attempt-10-20261015/

## Estado vigente — F24 ATTEMPT11 — 2026-10-15

F24 ATTEMPT11 **PASS**, run `run-20261015-044359`, 881.50s, 28/28 gates; Worker SUCCESS;13 tests/build PASS/PASS; web/continuación PASS/PASS; ChatGPT COMPLETED, envíos 1, retry ALREADY_SENT, adicionales 0; Reviewer ACCEPTED; Completion COMPLETED; cleanup/integridad PASS. F25 pendiente. docs/F24-ATTEMPT-11-REPORT.md; evidence/phase-24-attempt-11-20261015/

## Estado vigente — F25 — 2026-10-15T14:00:54.701948+00:00

F25 PASS: 7772.089s reales, 13 tareas completas, recuperación real, cero intervención humana tras START, todos los Reviewer/Completion/checkpoints PASS. Recursos/continuidad/cleanup/integridad PASS. Evidencia: evidence/endurance-f25-20261015-050751-1239ed/. docs/F25-REPORT-f25-20261015-050751-1239ed.md

## Estado vigente — 4H — 2026-10-15T18:10:41.141557+00:00

4H PASS: 14781.279s reales, 26 tareas completas, recuperación real, cero intervención humana tras START, todos los Reviewer/Completion/checkpoints PASS. Recursos/continuidad/cleanup/integridad PASS. Evidencia: evidence/endurance-4h-20261015-110202-059517/. docs/4H-REPORT-4h-20261015-110202-059517.md

## Estado vigente — F26 — 2026-10-15T18:49:43.769161+00:00

F26 PASS: 51 regression suites, 299 audit checks, 259 source hashes and 6119 historical evidence files verified. Actual F24/2h/4h evidence binds native roles, recovery, bridge and cleanup. docs/F26-REPORT-phase-26-audit-20261015-154228.md
