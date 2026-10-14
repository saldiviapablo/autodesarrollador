# Estado de Implementación
## Proyecto: Desarrollador Autónomo

**Última actualización:** 2026-10-14T14:56:58.537704-03:00
**Estado documental:** APROBADO / FROZEN PARA IMPLEMENTACIÓN DE MACROFASE 7A
**Baseline de arquitectura:** Hermes Agent (v0.21.6) + Qwen Code CLI (@qwen-code/qwen-code@0.25.1) + llama.cpp local (Qwen3.6-35B-A3B Q4_K_M)

---

## Tabla Oficial de Macrofases del Proyecto

| Macrofase | Título / Alcance | Estado | Evidencia Canónica / Notas |
|:---|:---|:---:|:---|
| **Macrofase 1** | **Baseline e Inventario** (Fases 0 a 4) | **PASS** | Auditoría física y de software en `docs/INVENTORY.md`, baseline Git en `MANIFEST.md`, configuración central en `config/system.yaml` y validación determinista de 66/66 tests en `scripts/verify-config.ps1`. |
| **Macrofase 2** | **Qwen Code CLI** (Fase 5) | **PASS** | Instalación de `@qwen-code/qwen-code@0.25.1`, suite `verify-qwen-code.ps1` exitosa (7/7 capacidades validadas: inferencia local, headless, inspección, autofix, JSON, timeout, resume). |
| **Macrofase 3** | **Hermes Agent** (Fase 6) | **PASS** | Instalación de `hermes-agent` v0.21.6 (commit `818c13b`), endpoint local OpenAI-compatible 64K (`http://127.0.0.1:8080/v1`), suite `verify-hermes.ps1` exitosa (10/10 pruebas validadas). |
| **Macrofase 4** | **Integración Hermes ↔ Qwen Code** (Fases 7 a 9) | **PASS** | Inference Lock cross-process (.NET Mutex), contratos JSON Schema `DelegationRequest`/`DelegationResult`, delegación supervisada completa de 2 agentes con serialización estricta (0 ms solapamiento). Evidencia en `evidence/integration/`. |
| **Macrofase 5** | **Memoria y Continuidad** (Fases 10 a 12) | **PASS** | Estructura `.autopilot/` (`STATE.json`, `RUN-CONTRACT.yaml`, `EVENTS.jsonl`), Protocolo de Recuperación de 15 pasos y continuidad multi-sesión validada con pérdida total de contexto en chat. Evidencia en `evidence/continuity/`. |
| **Macrofase 6** | **Web, ChatGPT, Seguridad y Anti-Loop** (Fases 13 a 16) | **PASS** | Web Research seguro (Fase 13), Chrome dedicado CDP con consulta real a ChatGPT y validación UTF-8/BOM (Fase 14), Guardrails deterministas de rutas, comandos y secretos (Fase 15) y Motor Anti-loop con escalera de escalamiento (Fase 16). Evidencias en `evidence/web/`, `evidence/chatgpt/`, `evidence/security/` y `evidence/anti-loop/`. |
| **Macrofase 7A** | **Capacidades Nativas de Hermes** (Subfases 7A.1 a 7A.10) | **PASS** | **Subfase 7A.1 = PASS** (Memoria Persistente + Skills SOP + Hook SHA-256; 6/6 pruebas en `evidence/phase-7a1/`). **Subfase 7A.2 = PASS** (Servidores MCP gobernados `da_local_sandbox` + Plugin seguro `desarrollador-autonomo-health` con integridad criptográfica SHA-256 y Security Guard; 7/7 pruebas en `evidence/phase-7a2/`). **Subfase 7A.3 = PASS** (extracción nativa gobernada, 5/5 pruebas y smoke en `evidence/phase-7a3/`). **Subfase 7A.4 = PASS** (native browser local/headless, gobernanza, timeout/cleanup, integración real y smoke en `evidence/phase-7a4/`). **Subfase 7A.5 = PASS** (tres roles reales, subagente nativo, serialización y políticas heredadas; `evidence/phase-7a5/`). **Subfase 7A.6 = PASS** (`evidence/phase-7a6/`). **Subfase 7A.7 = PASS** (`evidence/phase-7a7/`). **Subfase 7A.8 = PASS** (`evidence/phase-7a8/`). **Subfase 7A.9 = PASS** (`evidence/phase-7a9/`). **Subfase 7A.10 = PASS** (`evidence/phase-7a10/`). ChatGPT Idempotency **PASS**; regression gate final **PASS** (`evidence/regression-7a-final/`). |
| **Macrofase 7B** | **Runner Autónomo Nocturno** (Fases 17 a 22) | **PASS** | Orquestador determinista de procesos, integración obligatoria `Cron → Runner → Watchdog → RUN-CONTRACT` (`T-RUN-009`), Watchdog de fallos, Launchers limpios `INICIAR`/`DETENER`, Completion Gate objetivo, reportes estandarizados y Cleanup garantizado. |
| **Macrofase 8** | **Validación Final** (Fases 23 a 28) | **FAIL / BLOCKED_REQUIRES_HUMAN** | Suite integral en sandbox, pruebas autónomas prolongadas (E2E corto, 2 horas y nocturna de 6-8 horas), auditoría integral y piloto en proyecto real no crítico. |

