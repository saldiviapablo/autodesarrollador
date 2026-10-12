# 08 — Capacidades Nativas de Hermes
## Proyecto: Desarrollador Autónomo

**Versión:** 2.0  
**Estado:** BASELINE DE ARQUITECTURA (PENDIENTE DE IMPLEMENTACIÓN EN MACROFASE 7A)  
**Arquitectura base:** Hermes Agent + Qwen Code CLI + Qwen local mediante llama.cpp

---

# 1. Propósito y Filosofía de Integración

Este documento define el catálogo oficial, la especificación técnica, las políticas de seguridad y la matriz de preparación de las capacidades nativas de **Hermes Agent** (versión instalada v0.21.6) que se integran en la arquitectura del **Desarrollador Autónomo**.

### 1.1 Principio Rector: "Prefer Native When Verified"
Se preferirán las capacidades nativas provistas por Hermes Agent frente a desarrollos a medida propios **únicamente** cuando se cumplan simultáneamente las siguientes condiciones:
1. Estén presentes y comprobadas en la versión congelada de Hermes (`NousResearch/hermes-agent` v0.21.6).
2. Hayan superado una revisión formal de seguridad y encuadre en el modelo de privilegios mínimos.
3. Hayan superado las suites de pruebas deterministas correspondientes (funcionales, seguridad, fallos y cleanup).
4. No debiliten, sustituyan ni reduzcan las garantías provistas por la Capa de Control Determinista.

> **Regla de oro:** No sustituir componentes probados existentes por el simple hecho de que Hermes ofrezca una alternativa nativa. La evidencia verificable y la estabilidad determinista siempre tienen prioridad sobre la conveniencia sintética.

