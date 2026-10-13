# Estado de Implementación
## Proyecto: Desarrollador Autónomo

**Última actualización:** 2026-10-13T19:52:29.816470-03:00
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
| **Fase 23** | Sandbox integral | **FAIL** | Path Guard fix PASS. Intento 3 bloqueado por UNKNOWN_DELIVERY tras reconciliación real, no resend. evidence/phase-23-attempt-3/. |
| **Fase 24** | End-to-End corto | **NOT_RUN** | Ciclo completo de 15 a 45 minutos sin intervención humana. |
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