---

## Desglose Detallado de Fases Internas

| Fase | Título | Estado | Detalle Operativo |
|:---|:---|:---:|:---|
| **Fase 0** | Documentación base | **PASS** | Documentación técnica completa (00 a 08, AGENTS.md, MANIFEST.md) alineada y congelada. |
| **Fase 1** | Inventario del entorno | **PASS** | Inventario real registrado en `docs/INVENTORY.md`. |
| **Fase 2** | Backup y baseline | **PASS** | Respaldo inicial en `backups/preinstall-*/`, baseline Git inicial. |
| **Fase 3** | Validación llama.cpp + Qwen | **PASS** | Validado 64K context, `--parallel 1`, alias `qwen36`, inferencia exitosa (33.1 tok/s). |
| **Fase 4** | Configuración central | **PASS** | Archivos `config/system.yaml`, `config/security.yaml`, `config/VERSIONS.lock`. 66/66 tests PASS. |
| **Fase 5** | Qwen Code CLI | **PASS** | CLI local verificado con suite de 7 pruebas en sandbox. |
| **Fase 6** | Hermes Agent | **PASS** | Supervisor verificado con suite de 10 pruebas autónomas. |
| **Fase 7** | Model Gateway / Inference Lock | **PASS** | Primitiva de exclusión mutua cross-process con recuperación de crash y timeout. |
| **Fase 8** | Worker Qwen Code / Handoff | **PASS** | Contratos estructurados tipados validados con JSON Schema. |
| **Fase 9** | Delegación Hermes → Qwen Code | **PASS** | Flujo completo de 2 agentes, revisión/aceptación y rechazo ante falso éxito. |
| **Fase 10** | Estructura `.autopilot` | **PASS** | Escritura atómica, esquema formal, eventos append-only, redacción de secretos. |
| **Fase 11** | Recovery Protocol | **PASS** | Reconciliación determinista de 15 pasos; 4 escenarios de crash superados. |
| **Fase 12** | Sesiones y continuidad | **PASS** | Principio `CONVERSATION != SOURCE OF TRUTH` certificado en 2 etapas multi-sesión. |
| **Fase 13** | Web Research | **PASS** | Búsqueda técnica y defensa contra prompt injection validada con Hermes en vivo. |
| **Fase 14** | Chrome dedicado + ChatGPT | **PASS** | Perfil dedicado CDP, domain-lock `chatgpt.com`, consulta real sin mock y transporte UTF-8 certificado. |
| **Fase 15** | Guardrails de seguridad | **PASS** | Command Guard 11/11, Path Guard canónico, bloqueo de junctions y redacción de secretos. |
| **Fase 16** | Anti-loop | **PASS** | Normalización de errores, huella de progreso, escalera de escalamiento determinista. |
| **Subfase 7A.1**| Memoria Persistente + Skills | **PASS** | Memoria Nivel 2 (`MEMORY.md`), 3 Skills SOP (`test-failure-diagnosis`, `technical-audit-review`, `safe-refactoring`), hook `pre_tool_call` con verificación criptográfica SHA-256 en `security.yaml` sin auto-accept (`T-7A-MEM-001/002`, `T-7A-SKILL-001/002`, `T-7A-HIERARCHY-001`, `T-7A-HOOK-001` PASS). |
| **Subfase 7A.2**| Servidores MCP + Plugins | **PASS** | Servidor MCP local gobernado `da_local_sandbox` (allowlist de 4 tools, timeout 30s, confinamiento de ruta + junctions, health check y recuperación) y Plugin `desarrollador-autonomo-health` (`da_project_health`, SHA-256 en `security.yaml`, `PLUGIN != PRIVILEGE ESCALATION`). 7/7 pruebas PASS (`T-7A-MCP-001..005`, `T-7A-PLUGIN-001..002`). |
| **Subfase 7A.3** | Extracción documental nativa gobernada | **PASS** | Markdown, JSON, YAML, DOCX, XLSX, PDF con texto y RTF: `read_file` / `extract_document_bytes` reales; contrato/scope/hashes, macros y junctions DENY, redacción, fallo/timeout/cleanup. `T-7A-DOC-001..005` y smoke previo PASS en `evidence/phase-7a3/`; cero dependencias nuevas. |
| **Subfase 7A.4** | Native Browser | **PASS** | Browser built-in local/headless, dominios exactos, policy default DENY, eval bloqueado, Job Object y cleanup/timeout. Integración real Hermes qwen36 serializada PASS; `evidence/phase-7a4/`. |
| **Subfase 7A.5** | Bot Mode + Subagentes | **PASS** | BOT-001/002/003 y SUBAGENT-001 PASS; roles sin tools, hijo síncrono, timeout y cleanup; `evidence/phase-7a5/`. |
| **Subfase 7A.6** | Git Worktrees | **PASS** | Tests, seguridad, cleanup y smoke PASS; `evidence/phase-7a6/`. |
| **Subfase 7A.7** | Cron + No-Agent Jobs | **PASS** | Tests, seguridad, cleanup y smoke PASS; `evidence/phase-7a7/`. |
| **Subfase 7A.8** | Native Dashboard | **PASS** | Tests, seguridad, cleanup y smoke PASS; `evidence/phase-7a8/`. |
| **Subfase 7A.9** | Gateway | **PASS** | Tests, seguridad, cleanup y smoke PASS; `evidence/phase-7a9/`. |
| **Subfase 7A.10** | Controlled Auto-update | **PASS** | Tests, seguridad, cleanup y smoke PASS; `evidence/phase-7a10/`. |
| **ChatGPT Idempotency** | Reserva, deduplicación y reconciliación | **PASS** | T-CHATGPT-010 real + UTF-8/domain/budget/security/cleanup PASS; evidence/chatgpt-idempotency/. |
| **Gate final 7A** | Regression global | **PASS** | 11 gates ejecutables, auditoría de 38 tests obligatorios, 67 checks de integridad, recovery/delegation real y cleanup/hash PASS; `evidence/regression-7a-final/`. |
| **Fase 17** | Runner | **PASS** | evidence/phase-17/; pruebas, seguridad, timeout/cleanup y commit local. |
| **Fase 18** | Watchdog | **PASS** | evidence/phase-18/; pruebas, seguridad, timeout/cleanup y commit local. |
| **Fase 19** | Launcher | **PASS** | evidence/phase-19/; pruebas, seguridad, timeout/cleanup y commit local. |
| **Fase 20** | Completion Gate | **PASS** | evidence/phase-20/; pruebas, seguridad, timeout/cleanup y commit local. |
| **Fase 21** | Reportes | **PASS** | evidence/phase-21/; pruebas, seguridad, timeout/cleanup y commit local. |
| **Fase 22** | Cleanup garantizado | **PASS** | evidence/phase-22/; pruebas, seguridad, timeout/cleanup y commit local. |
| **Fase 23** | Sandbox integral | **PASS** | Reviewer real ACCEPTED, Completion Gate PASS; histórico preservado. evidence/hermes-prompt-transport-20261014/. |
| **Fase 24** | End-to-End corto | **FAIL / BLOCKED_REQUIRES_HUMAN** | ATTEMPT 3: Worker SUCCESS, 13 tests/build y Watchdog PASS; ChatGPT UNKNOWN_DELIVERY, sin reenvío. Reviewer/gate final NOT_RUN. evidence/phase-24-attempt-3-20261014/. |
| **Fase 25** | Prueba 2 horas | **NOT_RUN** | Validación de estabilidad autónoma continua de 2 horas. |
| **Fase 26** | Auditoría integral | **NOT_RUN** | Revisión global de robustez previa a despliegue con proyectos reales. |
| **Fase 27** | Piloto con proyecto real | **NOT_RUN** | Validación sobre proyecto real secundario respaldado en rama dedicada. |
| **Fase 28** | Prueba nocturna 6-8 horas | **NOT_RUN** | Prueba definitiva de autonomía prolongada desatendida. |

