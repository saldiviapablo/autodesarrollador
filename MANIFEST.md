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
- **Fase 2 (Backup y Baseline):** EN PROCESO / COMPLETADA (Punto de restauración `backups/preinstall-*/`, `.gitignore`, baseline Git)
- **Fases 3 a 28:** PENDING

---

# 5. Regla Fundamental de Verificación

> **Las capacidades, flags y versiones específicas deben verificarse siempre contra el software y las herramientas realmente instaladas en el host, y nunca asumirse ciegamente por documentación teórica.**
