# Manifiesto del Sistema
## Proyecto: Desarrollador Autónomo

**Versión de especificación:** 2.0  
**Baseline:** Establecido en Fase 2 (Backup y Baseline)  
**Host de ejecución:** Windows 11 Pro (Build 26200, 64 bits)

---

# 1. Documentación Oficial

El sistema se rige formalmente por la siguiente documentación técnica canónica (en orden de precedencia operativa):

1. **`AGENTS.md`**: Reglas permanentes y precedencia obligatoria para agentes de IA (Antigravity, Codex, etc.).
2. **`04-AUTONOMIA-Y-SEGURIDAD.md`**: Políticas de seguridad, límites de workspace, anti-loop y guardrails.
3. **`01-OBJETIVOS-Y-REQUISITOS.md`**: Especificación funcional y criterios de aceptación globales.
4. **`02-ARQUITECTURA.md`**: Arquitectura del sistema, supervisión, serialización y ciclo de vida.
5. **`03-MEMORIA-Y-CONTINUIDAD.md`**: Jerarquía de verdad, persistencia de estado (.autopilot), sesiones y recuperación.
6. **`05-INSTALACION-Y-CONFIGURACION.md`**: Requisitos de entorno, configuración central y directivas de despliegue.
7. **`06-PRUEBAS-Y-CRITERIOS-DE-EXITO.md`**: Catálogo de pruebas, criterios de éxito y Completion Gate.
8. **`07-ROADMAP.md`**: Orden cronológico obligatorio de implementación por fases (Fase 0 a Fase 28).
9. **`00-README.md`**: Visión general del proyecto y filosofía de trabajo.

---

# 2. Arquitectura Base

La cadena de trabajo aprobada es:

```text
USUARIO (Aprobación única)
    │
    ▼
HERMES AGENT (Supervisor / Orquestador)
    │
    ▼
QWEN CODE CLI (Coding Worker principal)
    │
    ▼
LLAMA.CPP (127.0.0.1:8080)
    │
    ▼
Qwen3.6-35B-A3B Q4_K_M (64K context)
    │
    ▼
PROYECTO + GIT LOCAL
```

### Componentes Deterministas Auxiliares:
- **Night Supervisor / Runner:** Control de ciclo de vida, timeouts, health y cleanup garantizado.
- **Watchdog:** Detección de fallos de procesos, heartbeat y recuperación controlada.
- **Inference Lock:** Serialización estricta de inferencia (`--parallel 1`) entre supervisor y worker.
- **Sistema de Estado:** `.autopilot/` (`RUN-CONTRACT.yaml`, `STATE.json`, `STATE.md`, `EVENTS.jsonl`, checkpoints).
- **Completion Gate:** Validación objetiva multi-criterio antes de permitir el estado `COMPLETED`.

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

# 4. Estado Actual de Implementación

- **Fase 0 (Documentación base):** PASS
- **Fase 1 (Inventario del entorno real):** PASS (Registrado en `docs/INVENTORY.md` y `logs/inventory-audit-20261011.log`)
- **Fase 2 (Backup y Baseline):** PASS (Punto de restauración `backups/preinstall-*/`, `.gitignore`, baseline Git)
- **Fase 3 (Validación llama.cpp + Qwen):** PASS (Validado 64K, parallel 1, qwen36, inferencia local y cleanup)
- **Fase 4 (Configuración central):** PASS (Configuraciones YAML, VERSIONS.lock, suite determinista de 66 pruebas)
- **Fase 5 (Qwen Code CLI):** PASS (Instalado @qwen-code/qwen-code@0.25.1, 7 capacidades validadas)
- **Fase 6 (Hermes Agent):** PASS (Instalado hermes-agent v0.21.6, perfil aislado, 10 pruebas validadas)
- **Fase 7 (Model Gateway / Inference Lock):** PASS (Primitiva System.Threading.Mutex + metadata en runtime/locks, crash recovery, timeout)
- **Fase 8 (Worker Qwen Code / Handoff):** PASS (Contratos DelegationRequest/DelegationResult validados con JSON Schema, ejecución sandbox)
- **Fase 9 (Delegación Hermes → Qwen Code):** PASS (Flujo 2 agentes, revisión/aceptación, rechazo ante falso éxito, serialización estricta 0 ms)
- **Fase 10 (Estado Persistente .autopilot):** PASS (Esquemas validados, atomic write + previous backup, eventos append-only, sanitización, checkpoints)
- **Fase 11 (Recovery y Reconciliación):** PASS (Protocolo de 15 pasos, Crash A/B/C/D resueltos, checkpoints, verificación de idempotencia)
- **Fase 12 (Continuidad de Sesiones):** PASS (Principio CONVERSATION != SOURCE OF TRUTH certificado, recuperación de contexto sin historial, etapas multi-sesión)
- **Fase 13 (Web Research):** PASS (Búsqueda gratuita DDG/Wiki/GitHub/PyPI, contenedor no confiable, defensa prompt injection con Hermes en vivo)
- **Fase 14 (Chrome Dedicado + ChatGPT):** PASS (Perfil HERMES-CHATGPT, CDP 9222, domain-lock, 1 pestaña, presupuesto global, login manual, rol consultivo)
- **Fase 15 (Guardrails de Seguridad):** PASS (Command Guard 11/11, Path Guard con canonical check, bloqueo de junctions, redacción de secretos, policy merge estricto)
- **Fase 16 (Anti-Loop / Timeouts):** PASS (Firmas de error normalizadas, fingerprints de avance real, límites de repetición, escalera de escalamiento, kill de árbol de procesos)
- **Fases 17 a 28:** PENDING

---

# 5. Regla Fundamental de Verificación

> **Las capacidades, flags y versiones específicas deben verificarse siempre contra el software y las herramientas realmente instaladas en el host, y nunca asumirse ciegamente por documentación teórica.**
