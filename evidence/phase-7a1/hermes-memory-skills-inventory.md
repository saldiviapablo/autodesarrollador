# Inventario Real de Hermes v0.21.6 — Subfase 7A.1 (Memoria Persistente y Skills Reutilizables)

**Fecha de inspección:** 2026-10-12  
**Versión de Hermes verificada:** `v0.21.6 (2026.4.14)` (`git commit 4d97dc792`)  
**Binario:** `C:\Users\Pc\AppData\Local\hermes\bin\hermes.exe`  
**Código fuente local:** `C:\Users\Pc\AppData\Local\hermes\hermes-agent`  
**Perfil activo (`-p desarrollador-autonomo`):** `C:\Users\Pc\AppData\Local\hermes\profiles\desarrollador-autonomo`

---

## 1. Hallazgos sobre `HERMES_HOME` y Layout en Windows

- En esta instalación Windows no se utiliza `C:\Users\Pc\.hermes`; la raíz instalada es `C:\Users\Pc\AppData\Local\hermes`.
- Al invocar `hermes -p desarrollador-autonomo ...`, `get_hermes_home()` resuelve al directorio del perfil:
  `C:\Users\Pc\AppData\Local\hermes\profiles\desarrollador-autonomo`.
- Dentro del perfil existen:
  - `config.yaml` (configuración del perfil)
  - `SOUL.md` (identidad y reglas base del supervisor)
  - `memories\` (directorio de memoria persistente nativa, inicialmente vacío)
  - `skills\` (directorio de skills reutilizables del perfil)
  - `sessions\` y `state.db` (historial de sesiones SQLite)

---

## 2. Mecanismo Real de Memoria Persistente Nativa (`MEMORY.md` / `USER.md`)

Inspeccionado en `tools/memory_tool.py`, `tools/memory_tool_store.py` y `agent/agent_init.py`:

1. **Almacenamiento en disco:**
   - `memories\MEMORY.md` (`target="memory"`, límite por defecto `2200` caracteres, configurable mediante `memory.memory_char_limit`).
   - `memories\USER.md` (`target="user"`, límite por defecto `1375` caracteres, configurable mediante `memory.user_char_limit`).
   - Las entradas se separan mediante el delimitador `ENTRY_DELIMITER = "\n§\n"`.
   - Escritura atómica mediante archivo temporal y bloqueo cross-process con archivo `.lock` (`msvcrt.locking` en Windows).
2. **Ciclo de vida entre sesiones:**
   - Al iniciar cualquier sesión (`AIAgent._init_memory`), `MemoryStore.load_from_disk()` lee `MEMORY.md` y `USER.md` y construye un snapshot congelado (`_system_prompt_snapshot`) que se inyecta en la capa `volatile` del system prompt bajo el bloque:
     `MEMORY (your personal notes) [X% — N/M chars]`.
   - Durante la sesión, la herramienta nativa `memory` (`action="add" | "replace" | "remove"`, o lote `operations=[...]`) persiste inmediatamente los cambios en `MEMORY.md` / `USER.md`.
   - Cualquier sesión nueva posterior (`new session_id`) carga automáticamente desde disco las entradas persistidas y las tiene disponibles desde el turno 1 sin depender de la conversación previa.
3. **Brecha detectada en sanitización nativa y solución determinista:**
   - `tools/memory_tool_store.py::_scan_memory_content` bloquea patrones de prompt injection y el patrón `hardcoded_secret` (que sólo detecta asignaciones entrecomilladas de 20+ caracteres y devuelve error en lugar de redactar a `[REDACTED]`), pero **no redacta** automáticamente patrones como `sk-...`, `ghp_...`, `Bearer ...`, `password=...`, `api_key=...`, `token=...` a `[REDACTED]` antes de escribir en `MEMORY.md`.
   - **Solución implementada:** Hermes v0.21.6 soporta nativamente **Shell Hooks `pre_tool_call`** (`agent/shell_hooks.py` + `agent/tool_executor.py::_dispatch_authorized_once`). Cuando un hook `pre_tool_call` devuelve en `stdout` JSON `{"action": "modify", "args": {...}}`, Hermes sustituye `ref.args` **antes** de ejecutar la herramienta `memory`. Así, `scripts/hermes-pre-tool-hook.py` sanitiza determinísticamente cualquier secreto a `[REDACTED]` antes de que toque `MemoryStore` o el disco (`MEMORY.md`).

---

## 3. Mecanismo Real de Skills Reutilizables (`SKILL.md`)

Inspeccionado en `tools/skills_tool.py`, `tools/skill_manager_tool.py`, `agent/prompt_builder.py` y `agent/oneshot_footprint.py`:

1. **Ubicación y formato:**
   - Directorio del perfil: `C:\Users\Pc\AppData\Local\hermes\profiles\desarrollador-autonomo\skills\<category>\<skill-name>\SKILL.md`.
   - Espejo versionado en repositorio: `config\skills\autonomous-dev\<skill-name>\SKILL.md`.
   - Formato obligatorio: frontmatter YAML delimitado por `---` con `name` (`^[a-z0-9][a-z0-9._-]*$`, máx. 64 chars) y `description` concisa (1 oración $\le 150$ chars), seguido de cuerpo Markdown con el procedimiento operativo estándar (SOP).
2. **Descubrimiento y carga (Progressive Disclosure):**
   - **Tier 1 (Índice en System Prompt):** `build_skills_system_prompt()` inyecta el catálogo de skills (`nombre: descripción`) agrupado por categoría en el system prompt.
   - **Tier 2 (Carga bajo demanda o precarga):** El agente invoca `skill_view(name="<skill-name>")` o `skills_list()` para inspeccionar el contenido completo, o bien se precarga mediante `-s <skill-name>` (`--skills`) o `skills.auto_load` en `config.yaml`.
   - **Nota sobre modo `-q` (`oneshot_footprint.py`):** En ejecuciones one-shot (`-q`), Hermes oculta únicamente `skill_manage` (creación/edición en caliente), manteniendo activas `skills_list` y `skill_view`.

---

## 4. Precedencia del System Prompt y Guardrails Deterministas

Inspeccionado en `agent/system_prompt.py`:

1. **`stable` tier:** Identidad (`SOUL.md`) $\rightarrow$ guías de ejecución y herramientas $\rightarrow$ `skills.auto_load` $\rightarrow$ prefijo de codificación.
2. **`context` tier:** `system_message` del invocador $\rightarrow$ archivos de contexto del proyecto (`AGENTS.md`) $\rightarrow$ snapshot del workspace.
3. **`volatile` tier:** Índice de skills $\rightarrow$ snapshot de `MEMORY.md` y `USER.md` $\rightarrow$ secciones de plugins $\rightarrow$ perfil activo $\rightarrow$ timestamp.

Para garantizar que **ninguna Skill ni entrada de Memoria pueda elevar permisos ni contradecir la verdad operativa (Nivel 1 > Nivel 2)**:
- El hook `pre_tool_call` (`scripts/hermes-pre-tool-hook.py`, configurado con `fail_closed: true` y `hooks_auto_accept: true`) intercepta toda llamada a `terminal`, `write_file`, `patch`, `edit_file`, `skill_manage` y `memory`:
  - Bloquea (`{"action": "block", "message": "DENY: ..."}`) cualquier comando prohibido (`git push`, `git reset --hard`, `format`, etc.).
  - Bloquea cualquier intento de modificar archivos protegidos de infraestructura (`config/security.yaml`, `RUN-CONTRACT.yaml`, `runner/`, `scripts/security-guard.ps1`, `scripts/hermes-pre-tool-hook.py`).
  - Bloquea escrituras fuera del workspace permitido (salvo rutas internas del propio perfil Hermes gestionadas por Hermes).
  - Sanitiza secretos a `[REDACTED]` antes de persistir en `MEMORY.md` / `USER.md`.