---

## Registro histórico de implementación

- **Preflight correctivo 7A:** estados reconciliados; URL absoluta HTTPS y hostname exacto `chatgpt.com` en bridge, wrapper e iniciador. Smoke acotado del hook/sanitización, MCP health/allowlist, plugin SHA-256 y bridge REAL/UTF-8 PASS, con cleanup PASS. Evidencia: `evidence/preflight-7a-correction-20261013/`. 7A.1 y 7A.2 siguen PASS; sus suites completas no se repitieron.
- **Subfase 7A.3:** pruebas obligatorias, seguridad, fallo/timeout, cleanup y smoke PASS (`evidence/phase-7a3/`). El preflight correctivo se cerró con commit local `f133bab` y Git limpio.
- **Subfase 7A.4:** funcional, seguridad, timeout, cleanup, integración Hermes real y smoke PASS. 7A.5 aprobada: flujo real Supervisor → Qwen Code → Reviewer, hijo nativo y smoke PASS. 7A.6 PASS. 7A.7 PASS. 7A.8 PASS. 7A.9 PASS. 7A.10 PASS. ChatGPT Idempotency PASS. Regression gate global **PASS**. **MACROFASE 7A = PASS; READY FOR 7B YES**. Detenido; no iniciar 7B sin nueva instrucción.

