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
- **Macrofase 8 (Validación Final - Fases 23 a 28):** **IN_PROGRESS (F23 PASS; adaptador F24 PASS; intento 2 pendiente)**

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
