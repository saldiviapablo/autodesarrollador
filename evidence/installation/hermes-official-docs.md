# Documentación Oficial y Opciones CLI — Hermes Agent
## Proyecto: Desarrollador Autónomo — Fase 6

**Repositorio oficial:** `NousResearch/hermes-agent` (GitHub)  
**Sitio web oficial:** `https://hermes-agent.nousresearch.com` / `https://hermes-agent.org`  
**Versión estable identificada:** `v0.21.6`  
**Commit de release:** `818c13be1dc4fd28987e1e881a9408224afd4535`  
**Fecha de publicación:** `2026-10-08T11:51:57Z`  
**Soporte nativo en Windows:** Windows 10/11 x64 mediante installer `install.ps1` en `%LOCALAPPDATA%\hermes`.

---

# 1. Arquitectura de Proveedores Personalizados (OpenAI-Compatible)

Hermes Agent incluye soporte de primera clase para endpoints compatibles con la API de OpenAI (vLLM, Ollama, llama.cpp):

- **Tipo de proveedor:** `custom` (o proveedor compatible OpenAI).
- **Parámetros clave de configuración:**
  - `base_url`: URL base del servidor (e.g., `http://127.0.0.1:8080/v1`).
  - `model`: Identificador del modelo servido (e.g., `qwen36`).
  - `api_key`: Credencial de acceso (en entornos locales sin autenticación se utiliza un sentinel como `local-not-required`).
  - `context_length`: Ventana de contexto máxima utilizable (fijada en `65536` para nuestro entorno).
  - `api_mode` / `transport`: `chat_completions`.

---

# 2. Sistema de Perfiles Aislados (`profiles`)

Hermes Agent implementa un sistema nativo de perfiles para desacoplar por completo distintos proyectos y entornos:

- **Aislamiento total:** Cada perfil mantiene su propio directorio independiente con:
  - `config.yaml`: Configuración de modelo, proveedor y herramientas.
  - `state.db`: Base de datos SQLite para persistencia de sesiones.
  - `memories/`: Directorio de memorias a largo plazo (`MEMORY.md`, `USER.md`).
  - `logs/`: Registros de ejecución específicos del perfil.
  - `skills/`: Habilidades personalizadas del agente.
- **Creación de perfil:** `hermes profile create <nombre>`
- **Invocación con perfil:** `hermes -p <nombre> <comando>`
- **Perfil asignado al proyecto:** `desarrollador-autonomo`.

---

# 3. Modos de Ejecución Headless / One-Shot

Hermes Agent ofrece comandos nativos para ejecución no interactiva y desatendida en scripts y runners:

1. **Modo One-Shot Limpio (`-z`):**
   - Sintaxis: `hermes -p <perfil> -z "<prompt>"`
   - Suprime la interfaz TUI interactiva, spinners y banners decorativos, emitiendo directamente la respuesta del agente.
2. **Modo Consulta (`chat -q`):**
   - Sintaxis: `hermes -p <perfil> chat -q "<prompt>"`
   - Soporta formato estructurado con `--format json` o `--format stream-json`.
3. **Límites de Turnos (Budgets):**
   - Parámetro `--max-turns <N>` (o configurable en `config.yaml` del perfil) para limitar el número de ciclos de interacción y llamadas a herramientas en una sesión desatendida.

---

# 4. Diagnóstico y Comprobación del Sistema

- **`hermes doctor`:** Inspecciona la salud del entorno, conectividad con el proveedor configurado, herramientas disponibles y estado de la base de datos.
- **`hermes config`:** Muestra y valida la configuración activa del perfil seleccionado.
