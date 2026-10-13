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
- **Macrofase 7A (Hermes Native Capabilities - Subfases 7A.1 a 7A.10):** **IN_PROGRESS** (`7A.1 — Memoria Persistente + Skills`: **PASS**; `7A.2 — MCP + Plugins`: **PASS**; `7A.3 — Document Extraction`: **PASS**; `7A.4 — Native Browser`: **PASS**; `7A.5–7A.10`: **PENDING**). Preflight correctivo aprobado en commit `f133bab`.
- **Macrofase 7B (Runner Autónomo Nocturno - Fases 17 a 22):** **PENDING**
- **Macrofase 8 (Validación Final - Fases 23 a 28):** **PENDING**

---

# 5. Regla Fundamental de Verificación

> **Las capacidades, flags y versiones específicas deben verificarse siempre contra el software y las herramientas realmente instaladas en el host, y nunca asumirse ciegamente por documentación teórica.**
