# Documentación del Subsistema de Configuración
## Proyecto: Desarrollador Autónomo — Directorio `config/`

**Versión:** 2.0 (Fase 4 — Configuración Central)  
**Estado:** VIGENTE Y CANÓNICO  

---

# 1. Propósito de este Directorio

El directorio `config/` centraliza toda la configuración declarativa y las políticas maestras del sistema para evitar que rutas, parámetros de modelo, puertos, límites o reglas de seguridad queden dispersos o duplicados en múltiples scripts.

A partir de la Fase 4, los componentes y scripts de la infraestructura deben consumir estos archivos como fuente única de verdad técnica.

---

# 2. Archivos del Subsistema

### 2.1 `config/system.yaml`
Es la **fuente técnica declarativa** de la infraestructura:
- **`system`**: Identificación del sistema y entorno.
- **`paths`**: Directorio raíz de infraestructura y herramientas de IA.
- **`llama`**: Parámetros validados para el servidor de inferencia local:
  - Binario verificado (`llama-server.exe`).
  - Ruta absoluta del modelo GGUF snapshot.
  - Endpoints (`/health`, `/v1/models`, `/v1/chat/completions`).
  - Parámetros operativos validados en Fase 3 (`ctx_size: 65536`, `parallel: 1`, `cpu_moe: true`, `n_gpu_layers: 99`, `cache_type: q8_0`, `jinja: true`).
  - Registro de advertencias conocidas (`known_warnings`, e.g., mmap con CPU MoE).
- **`runner`**: Timeouts de arranque, espera de peticiones y período de heartbeat.
- **`limits`**: Presupuestos operativos de ciclos, reintentos y escalamiento anti-loop.

### 2.2 `config/security.yaml`
Define las **políticas maestras de seguridad y guardrails** inmutables del host:
- **Límites de workspace:** Prohibición de escritura fuera del proyecto y aplicación de canonical path.
- **Políticas de Git:** Prohibición estricta de `git push`, `--force` y resets destructivos.
- **Políticas de sistema operativo:** Prohibición de elevación UAC en runtime, reinicio, apagado, alteración del registro de Windows o cambios de firewall.
- **Políticas de red:** Aislamiento estricto de llama local en `127.0.0.1` (sin exposición pública ni túneles).
- **Políticas de navegador y ChatGPT:** Perfil dedicado (`HERMES-CHATGPT`), domain-lock en `chatgpt.com` y límites de consultas.
- **Protección de credenciales:** Prohibición absoluta de secretos en Git, logs, estado o prompts.
- **Lista de comandos bloqueados:** Patrones peligrosos prohibidos por política.

### 2.3 `config/VERSIONS.lock`
Es el **manifiesto de bloqueo de versiones** del entorno físico y lógico:
- Formato: **YAML estructurado determinista**, legible por humanos y parseable sin librerías adicionales.
- Registra exclusivamente versiones reales auditadas y comprobadas en las Fases 1, 2 y 3.
- Separa claramente herramientas activas (`VALIDATED`), no instaladas (`NOT_INSTALLED`) y legadas (`LEGACY`).

### 2.4 `config/INSTALLATION-STATE.json`
Rastrea el progreso formal de la hoja de ruta de instalación (Fases del Roadmap).

---

# 3. Precedencia de Configuración

Si existe cualquier contradicción o conflicto entre directivas, rige estrictamente el siguiente orden jerárquico descendente:

```text
1. Políticas globales de seguridad (config/security.yaml)
       ↓
2. Contrato de ejecución (.autopilot/RUN-CONTRACT.yaml)
       ↓
3. Configuración del proyecto / sistema (config/system.yaml)
       ↓
4. Instrucciones del agente (prompts y memoria auxiliar)
       ↓
5. Decisiones del modelo (inferencia activa)
```

> **Regla de oro de seguridad:** Una capa inferior **NUNCA** puede hacer más permisiva una regla establecida por una capa superior.

---

# 4. Qué Valores NUNCA deben Almacenarse en `config/`

Este directorio contiene **únicamente configuración declarativa y estática**. Está estrictamente prohibido almacenar en `config/system.yaml`, `config/security.yaml` o `config/VERSIONS.lock`:

- PIDs de procesos en ejecución.
- Métricas volátiles de memoria (RAM libre/usada, VRAM actual).
- Identificadores de sesión efímeros (`session_id`).
- Timestamps de ejecuciones o ciclos.
- Estado transaccional de tareas activas o pendientes.
- **Credenciales, API keys, tokens de autenticación o cookies.**

Toda esa información pertenece exclusivamente a `.autopilot/STATE.json`, `.autopilot/HEARTBEAT.json`, `.autopilot/LOCK.json`, o a los registros en `logs/`.

---

# 5. Consumo de YAML en el Entorno Local

- **Host:** Windows PowerShell 5.1 (Desktop Edition) sin módulos YAML externos instalados.
- **Consumo determinista:** El host cuenta nativamente con Python 3.14.4 y **`PyYAML 6.0.3`** ya instalado en su librería de paquetes.
- **Estrategia técnica:** Cuando los scripts de PowerShell o el futuro Runner requieran parsear de forma estructurada `system.yaml` o `security.yaml`, pueden invocar directamente el motor Python existente con PyYAML para convertirlo a JSON estándar o consumir variables de manera determinista, evitando la introducción de dependencias externas en PowerShell y eliminando la necesidad de parsers caseros frágiles.