F17 = PASS. Próximo gate de 7B tras commit local: F18. No iniciar Macrofase8.

F18 = PASS. Próximo gate de 7B tras commit local: F19. No iniciar Macrofase8.

F19 = PASS. Próximo gate de 7B tras commit local: F20. No iniciar Macrofase8.

F20 = PASS. Próximo gate de 7B tras commit local: F21. No iniciar Macrofase8.

F21 = PASS. Próximo gate de 7B tras commit local: F22. No iniciar Macrofase8.

F22 = PASS. Pendiente: E2E corto 7B y regression smoke final. No iniciar Macrofase8.

## Cierre histórico 7B

MACROFASE 7B = PASS. F17–F22, E2E real COMPLETED con fallo controlado, regression smoke y cleanup global PASS. READY FOR MACROFASE 8 YES. Macrofase 8 PENDING; no comenzar sin una nueva instrucción. Informe: docs/MACROPHASE-7B-FINAL-REPORT.md.

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

## Reconciliación humana F24 sin envío — 2026-10-14

BASELINE_PROVEN YES: 1/1 persistido antes de DELIVERY_INTENT. Fix de la ruta humana PASS para conversaciones existentes; reconciliación automática intacta. Mismo ID f24-7257c739e1fd449aae1f1f93856aef7f: NOT_DELIVERED_CONFIRMED / RETRY_SAFE, una habilitación pendiente, send_attempts permanece 1, cero envíos físicos adicionales. Composer original sin reescribir; turnos 1/1, presupuesto 1/5 y STATE sin cambios. Histórico UNKNOWN_DELIVERY/DELIVERY_INTENT conservado. F23 PASS y evidencias históricas intactas. F24 E2E no certificado y detenido por instrucción humana; F25–F28 no iniciadas. docs/F24-HUMAN-BASELINE-RECONCILIATION.md; evidence/f24-human-baseline-reconciliation-20261014/.

## Envío único F24 autorizado — 2026-10-14

