# Documentación Oficial y Opciones CLI — Qwen Code 0.25.1
## Proyecto: Desarrollador Autónomo — Fase 5

**Paquete oficial:** `@qwen-code/qwen-code`  
**Versión instalada:** `0.25.1`  
**Fecha de release en npm:** `2026-10-11T10:29:32.140Z`  
**Requisitos de Node:** `engines: { node: '>=22.0.0' }` (Entorno actual: Node `24.14.1` / npm `11.11.0`)  
**Ruta del ejecutable:** `C:\Users\Pc\AppData\Roaming\npm\qwen.cmd`  

---

# 1. Configuración de Modelos Locales (OpenAI-compatible)

Qwen Code 0.25.1 cuenta con soporte nativo de primera clase para endpoints compatibles con OpenAI:

- `--auth-type openai`: Selecciona el proveedor compatible con la API de OpenAI (descartando `qwen-oauth`, `anthropic`, `gemini`).
- `--openai-base-url <url>`: URL base del endpoint local (`http://127.0.0.1:8080/v1`).
- `--openai-api-key <dummy>`: Credencial local sentinel (`local-not-required`).
- `-m, --model <model>`: Identificador del modelo registrado en llama.cpp (`qwen36`).
- `--openai-logging`: Registro opcional de llamadas para auditoría en `evidence/`.

Alternativamente, el CLI honra variables de entorno estándar de proceso:
- `OPENAI_BASE_URL`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`

---

# 2. Modos de Ejecución Headless y Salida Estructurada

- **Prompt no interactivo:** Se pasa como argumento posicional o mediante `-p <prompt>`.
- **Formato de salida estructurada:** `-o json` (o `--output-format json`). Emite un objeto JSON estructurado con el resultado de la sesión, tokens consumidos, llamadas a herramientas y metadatos.
- **Dual output mode:** `--json-file <path>` o `--json-fd <number>` permite guardar la traza JSON mientras el proceso se ejecuta.

---

# 3. Modos de Aprobación (`--approval-mode`)

El CLI ofrece 5 modos de aprobación granular:
1. `plan`: Modo solo lectura y análisis. Prohíbe modificar archivos o ejecutar comandos shell.
2. `default`: Requiere confirmación interactiva para escrituras y ejecuciones de comandos.
3. `auto-edit`: Aprueba automáticamente modificaciones de archivos pero pide confirmación para comandos de consola.
4. `auto`: Clasificador que aprueba acciones consideradas seguras y bloquea las riesgosas.
5. `yolo` (`-y, --yolo`): Aprueba automáticamente todas las herramientas sin interacción del usuario.

> **Advertencia de seguridad oficial:** El modo YOLO ejecuta herramientas con todos los permisos del proceso. No constituye un sandbox en sí mismo. En este proyecto se utiliza exclusivamente dentro del directorio aislado `sandbox/`, bajo control de Git local y con budgets estrictos de tiempo y llamadas.

---

# 4. Presupuestos y Límites (Budgets)

- `--max-wall-time <duration>`: Presupuesto total de tiempo por reloj de pared (e.g. `120s`, `10m`). Si se excede, aborta inmediatamente la ejecución con código de salida `55`.
- `--max-session-turns <number>`: Límite máximo de turnos en la sesión.
- `--max-tool-calls <number>`: Límite acumulativo de llamadas a herramientas ejecutadas. Si se excede, aborta con código `55`.

---

# 5. Continuidad de Sesión (`--continue` / `--resume`)

- `-c, --continue`: Reanuda la sesión más reciente dentro del proyecto actual (`cwd`).
- `-r, --resume <session-id>`: Reanuda una sesión específica a partir de su identificador UUID.
- `--session-id <id>`: Permite fijar un identificador de sesión determinista para la ejecución.
- `--chat-recording`: Grabación de historial en disco (habilitada por defecto en `.qwen/`).
