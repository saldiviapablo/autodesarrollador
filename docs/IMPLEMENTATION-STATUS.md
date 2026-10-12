# Estado de Implementación
## Proyecto: Desarrollador Autónomo

**Última actualización:** 2026-10-12T19:22:00-03:00  
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
| **Macrofase 7A** | **Capacidades Nativas de Hermes** (Subfases 7A.1 a 7A.10) | **PENDING** | Congelada documentalmente en `08-CAPACIDADES-NATIVAS-HERMES.md`. Incorpora Memoria N2, Skills, MCP, Extracción documental (`Prefer Native When Verified`), Browser nativo, Bot Mode, Worktrees, Cron/No-agent jobs (validación autónoma en `7A.7`), Web Dashboard (superficie administrativa `127.0.0.1:9119` configurable), Gateway, Auto-update e Idempotencia de ChatGPT (`T-CHATGPT-010`, pendiente de implementar y probar). Ninguna capacidad activa aún. |
| **Macrofase 7B** | **Runner Autónomo Nocturno** (Fases 17 a 22) | **PENDING** | Orquestador determinista de procesos, integración obligatoria `Cron → Runner → Watchdog → RUN-CONTRACT` (`T-RUN-009`), Watchdog de fallos, Launchers limpios `INICIAR`/`DETENER`, Completion Gate objetivo, reportes estandarizados y Cleanup garantizado. |
| **Macrofase 8** | **Validación Final** (Fases 23 a 28) | **PENDING** | Suite integral en sandbox, pruebas autónomas prolongadas (E2E corto, 2 horas y nocturna de 6-8 horas), auditoría integral y piloto en proyecto real no crítico. |

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
| **Fase 7A.1-10**| Hermes Native Capabilities | **PENDING** | 10 subfases canónicas definidas formalmente en `08-CAPACIDADES-NATIVAS-HERMES.md`. |
| **Fase 17** | Runner | **PENDING** | Orquestador determinista del ciclo de vida y gestión de procesos. |
| **Fase 18** | Watchdog | **PENDING** | Monitor de heartbeat, detección de procesos caídos y recuperación limitada. |
| **Fase 19** | Launcher único | **PENDING** | Scripts ejecutables limpios `INICIAR` y `DETENER`. |
| **Fase 20** | Completion Gate | **PENDING** | Validación objetiva multi-criterio antes de permitir estado COMPLETED. |
| **Fase 21** | Reportes | **PENDING** | Generación estandarizada de `FINAL.md`, `BLOCKED.md`, `FAILURE.md`, `STALLED.md`. |
| **Fase 22** | Cleanup garantizado | **PENDING** | Rutina destructora segura (tipo `finally`) para evitar procesos huérfanos. |
| **Fase 23** | Sandbox integral | **PENDING** | Suite completa de pruebas destructivas y recuperación en entorno controlado. |
| **Fase 24** | End-to-End corto | **PENDING** | Ciclo completo de 15 a 45 minutos sin intervención humana. |
| **Fase 25** | Prueba 2 horas | **PENDING** | Validación de estabilidad autónoma continua de 2 horas. |
| **Fase 26** | Auditoría integral | **PENDING** | Revisión global de robustez previa a despliegue con proyectos reales. |
| **Fase 27** | Piloto con proyecto real | **PENDING** | Validación sobre proyecto real secundario respaldado en rama dedicada. |
| **Fase 28** | Prueba nocturna 6-8 horas | **PENDING** | Prueba definitiva de autonomía prolongada desatendida. |

---

## Próximo Paso Recomendado

- **Aprobación de la Revisión Documental de Arquitectura:** El usuario revisará el catálogo congelado de capacidades nativas (`08-CAPACIDADES-NATIVAS-HERMES.md`), la incorporación de las capas `HERMES CAPABILITY LAYER` y `DETERMINISTIC CONTROL LAYER`, el nuevo modelo de memoria de 3 niveles + Skills, y la reestructuración del Roadmap en Macrofases 7A, 7B y 8.
- **Inicio de Macrofase 7A (Hermes Native Capabilities):** Proceder con la implementación secuencial (7A.1 → 7A.2 → ...) únicamente tras la aprobación formal de esta revisión documental.