### 1.2 Separación Estricta de Capas
La incorporación de estas capacidades consolida una arquitectura dividida en dos capas complementarias pero desacopladas:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        HERMES CAPABILITY LAYER                         │
│  - Memoria Persistente (Nivel 2)      - Cron / Rutinas                 │
│  - Skills (Memoria Procedimental)     - Jobs sin Agente                │
│  - Servidores MCP                     - Extracción Documental          │
│  - Plugins / Herramientas Custom      - Gateway Multiplataforma        │
│  - Browser Automation Nativo          - Web Dashboard                  │
│  - Bot Mode (Supervisor/Reviewer)     - Subagentes Jerárquicos         │
│  - Git Worktrees Isolados             - Auto-Update Controlado         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Operaciones reguladas por contrato
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      DETERMINISTIC CONTROL LAYER                       │
│  - RUN-CONTRACT.yaml                  - Progress Guard (Anti-loop)     │
│  - STATE.json / EVENTS.jsonl          - Inference Lock (parallel = 1)  │
│  - Checkpoints Inmutables             - Runner de Ciclo de Vida        │
│  - Filesystem & Git Real              - Watchdog de Procesos           │
│  - Tests & Builds Objetivos           - Cleanup Garantizado            │
│  - Security Guard (Path/Command/Secret)                                │
└────────────────────────────────────────────────────────────────────────┘
```

Ninguna capacidad de la **Hermes Capability Layer** puede sobreescribir, puentear o sustituir la verdad técnica dictada por la **Deterministic Control Layer**.

---

# 2. Catálogo y Matriz de Estado de Capacidades

A continuación se detalla el estado oficial de preparación y gobernanza de las 14 capacidades nativas de Hermes y del componente de idempotencia:

| CAPACIDAD | PROPÓSITO | SUPPORTED_BY_INSTALLED_VERSION | ENABLED | CONFIGURED | SECURITY_REVIEWED | TESTED | PRODUCTION_READY | DEPENDENCIES | FALLBACK | NOTAS |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---|:---|:---|
| **1. Cron / Routines** | Planificación temporal de tareas recurrentes y rondas de mantenimiento | SÍ (CLI `hermes cron`) | **NO** | NO | NO | NO | **NO** | Python scheduler, Runner | Tareas periódicas disparadas por Runner | Controlado exclusivamente por Runner |
| **2. Jobs sin Agente** | Ejecución determinista de tareas de mantenimiento sin inferencia LLM | SÍ (Hermes task runner) | **NO** | NO | NO | NO | **NO** | Scripts deterministas propios | Scripts PowerShell estándar | Cero consumo de tokens e Inference Lock |
| **3. Skills Reutilizables** | Memoria procedimental: guías operativas y SOPs especializados | SÍ (`~/.hermes/skills/`) | **NO** | NO | NO | NO | **NO** | Markdown estructurado, validadores | Prompts en contexto / instrucciones | Sólo lectura; no alteran seguridad |
| **4. Memoria Persistente** | Memoria contextual de Nivel 2: preferencias, decisiones y lecciones | SÍ (`MEMORY.md` / core memory) | **NO** | NO | NO | NO | **NO** | Storage local Hermes | `QWEN.md` y `.autopilot/` | Auxiliar; Git y tests superan esta memoria |
| **5. Servidores MCP** | Conexión modular a herramientas y servicios vía protocolo MCP | SÍ (`hermes mcp`) | **NO** | NO | NO | NO | **NO** | Clientes stdio/SSE MCP | Herramientas CLI nativas | Principio de mínima superficie |
| **6. Plugins / Tools** | Extensión modular de herramientas custom para Hermes | SÍ (Python tool plugins) | **NO** | NO | NO | NO | **NO** | Runtime Python | Scripts invocados vía Terminal | Verificación de integridad estricta |
| **7. Browser Nativo** | Navegación e investigación web sin navegador gráfico pesado | SÍ (Hermes Agent Browser) | **NO** | NO | NO | NO | **NO** | Dependencias headless browser | `web-research.py` existente | Jerarquía: Nativo → MCP → ChatGPT Bridge |
| **8. Bot Mode** | Especialización de roles (Supervisor, Reviewer, Researcher) | SÍ (Hermes profiles/bots) | **NO** | NO | NO | NO | **NO** | Hermes core, Inference Lock | Supervisor monolítico Hermes | Inferencia 100% serializada (`parallel = 1`) |
| **9. Subagentes** | Descomposición jerárquica de tareas en trabajadores efímeros | SÍ (Hermes subagent spawn) | **NO** | NO | NO | NO | **NO** | Inference Lock, Runner | Delegación directa Hermes → Qwen Code | Subagentes no pueden escalar privilegios |
| **10. Git Worktrees** | Aislamiento físico de ramas para trabajadores en paralelo | SÍ (Git CLI integration) | **NO** | NO | NO | NO | **NO** | Git 2.5+, espacio en disco | Rama dedicada estándar `agent/<run>` | En `.autopilot-worktrees/`; sin merge ciego |
| **11. Web Dashboard** | Interfaz visual de monitorización y observabilidad | SÍ (Hermes Web UI) | **NO** | NO | NO | NO | **NO** | Servidor web local, puerto libre | Logs y `STATE.md` en terminal | No es dependencia crítica del Runner |
| **12. Gateway Multiplataforma**| Emisión de alertas y notificaciones vía Telegram/Discord/Slack | SÍ (Hermes Gateways) | **NO** | NO | NO | NO | **NO** | Tokens API, red saliente | Logs en disco y reportes locales | Modo unidireccional (notificación) inicial |
| **13. Extracción Documentos** | Parsing estructurado de formatos ofimáticos (PDF, DOCX, XLSX) | SÍ (con libs opcionales) | **NO** | NO | NO | NO | **NO** | Libs Python especializadas | Visores de texto / scripts de extracción | Libs opcionales no se instalan aún |
| **14. Auto-Update Controlado** | Actualización segura de Hermes bajo pipeline canary y rollback | SÍ (`hermes update`) | **NO** | NO | NO | NO | **NO** | Git / wheel manager, test suite | Congelación de versión fija (v0.21.6) | Actualización ciega terminantemente prohibida |
| **15. ChatGPT Idempotency** | Prevención de doble envío y deduplicación estricta de consultas | SÍ (Bridge extendido) | SÍ | SÍ | SÍ | SÍ | **NO** (Req. 7A) | Chrome CDP, `chatgpt-bridge.js` | Modo de error determinista | `consultation_id`, tracking de turnos +1 |

---

# 3. Especificación Técnica de las Capacidades

## 3.1 Cron / Routines
- **Definición:** Mecanismo de programación temporal de eventos dentro de Hermes para activar revisiones periódicas, chequeos de salud o disparadores de arranque.
- **Relación con el Runner:** Cron **no** sustituye al Runner ni al Watchdog. El Runner de ciclo de vida es el proceso padre del sistema operativo. Si Cron se utiliza, actúa subordinado al Runner:
  ```text
  Cron Routine
      ↓
  Invoca Runner de Tarea
      ↓
  Run Autónomo Bajo RUN-CONTRACT
  ```
- **Límites de Seguridad:** Las tareas programadas no pueden modificar la política de seguridad global, no pueden ejecutar scripts no registrados en allowlist y no pueden saltarse el Inference Lock.

## 3.2 Jobs sin Agente (Deterministic No-Agent Jobs)
- **Definición:** Tareas programadas o de mantenimiento que se resuelven exclusivamente mediante lógica determinista (scripts en PowerShell o Python) sin involucrar ningún LLM.
- **Alcance Operativo:**
  - Limpieza de logs antiguos o temporales en `logs/`.
  - Verificación de hashes SHA-256 de archivos críticos y backups.
  - Health checks de endpoints y conectividad.
  - Verificación periódica de espacio en disco y memoria.
  - Generación de copias de seguridad de `.autopilot/STATE.json`.
- **Ventaja de Rendimiento:** **Cero (0) inferencias LLM**. No consumen tokens ni saturan el `Inference Lock`.

## 3.3 Skills Reutilizables (Memoria Procedimental)
- **Definición:** Conjunto de procedimientos operativos estandarizados (SOPs) empaquetados en archivos Markdown legibles estructurados, que enseñan a los agentes cómo abordar tareas técnicas complejas de manera uniforme.
- **Ciclo de Promoción a Skill:**
  ```text
  Experiencia Práctica Repetida
      ↓
  Procedimiento Estable y Validado
      ↓
  Revisión Humana / Auditoría de Seguridad
      ↓
  Skill Reutilizable en ~/.hermes/skills/
  ```
- **Restricción Inviolable:** Un Skill es una guía de razonamiento y acción metodológica; **bajo ninguna circunstancia** puede redefinir o puentear directivas de `security.yaml` o `RUN-CONTRACT.yaml`.

## 3.4 Memoria Persistente Nativa de Hermes (Nivel 2)
- **Definición:** Capacidad de Hermes de retener conocimiento semántico entre sesiones a través de su subsistema de almacenamiento de memoria.
- **Alcance de Contenido:**
  - Preferencias arquitectónicas declaradas por el usuario.
  - Decisiones de diseño y lecciones aprendidas en tareas previas.
  - Patrones de depuración que funcionaron eficazmente.
- **Límites Canónicos:** La memoria persistente jamás puede afirmar el estado de un test, build o archivo actual. Esos aspectos pertenecen a la Memoria Operativa Autoritativa (Nivel 1) y deben verificarse siempre en vivo.

## 3.5 Servidores MCP (Model Context Protocol)
- **Definición:** Protocolo estándar para extender las herramientas de Hermes mediante servidores desacoplados que exponen recursos, prompts y herramientas.
- **Principio de Mínima Superficie:** No se admitirán servidores MCP monolíticos con docenas de herramientas no utilizadas. Cada servidor MCP integrado debe pasar por:
  - **Allowlist estricto de herramientas:** sólo se habilitan las funciones indispensables.
  - **Scope delimitado:** restricción a rutas de filesystem específicas o endpoints concretos.
  - **Timeouts individuales:** prevención de cuelgues ante servidores MCP no responsivos.
  - **Health check determinista:** validación de disponibilidad antes de la invocación.

## 3.6 Plugins y Custom Tools
- **Definición:** Extensiones modulares de código que introducen herramientas especializadas en el runtime de Hermes.
- **Criterio de Elección:**
  - Si una capacidad nativa de Hermes satisface la necesidad, ha sido auditada y testeada, se adopta preferentemente para reducir código redundante.
  - Si se requiere un comportamiento determinista no provisto o salvaguardas especiales de seguridad, se implementa una herramienta custom dedicada.

## 3.7 Automatización de Navegador Nativa (Browser Automation)
- **Definición:** Capacidad de navegación web headless o controlada para investigación técnica profunda y extracción de contenido dinámico.
- **Jerarquía Operativa de Navegadores:**
  ```text
  1. Browser Nativo de Hermes      → Para búsqueda técnica e inspección de docs
  2. MCP Browser / Playwright      → Para pruebas E2E de aplicaciones web si aplica
  3. Hardened ChatGPT Bridge (CDP) → Acceso exclusivo y restringido a chatgpt.com
  ```
- No se sustituye el bridge de ChatGPT por el navegador general; cada uno mantiene su perfil y restricciones específicas.

## 3.8 Bot Mode (Roles Especializados Serializados)
- **Definición:** Configuración de múltiples identidades de agente dentro de Hermes para segregar responsabilidades:
  - `HERMES SUPERVISOR`: Orquesta, planifica, gestiona contratos y valida entregables.
  - `QWEN CODE`: Coding Worker dedicado a implementación y refactorización.
  - `HERMES REVIEWER`: Auditor independiente que valida diffs y verifica criterios de aceptación.
  - `HERMES RESEARCHER`: Investigador auxiliar de documentación técnica.
- **Serialización Absoluta:** Todos los roles se ejecutan sobre el único modelo local `qwen36` (`--parallel 1`). El `Inference Lock` garantiza que **en ningún momento** dos bots compitan por inferencia simultánea.

## 3.9 Subagentes Jerárquicos
- **Definición:** Capacidad del Supervisor de crear instancias temporales de subagentes para resolver subproblemas específicos de alcance acotado.
- **Gobernanza:**
  - El Supervisor retiene el control del presupuesto de tiempo/turnos y la validación final.
  - Los subagentes operan con permisos idénticos o más restringidos que el Supervisor; **nunca** pueden escalar privilegios, ejecutar comandos prohibidos ni modificar la infraestructura.

## 3.10 Git Worktrees para Aislamiento de Tareas
- **Definición:** Uso de `git worktree` para asignar a los workers copias de trabajo desacopladas del árbol principal de trabajo.
- **Estructura y Ciclo de Vida:**
  ```text
  Directorio Raíz: .autopilot-worktrees/task-<ID>/
  Flujo:
    git worktree add (.autopilot-worktrees/task-001)
         ↓
    Worker implementa y ejecuta tests en aislamiento
         ↓
    Reviewer audita diff resultante
         ↓
    Supervisor acepta / rechaza en Completion Gate
         ↓
    Merge / Cherry-pick controlado al árbol principal
         ↓
    git worktree remove --force (.autopilot-worktrees/task-001)
  ```
- Queda prohibido el merge automático hacia `master` o `main` sin validación completa del Completion Gate.

## 3.11 Web Dashboard
- **Definición:** Servidor web ligero de observabilidad que proporciona una interfaz visual con el estado de tareas, logs, bots activos y rutinas de Cron.
- **Principio de Desacoplamiento:** El Web Dashboard es un componente meramente observacional y administrativo. El Runner, el Watchdog y las suites de prueba deben poder ejecutarse al 100% en entornos headless sin que el Dashboard esté activo.

## 3.12 Gateway Multiplataforma
- **Definición:** Interfaz de comunicación con plataformas de mensajería (Telegram, Discord, Slack) para telemetría remota.
- **Política de Fases:**
  - **Fase Inicial:** Exclusivamente **notificaciones salientes** unidireccionales (`RUN COMPLETED`, `RUN FAILED`, `BLOCKED_REQUIRES_HUMAN`, `STALLED`).
  - **Fase Avanzada (si se autoriza):** Recepción de órdenes bajo autenticación criptográfica estricta, filtrado por `Security Guard` y verificación obligatoria contra `RUN-CONTRACT`.

## 3.13 Extracción Estructurada de Documentos
- **Definición:** Capacidades para convertir y extraer texto a partir de especificaciones de proyecto en formatos no planos.
- **Formatos Soportados:** DOCX, XLSX, PPTX, PDF, RTF, ODF, EPUB, legacy Office.
- **Categorización de Dependencias:**
  - *Nativas:* Formatos soportados directamente por utilidades del sistema o parsing de texto simple.
  - *Dependencias Opcionales:* Librerías Python como `openpyxl`, `mammoth`, `pypdf`, etc. Estas dependencias **no se instalan** en esta fase documental; se evaluarán y auditarán durante la Macrofase 7A.

## 3.14 Actualización Automática Controlada
- **Definición:** Procedimiento riguroso para actualizar Hermes Agent sin exponer el entorno de producción a regresiones o incompatibilidades.
- **Pipeline de Actualización Segura:**
  ```text
  DETECT UPDATE AVAILABLE
            ↓
  Download Candidate a Sandbox / Entorno Aislado
            ↓
  Verificar Origen, Versión, Hash SHA-256
            ↓
  Backup Completo de la Versión Productiva
            ↓
  Ejecutar Smoke Tests & Regression Suite en Canary
            ↓
  ¿Todos los Tests PASS?
   ├─ SÍ → Promover candidato a Producción & Actualizar VERSIONS.lock
   └─ NO → Rollback Inmediato & Registrar Incidencia
  ```
- Se prohíbe terminantemente la ejecución desatendida de `hermes update` directamente sobre el entorno en producción.

## 3.15 Idempotencia y Deduplicación del Bridge ChatGPT
- **Definición:** Garantía determinista en el bridge CDP de ChatGPT de que cada solicitud se transmite a lo sumo una única vez.
- **Requisitos de Implementación:**
  - Cada solicitud debe contar con un identificador único `consultation_id`.
  - Si se reintenta una consulta con el mismo identificador, el bridge debe retornar inmediatamente `ALREADY_SENT` o recuperar la respuesta existente sin pulsar "Send" nuevamente.
  - El bridge debe registrar `user_turns_before` y `user_turns_after`, requiriendo un incremento estricto de **exactamente +1** en turnos del usuario y **exactamente +1** en turnos del asistente.

---

# 4. Matriz de Aislamiento y Dependencias

| CAPACIDAD | IMPACTO EN INFERENCE LOCK | IMPACTO EN FILESYSTEM | RIESGO DE RED | REQUISITO DE AUDITORÍA |
|:---|:---:|:---:|:---:|:---:|
| **Cron / Routines** | Nulo (delegado) | Bajo (logs) | Nulo | Verificación de alcance de tareas |
| **Jobs sin Agente** | Nulo (0 inferencias) | Medio (housekeeping) | Nulo | Allowlist de scripts |
| **Skills** | Nulo (contextual) | Bajo (solo lectura) | Nulo | Revisión de no alteración de seguridad |
| **Memoria Persistente** | Nulo (archivos texto) | Bajo (`~/.hermes/`) | Nulo | Sanitización de secretos `[REDACTED]` |
| **Servidores MCP** | Nulo (herramientas) | Según scope | Según servidor | Filtrado de comandos y sandboxing |
| **Plugins / Tools** | Nulo | Según herramienta | Según plugin | Análisis estático de código |
| **Browser Nativo** | Nulo | Bajo (capturas/temp) | Alto | Domain allowlist y sandboxing |
| **Bot Mode** | Alto (requiere Lock) | Medio | Nulo | Serialización estricta bajo Mutex |
| **Subagentes** | Alto (requiere Lock) | Medio | Nulo | Límite estricto de recursión y herencia |
| **Git Worktrees** | Nulo | Alto (carpetas clonadas)| Nulo | Limpieza garantizada post-tarea |
| **Web Dashboard** | Nulo | Bajo | Bajo (puerto local)| Binding a 127.0.0.1 exclusivamente |
| **Gateway** | Nulo | Bajo | Medio (outbound) | Sanitización de mensajes y token TLS |
| **Doc Extraction** | Nulo | Medio (lectura) | Nulo | Validación contra exploits de parsers |
| **Auto-Update** | Nulo | Alto (binarios/libs) | Alto (repos) | Verificación de firmas y hash lock |
| **ChatGPT Idempotency**| Nulo | Bajo (registro sesiones)| Medio | Domain lock `chatgpt.com` invariable |

---

# 5. Criterio de Transición a Producción (Macrofase 7A)

Para que cualquier capacidad de este catálogo pase del estado actual (`ENABLED: NO`, `TESTED: NO`, `PRODUCTION_READY: NO`) al estado operacional (`PASS` / `PRODUCTION_READY: SÍ`), deberá completar secuencialmente durante su correspondiente subfase de la Macrofase 7A:

1. **FUNCTIONAL TEST:** Demostración de funcionamiento de la capacidad en un caso de uso representativo.
2. **SECURITY TEST:** Demostración de contención de privilegios, rechazo de inputs maliciosos o confinamiento a límites autorizados.
3. **FAILURE TEST:** Verificación del comportamiento ante fallos, timeouts o indisponibilidad del servicio subyacente.
4. **CLEANUP TEST:** Comprobación de que tras finalizar la tarea no quedan procesos huérfanos, locks tomados ni archivos temporales basura.
5. **INTEGRATION TEST:** Demostración de interoperabilidad armoniosa con el Supervisor, el Inference Lock y el sistema `.autopilot/`.