Precheck PASS y un único envío físico del mismo ID y composer. Usuario 1→2, asistente 1→2, composer vacío, respuesta capturada, conversación intacta. Ledger SENT confirmado → COMPLETED; retry lógico ALREADY_SENT / cero envíos adicionales; human_retry_remaining=0. Presupuesto 1/5 y STATE sin cambios, sólo evento nativo CHATGPT_CONSULTED. Histórico preservado, integridad/cleanup PASS. READY_TO_RESUME_F24 YES para una continuación posterior autorizada; F24 E2E aún no certificado. Reviewer, Completion Gate y F25 no ejecutados. Detenido por instrucción humana; F27/F28 no iniciadas. docs/F24-SINGLE-SEND-REPORT.md; evidence/f24-human-send-once-20261014/.

## Cierre F24 detenido en preflight de aceptación — 2026-10-14

F24 FAIL / MANDATORY_TEST_FAILED: el Worker rechaza pesos cero permitidos y acepta importe negativo prohibido por el plan aprobado. Dos probes read-only FAIL, archivos fuente intactos; suites históricas PASS conservadas. Reviewer y Completion Gate NOT_RUN por la instrucción de STOP ante nueva inconsistencia. ChatGPT permanece COMPLETED, cero acciones nuevas. STATE terminal BLOCKED_REQUIRES_HUMAN con motivo actualizado; cleanup e integridad PASS. Métricas originales preservadas y snapshot actual separado; no segmento nativo nuevo. READY_FOR_F25 NO; F25–F28 no iniciadas. docs/F24-CLOSURE-PREFLIGHT-STOP.md; evidence/f24-closure-preflight-blocked-20261014/.

## Corrección Worker F24 bloqueada por plazo congelado — 2026-10-14

Worker correction BLOCKED_REQUIRES_HUMAN / GLOBAL_TIMEOUT: plazo global aprobado 2700s vencido desde 02:54:22 -03:00. Restarts Worker 1/2 todavía con margen; reloj y todos los presupuestos/contadores intactos. STOP conforme a la instrucción de no modificar presupuestos congelados. Cero invocaciones Worker/modelo/ChatGPT y cero ediciones manuales del código; Reviewer/Completion Gate/F25 NOT_RUN. F24 permanece FAIL, tests/build históricos y evidencias conservados. Cleanup/integridad PASS; STATE terminal coherente. docs/F24-WORKER-CORRECTION-BUDGET-STOP.md; evidence/f24-worker-correction-budget-blocked-20261014/.

## Estado vigente — F24 ATTEMPT 3 — 2026-10-14

ATTEMPT 2 (run-20261014-020920) cerrado como FAIL / GLOBAL_TIMEOUT; sus 216 archivos, sandbox, STATE, reloj y presupuestos permanecen intactos. ATTEMPT 3 nuevo run-20261014-143502: launcher/Prepare/preflight/aprobación única, Supervisor, Worker SUCCESS tras 2 reinicios normales, 13 tests/build, checkpoint y crash/Watchdog PASS. Consulta nueva f24-a3-run-20261014-143502-bfca6e98 UNKNOWN_DELIVERY / NO RESEND; F24 FAIL / BLOCKED_REQUIRES_HUMAN. Recovery E2E posterior al crash, Reviewer final y Completion Gate NOT_RUN. Fetch web oficial PASS; lectura de WEB.json por Worker no demostrada. Duración nativa 920.52s dentro de 2700s, sin ampliación. Cleanup/integridad PASS. F23 PASS conservada. READY_FOR_F25 NO; F25–F28 no iniciadas. Informe: docs/F24-ATTEMPT-3-STOP-REPORT.md; evidence/phase-24-attempt-3-20261014/.

## Fronteras antes de ATTEMPT 4 — 2026-10-14

ATTEMPT 3 queda HISTORICAL FAIL / BLOCKED_REQUIRES_HUMAN, ledger intacto y no reutilizable. Hardening A ChatGPT PASS determinista; B/C/regresión conjunta pendientes. Ningún envío real durante estas pruebas. docs/F24-FRONTIER-HARDENING.md; evidence/f24-frontiers-20261014/. F24 permanece FAIL; F25 no iniciada.
