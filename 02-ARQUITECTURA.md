# 02 — Arquitectura técnica
## Proyecto: Desarrollador Autónomo

**Versión:** 2.0  
**Estado:** BORRADOR PARA APROBACIÓN  
**Arquitectura base:** Hermes Agent + Qwen Code CLI + Qwen local mediante llama.cpp

---

# 1. Objetivo de esta arquitectura

Definir una arquitectura robusta para un trabajador de programación autónomo local capaz de:

- recibir un proyecto y un objetivo;
- investigar;
- programar;
- ejecutar comandos;
- probar;
- autocorregirse;
- consultar ChatGPT;
- continuar entre sesiones;
- evitar loops infinitos;
- terminar de forma verificable;
- funcionar durante horas sin intervención humana constante.

La arquitectura debe priorizar:

1. continuidad;
2. seguridad;
3. verificabilidad;
4. recuperación;
5. simplicidad operativa.

---

# 2. Arquitectura lógica general

```text
┌─────────────────────────────────────────────────────────────┐
│                         USUARIO                             │
│  Selecciona proyecto + objetivo + aprobación inicial       │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                   HERMES SUPERVISOR                         │
│               Orquestación y Gobernanza                     │
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
               ▼                               ▼
┌─────────────────────────────┐ ┌─────────────────────────────┐
│        QWEN CODE            │ │       HERMES REVIEWER       │
│      Coding Worker          │ │    Auditor Independiente    │
│  - edición / terminal       │ │  - verificación de diffs    │
│  - tests / builds / git     │ │  - criterios de aceptación  │
└──────────────┬──────────────┘ └──────────────┬──────────────┘
               │                               │
               │ [Serializado vía Inference Lock]
               ▼                               ▼
┌─────────────────────────────────────────────────────────────┐
│                        LLAMA.CPP                            │
│  Modelo único local: Qwen3.6-35B-A3B Q4_K_M (64K context)    │
│  parallel = 1 | host: 127.0.0.1:8080 | alias: qwen36        │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                      PROYECTO REAL                          │
│  Código | Git | tests | build | artefactos | .autopilot/    │
└─────────────────────────────────────────────────────────────┘
```

El sistema opera mediante la interacción coordinada de dos capas arquitectónicas desacopladas:

### 2.1 HERMES CAPABILITY LAYER
Conjunto de capacidades nativas que potencian la cognición, investigación y extensibilidad de Hermes:
- **Native Browser:** Navegación e inspección técnica web autónoma.
- **Web Search:** Búsqueda técnica externa en fuentes allowlisted.
- **ChatGPT Consultant:** Asesoría externa supervisada con domain-lock estricto.
- **Skills Reutilizables:** Memoria procedimental (SOPs operativos estandarizados).
- **Memoria Persistente (Nivel 2):** Retención semántica de contexto, preferencias y lecciones aprendidas.
- **Servidores MCP:** Integración modular de herramientas bajo principio de mínima superficie.
- **Plugins y Custom Tools:** Extensiones de herramientas en runtime.
- **Cron y No-Agent Jobs:** Disparadores periódicos y rutinas de mantenimiento sin inferencias.
- **Extracción Documental:** Ingesta estructurada de especificaciones (DOCX, XLSX, PDF, etc.).
- **Gateway Multiplataforma:** Notificaciones seguras hacia mensajería externa.
- **Web Dashboard:** Interfaz de observabilidad y estado de tareas (no crítica).
- **Bot Mode y Subagentes:** Especialización de roles (Supervisor, Reviewer, Researcher) y descomposición jerárquica.
- **Git Worktrees:** Espacios de trabajo físicos aislados para workers.
- **Auto-Update Controlado:** Pipeline de actualización con canary y rollback.

### 2.2 DETERMINISTIC CONTROL LAYER (Capa Autoritativa)
Capa determinista de gobernanza, ciclo de vida, contención y persistencia objetiva:
- **RUN-CONTRACT.yaml:** Contrato inmutable de alcance, políticas y límites de la ejecución.
- **STATE.json y EVENTS.jsonl:** Estado operativo canónico y log monotónico auditable.
- **Checkpoints Inmutables:** Snapshots reproducibles de estado, Git y artefactos.
- **Security Guard:** Control perimetral de rutas (Path Guard), comandos (Command Guard) y secretos.
- **Progress Guard:** Motor anti-loop, normalización de firmas de error y fingerprints de progreso.
- **Inference Lock:** Primitiva de exclusión mutua cross-process que garantiza `--parallel 1`.
- **Runner de Ciclo de Vida:** Control de procesos padre, timeouts y orquestación externa a los LLM.
- **Watchdog de Procesos:** Monitor de heartbeat, fallos de servicio y recuperación limitada.
- **Cleanup Garantizado:** Destructor tipo `finally` que garantiza ausencia de procesos o locks huérfanos.
- **Completion Gate:** Barrera determinista de salida basada en tests, build, diffs y criterios reales.

---

# 3. Componentes

## 3.1 Night Supervisor / Runner

Componente determinista externo a los LLM.

Es el componente que inicia, vigila y finaliza toda la ejecución.

No debe depender del razonamiento de Hermes para tareas operativas críticas.

### Responsabilidades

- cargar configuración;
- validar proyecto;
- crear `run_id`;
- preparar `.autopilot/`;
- iniciar llama.cpp;
- esperar health check;
- comprobar puerto;
- iniciar Hermes;
- controlar timeout global;
- controlar heartbeat;
- comprobar procesos;
- gestionar reinicios;
- gestionar locks;
- recopilar logs;
- ejecutar cleanup;
- generar estado final.

### Regla

El Runner manda sobre el ciclo de vida de procesos.

Hermes manda sobre la estrategia de trabajo.

---

## 3.2 Hermes Agent

Hermes es el supervisor inteligente.

### Responsabilidades

- recibir objetivo;
- ejecutar preflight;
- crear/validar plan;
- leer estado persistente;
- decidir siguiente tarea;
- investigar web;
- evaluar resultados;
- detectar bloqueo;
- consultar ChatGPT;
- delegar a Qwen Code;
- decidir reintento/cambio de estrategia;
- decidir si pasar a Completion Gate.

### Hermes NO debe

- editar simultáneamente los mismos archivos que Qwen Code;
- saltarse el contrato de ejecución;
- ejecutar acciones destructivas fuera de política;
- marcar `COMPLETED` sin evidencia.

---

## 3.3 Qwen Code CLI

Qwen Code es el worker especializado en programación.

### Entrada mínima de cada tarea

Debe recibir:

- `run_id`;
- ruta de proyecto;
- task_id;
- objetivo concreto;
- criterios de aceptación;
- restricciones;
- estado relevante;
- archivos relevantes si aplica;
- timeout;
- formato esperado de salida.

### Salida mínima

Debe devolver:

- estado;
- resumen;
- archivos modificados;
- comandos ejecutados;
- tests ejecutados;
- build;
- errores;
- evidencia;
- siguiente recomendación;
- motivo si quedó bloqueado.

---

## 3.4 llama.cpp

Servidor local único para Hermes y Qwen Code.

### Configuración base

```text
C:\AI\llama.cpp\llama-server.exe

--ctx-size 65536
--parallel 1
--cpu-moe
--n-gpu-layers 99
--flash-attn on
--cache-type-k q8_0
--cache-type-v q8_0
--jinja
```

### Endpoint

```text
http://127.0.0.1:8080
```

### Regla de ciclo de vida

Durante una ejecución autónoma:

- se inicia una vez;
- permanece activo;
- no se reinicia entre llamadas normales;
- se cierra al finalizar;
- se cierra también ante fallo irreversible, timeout o abort.

---

# 4. Restricción clave: `--parallel 1`

Sólo puede existir una inferencia local activa a la vez.

Por lo tanto:

```text
NO:
Hermes inferencia  ─────┐
                        ├── simultáneo
Qwen Code inferencia ───┘
```

Debe existir serialización.

```text
Hermes piensa
   ↓
libera turno de modelo
   ↓
Qwen Code trabaja
   ↓
libera turno de modelo
   ↓
Hermes evalúa
```

---

# 5. Model Gateway / Inference Lock

Debe existir una capa de exclusión mutua para impedir dos inferencias simultáneas.

Nombre provisional:

```text
Model Gateway
```

o bien:

```text
Inference Lock
```

### Función

Antes de una llamada al modelo:

```text
solicitar lock
   ↓
¿libre?
   ├─ sí -> usar modelo
   └─ no -> esperar
```

Después:

```text
termina inferencia
   ↓
liberar lock
```

### Requisito

El lock debe recuperarse si un proceso muere.

No debe quedar bloqueado para siempre.

---

# 6. Concurrencia permitida

Aunque sólo exista una inferencia local:

sí pueden ejecutarse simultáneamente tareas externas.

Ejemplos:

```text
Hermes:
web search
         \
          \ simultáneo
           \
Qwen Code:
npm test
```

También:

```text
Hermes:
analiza evidencia ya disponible

Qwen Code:
build externo
```

Siempre que ninguna tarea necesite llamar al Qwen local al mismo tiempo.

---

# 7. Workspace principal

El proyecto de infraestructura tendrá su propia carpeta:

```text
Desarrollador autonomo/
```

Dentro debe existir como mínimo:

```text
Desarrollador autonomo/
│
├── 00-README.md
├── 01-OBJETIVOS-Y-REQUISITOS.md
├── 02-ARQUITECTURA.md
├── 03-MEMORIA-Y-CONTINUIDAD.md
├── 04-AUTONOMIA-Y-SEGURIDAD.md
├── 05-INSTALACION-Y-CONFIGURACION.md
├── 06-PRUEBAS-Y-CRITERIOS-DE-EXITO.md
├── 07-ROADMAP.md
├── AGENTS.md
│
├── config/
├── scripts/
├── runner/
├── tools/
├── tests/
├── sandbox/
├── backups/
└── docs/
```

Antigravity puede crear nuevas subcarpetas justificadas.

---

# 8. Estructura por proyecto gestionado

Cada proyecto real debe contener o recibir:

```text
PROJECT_ROOT/
│
├── QWEN.md
├── .autopilot/
│   ├── RUN-CONTRACT.yaml
│   ├── STATE.json
│   ├── STATE.md
│   ├── EVENTS.jsonl
│   ├── LOCK.json
│   ├── logs/
│   │   ├── runner/
│   │   ├── hermes/
│   │   ├── qwen/
│   │   ├── llama/
│   │   ├── tests/
│   │   └── builds/
│   ├── evidence/
│   │   ├── web/
│   │   ├── chatgpt/
│   │   ├── tests/
│   │   └── artifacts/
│   ├── checkpoints/
│   └── reports/
│
└── proyecto...
```

---

# 9. RUN-CONTRACT.yaml

Contrato generado después del preflight.

Debe definir:

```yaml
run_id:
project_path:
objective:
acceptance_criteria:
autonomy:
allowed_actions:
forbidden_actions:
git_policy:
network_policy:
chatgpt_policy:
timeouts:
budgets:
completion_policy:
```

Después de aprobación inicial:

`RUN-CONTRACT.yaml` es vinculante para esa ejecución.

---

# 10. Flujo de inicio

```text
1. Usuario inicia sistema
2. Runner carga configuración
3. Selecciona proyecto
4. Hermes hace preflight
5. Se genera RUN-CONTRACT
6. Usuario aprueba
7. Se crea run_id
8. Se prepara .autopilot
9. Se inicia llama-server
10. Se espera /health
11. Se inicia Hermes autónomo
12. Hermes reconstruye estado
13. Comienza ciclo 1
```

---

# 11. Flujo normal de trabajo

```text
HERMES
  |
  v
lee estado
  |
  v
elige tarea
  |
  +--> si necesita investigación
  |       |
  |       v
  |     web / docs / GitHub
  |
  v
delega a Qwen Code
  |
  v
Qwen analiza
  |
  v
modifica
  |
  v
ejecuta tests/build
  |
  v
devuelve resultado
  |
  v
Hermes evalúa
  |
  +--> FAIL -> replanificar
  |
  +--> PASS -> checkpoint
  |
  v
actualiza STATE/EVENTS
  |
  v
siguiente ciclo
```

---

# 12. Autocorrección en Qwen Code

Dentro de una misma tarea:

```text
analizar
  ↓
implementar
  ↓
ejecutar
  ↓
fallo
  ↓
diagnosticar
  ↓
corregir
  ↓
volver a probar
```

Qwen Code puede realizar varios intentos internos, pero debe respetar presupuestos.

Hermes controla un nivel superior.

---

# 13. Escalamiento de fallo

Orden recomendado:

```text
Intento 1
  ↓
Qwen corrige
  ↓
Intento 2
  ↓
cambio de enfoque
  ↓
Intento 3
  ↓
Hermes investiga web
  ↓
nuevo intento
  ↓
si sigue bloqueado
  ↓
consultar ChatGPT
  ↓
nuevo enfoque
  ↓
si no hay progreso
  ↓
STALLED
```

---

# 14. ChatGPT

## 14.1 Rol

Consultor externo asistido. No es worker de implementación ni modifica archivos directamente.

---

## 14.2 Chrome dedicado

Perfil dedicado y persistente: `data/browser/HERMES-CHATGPT`.
Reglas de confinamiento:
- una sola pestaña controlada;
- domain-lock estricto: `chatgpt.com`;
- sesión iniciada manualmente por el usuario en preflight o paso inicial;
- sin acceso a pestañas personales del usuario ni a otros dominios;
- sin credenciales almacenadas en scripts.

---

## 14.3 Herramienta `consultar_chatgpt`

Debe:
1. validar que Chrome CDP (puerto 9222) esté respondiendo;
2. verificar que la pestaña pertenezca a `chatgpt.com`;
3. sanear prompt de secretos y aplicar codificación UTF-8 pura (BOM check);
4. enviar prompt y monitorear extracción de respuesta en streaming;
5. guardar evidencia en `.autopilot/evidence/chatgpt/`;
6. devolver la respuesta consultiva a Hermes para su evaluación.

---

## 14.4 Idempotencia y Deduplicación del Bridge

Toda consulta debe incluir un `consultation_id` único y determinista.
- **Garantía:** Exactamente un (1) envío físico por `consultation_id`.
- **Detección de Reintento:** Si se invoca el bridge con un identificador ya procesado o en curso, debe retornar inmediatamente `ALREADY_SENT` o entregar el resultado previo sin volver a pulsar "Send".
- **Verificación de Turnos:** El bridge debe auditar que:
  - `user_turns_after == user_turns_before + 1`
  - `assistant_turns_after == assistant_turns_before + 1`
  Garantizando que no hubo pérdida ni duplicación de contexto en el chat.

---

# 15. Web Research y Automatización de Navegación

Hermes prioriza fuentes técnicas oficiales estructuradas:
1. Documentación oficial del framework / biblioteca.
2. Repositorios oficiales y issues cerrados.
3. Especificaciones y RFCs.

### Jerarquía de Navegadores:
```text
1. Browser Nativo de Hermes      → Para búsqueda técnica, scraping headless y documentación
2. MCP Browser / Playwright      → Para pruebas dinámicas o interacción con UIs complejas
3. Hardened ChatGPT Bridge (CDP) → Confinado estrictamente a chatgpt.com
```

Toda investigación relevante se persiste en `.autopilot/evidence/web/` con fuentes y hashes.

---

# 16. Memoria y continuidad (Modelo de 3 Niveles + Skills)

La persistencia del sistema se organiza formalmente en tres niveles de memoria más memoria procedimental:

```text
┌────────────────────────────────────────────────────────────────────────┐
│             NIVEL 1 — MEMORIA OPERATIVA AUTORITATIVA                   │
│  - Filesystem y código real           - RUN-CONTRACT.yaml              │
│  - Git (status, commits, diffs)       - EVENTS.jsonl (append-only)     │
│  - Tests y builds ejecutados          - Checkpoints inmutables         │
│  - STATE.json (fuente operativa canónica)                              │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Prevalece sobre niveles superiores
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│             NIVEL 2 — MEMORIA PERSISTENTE HERMES                       │
│  - Preferencias arquitectónicas       - Decisiones reutilizables       │
│  - Lecciones aprendidas               - Patrones exitosos comprobados  │
│  * No puede declarar como verdad: estado de tests, build o archivos    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│             NIVEL 3 — MEMORIA DE SESIÓN (AUXILIAR)                     │
│  - Historial de chat                  - Razonamiento transitorio       │
│  * Se puede perder, compactar o descartar sin afectar continuidad      │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│             MEMORIA PROCEDIMENTAL (SKILLS REUTILIZABLES)               │
│  - Procedimientos operativos estandarizados (SOPs en Markdown)         │
│  - Diagnóstico de stacks, auditorías SQL, checklists de release        │
│  * Solo lectura; no pueden alterar directivas de seguridad ni contrato │
└────────────────────────────────────────────────────────────────────────┘
```

---

# 17. Recovery Protocol

Ante reinicio, nueva sesión o fallo:

```text
1. verificar proyecto
2. leer RUN-CONTRACT
3. leer STATE.json
4. leer STATE.md
5. leer QWEN.md
6. git status
7. git diff
8. comprobar tests/build relevantes
9. reconciliar inconsistencias
10. recuperar sesión si conviene
11. continuar
```

---

# 18. Gestión de sesiones

## Qwen Code

Preferencia:

```text
--continue
```

o:

```text
--resume <session>
```

mientras la sesión sea sana.

Crear sesión nueva si:

- contexto contaminado;
- compactación excesiva;
- repetición;
- cambio de etapa grande;
- inconsistencia.

---

## Hermes

Debe aprovechar:

- sesiones persistentes;
- resume;
- session search;
- memoria persistente.

Pero STATE sigue siendo fuente operativa principal.

---

# 19. Checkpoints

Un checkpoint se crea:

- al completar hito;
- antes de nueva sesión;
- antes de cambio de estrategia grande;
- antes de operación riesgosa permitida;
- antes de finalizar.

Debe incluir:

- estado;
- Git diff;
- tests;
- build;
- decisiones;
- siguiente paso.

---

# 20. Git

## Política base

Trabajar preferentemente en rama:

```text
agent/night-YYYY-MM-DD
```

o:

```text
agent/<run_id>
```

Permitido:

- status;
- diff;
- log;
- branch;
- commit local;
- checkout seguro.

Bloqueado por defecto:

- push;
- force push;
- reset destructivo;
- borrar historia.

---

# 21. Locks

Debe existir al menos:

## 21.1 Run Lock

Evita dos ejecuciones autónomas sobre el mismo proyecto.

Archivo posible:

```text
.autopilot/LOCK.json
```

Debe incluir:

- run_id;
- PID;
- timestamp;
- heartbeat;
- owner.

---

## 21.2 Inference Lock

Evita dos inferencias sobre Qwen con `parallel 1`.

Puede ser:

- mutex de Windows;
- lockfile robusto;
- servicio local;
- cola interna.

La implementación queda a Antigravity, pero debe ser recuperable tras crash.

---

# 22. Heartbeat

El Runner debe emitir heartbeat periódico.

Ejemplo:

```text
.autopilot/heartbeat.json
```

Debe incluir:

- run_id;
- timestamp;
- estado;
- ciclo;
- proceso Hermes;
- proceso Qwen;
- llama health.

Si heartbeat queda obsoleto:

- diagnosticar;
- recuperar;
- o detener.

---

# 23. Watchdog

Debe vigilar:

- llama-server;
- Hermes;
- Qwen Code worker;
- timeout;
- heartbeat;
- locks;
- crecimiento anormal;
- falta de progreso.

No debe reiniciar indiscriminadamente.

Cada reinicio debe quedar registrado.

---

# 24. Política de reinicio

## llama.cpp cae

```text
detectar
  ↓
registrar
  ↓
guardar estado si es posible
  ↓
reiniciar
  ↓
esperar health
  ↓
Recovery Protocol
```

Máximo de reinicios configurable.

---

## Qwen Code cae

```text
registrar
  ↓
revisar salida
  ↓
resume si es posible
  ↓
si no -> nueva sesión
  ↓
Recovery Protocol
```

---

## Hermes cae

```text
Runner detecta
  ↓
reinicia Hermes
  ↓
Recovery Protocol
  ↓
reanudar
```

---

# 25. Anti-loop arquitectónico

No depender sólo de que Hermes “se dé cuenta”.

El Runner debe medir:

- ciclo actual;
- error signature;
- hash/diff de cambios;
- tests;
- build;
- progreso;
- timestamps.

Si:

```text
mismo error
+
mismo diff
+
mismo estado
```

durante N ciclos:

```text
NO_PROGRESS
```

---

# 26. Progress Score

Puede existir un indicador simple, no necesariamente IA.

Ejemplo:

```text
0-100
```

Basado en:

- hitos completados;
- criterios cumplidos;
- tests;
- build;
- pendientes.

No debe usarse solo para decidir COMPLETED.

---

# 27. Completion Gate

Flujo:

```text
Hermes cree que terminó
       ↓
VERIFYING
       ↓
tests
       ↓
build
       ↓
artefactos
       ↓
criterios
       ↓
Git diff
       ↓
pendientes
       ↓
consistencia STATE
       ↓
PASS?
  ├─ no -> RUNNING
  └─ sí -> COMPLETED
```

---

# 28. Cleanup

Debe ejecutarse siempre.

Orden recomendado:

```text
1. detener workers
2. cerrar sesiones auxiliares
3. guardar logs
4. actualizar STATE
5. generar reporte
6. detener llama-server
7. verificar ausencia del proceso
8. liberar locks
9. marcar run finalizado
```

Debe existir comportamiento equivalente a `finally`.

---

# 29. Estados globales

```text
PREFLIGHT
READY
STARTING
RUNNING
RECOVERING
VERIFYING
STALLED
BLOCKED_REQUIRES_HUMAN
FAILED
COMPLETED
CLEANING_UP
STOPPED
```

---

# 30. Puertos y servicios

Configuración inicial:

| Servicio | Dirección |
|---|---|
| llama.cpp | `127.0.0.1:8080` |
| otros servicios internos | asignación dinámica o documentada |

Regla:

No exponer `llama.cpp` públicamente.

Host:

```text
127.0.0.1
```

---

# 31. Seguridad de red

Por defecto:

- llama local solamente;
- no abrir firewall;
- no publicar puertos;
- no túneles externos;
- no credenciales en logs.

---

# 32. Configuración central

Debe existir un archivo único de configuración global del sistema.

Nombre provisional:

```text
config/system.yaml
```

Debe contener:

```yaml
llama:
  executable:
  model:
  host:
  port:
  ctx_size:
  parallel:
  args:

hermes:
  executable:
  profile:

qwen_code:
  executable:
  profile:

runner:
  timeouts:
  retries:
  heartbeat:

security:
  workspace_policy:
  blocked_commands:

chatgpt:
  enabled:
  chrome_profile:
  allowed_domain:
```

Evitar valores duplicados en múltiples scripts.

---

# 33. Gestión de secretos

Nunca almacenar en:

- STATE;
- EVENTS;
- logs;
- prompts persistidos;
- Git.

Si algún secreto es necesario:

- referencia indirecta;
- variable de entorno;
- almacén seguro compatible;
- acceso mínimo.

---

# 34. Backups

Antes de modificar configuración existente:

```text
backups/
  YYYY-MM-DD-HHMMSS/
```

Debe incluir copia de archivos afectados y manifiesto.

---

# 35. Launchers legacy

No usar como fuente oficial:

- `Iniciar Qwen - Goose 16K.bat`
- `Iniciar Qwen.bat`
- `GOOSE-TEST\goose-night.ps1`

Pueden conservarse como legacy.

---

# 36. Inicio único

Nombre provisional:

```text
INICIAR-DESARROLLADOR-AUTONOMO.bat
```

Su única función visible es iniciar el Runner.

No debe contener lógica compleja.

---

# 37. Web Dashboard y Observabilidad

El Web Dashboard es una interfaz web ligera de monitorización local provista por Hermes.
- **Propósito:** Visualizar sesiones, bots activos, cron jobs, logs en tiempo real y métricas de salud.
- **Desacoplamiento Operacional:** El Runner y el sistema de ejecución autónoma nocturna son completamente independientes del Dashboard. El Dashboard es una herramienta de observabilidad humana; **si el dashboard se cierra, falla o no se inicia, el Runner continúa su ejecución sin interrupción.**
- **Red:** Confinado estrictamente a `127.0.0.1` en puerto local no conflictivo.

---

# 38. Gateway Multiplataforma

Capacidad de Hermes para integrarse con canales de mensajería externos (Telegram, Discord, Slack, etc.).
- **Fase Inicial (Notificaciones):** Transmisión unidireccional y saliente de eventos críticos:
  - `RUN COMPLETED` (con resumen y métricas)
  - `RUN FAILED` (con causa raíz normalizada)
  - `BLOCKED_REQUIRES_HUMAN` (solicitud de desbloqueo justificada)
  - `STALLED` (detección de ausencia de progreso)
- **Fase Avanzada (Comandos Remotos - Restringida):** Si se autoriza la recepción de órdenes, cualquier mensaje recibido desde el Gateway es tratado como **entrada no confiable (`UNTRUSTED`)**, debiendo validarse criptográficamente, pasar por el `Security Guard` y ajustarse estrictamente a las restricciones de `RUN-CONTRACT.yaml`. Quedan terminantemente prohibidas acciones destructivas remotas.

---

# 39. Bot Mode y Subagentes Jerárquicos

Configuración multi-agente especializada para la segregación de funciones:
- **Roles:**
  - `HERMES SUPERVISOR`: Orquesta el ciclo global, evalúa contratos y aprueba o rechaza entregables.
  - `QWEN CODE`: Coding Worker principal especializado en edición, testing y ejecución de comandos.
  - `HERMES REVIEWER`: Auditor independiente que examina diffs de Git y verifica que los criterios de aceptación se cumplan objetivamente antes de la aprobación.
  - `HERMES RESEARCHER`: Investigador auxiliar dedicado a la documentación técnica.
- **Serialización Absoluta:** Todos los roles comparten la única instancia local `qwen36` (`--parallel 1`). **En ningún momento se ejecutan inferencias simultáneas.** El `Inference Lock` encola y serializa cada turno.
- **Subagentes:** Hermes puede instanciar subagentes efímeros para tareas puntuales. Los subagentes heredan permisos restringidos y no pueden alterar contratos, políticas de seguridad ni realizar acciones fuera de scope.

---

# 40. Git Worktrees Isolados

Para tareas complejas o workers paralelos que requieran aislamiento del espacio de trabajo principal:
- **Ubicación:** `.autopilot-worktrees/task-<ID>/`
- **Ciclo de Vida:**
  ```text
  1. git worktree add .autopilot-worktrees/task-001 -b agent/task-001
  2. Worker opera, edita y corre tests en el worktree aislado
  3. Reviewer examina el diff generado
  4. Supervisor evalúa en Completion Gate
  5. Merge o cherry-pick controlado hacia el árbol de trabajo principal
  6. git worktree remove --force .autopilot-worktrees/task-001
  ```
- **Regla:** Ningún worktree se fusiona automáticamente al branch principal sin superar la suite de tests y el Completion Gate.

---

# 41. Servidores MCP y Plugins

- **Mínima Superficie:** No se incorporan servidores MCP que expongan decenas de herramientas genéricas. Se exige un allowlist explícito por servidor.
- **Gobernanza MCP:** Cada servidor MCP conectado cuenta con scope de filesystem delimitado, timeouts estrictos y health check periódico.
- **Plugins Custom:** Se adoptan capacidades nativas de Hermes preferentemente ("Prefer Native When Verified"). Se recurre a plugins de herramientas custom únicamente cuando se requieran salvaguardas deterministas no provistas nativamente.

---

# 42. Cron y Tareas sin Agente (No-Agent Jobs)

- **Cron / Routines:** Planificador temporal subordinado al Runner para activar rutinas periódicas de supervisión.
- **Jobs sin Agente (Deterministic No-Agent Jobs):** Tareas automatizadas que no requieren razonamiento de lenguaje:
  - Limpieza de temporales y logs antiguos;
  - Auditoría de hashes SHA-256 e integridad de backups;
  - Health checks de puertos y servicios;
  - Backups de `STATE.json`.
  - **Ventaja crítica:** **0 inferencias LLM**, 0 consumo de tokens y nulo bloqueo del Inference Lock.

---

# 43. Extracción Estructurada de Documentos

Soporte estructurado para ingerir especificaciones en formatos no planos (DOCX, XLSX, PPTX, PDF, RTF, ODF, EPUB, legacy Office):
- *Nativo:* Parsing de formatos soportados directamente por el sistema o convertidores a texto plano.
- *Dependencias Opcionales:* Librerías Python (`openpyxl`, `mammoth`, `pypdf`). No se instalan ciegamente; su incorporación requiere auditoría previa en Macrofase 7A.

---

# 44. Pipeline de Auto-Update Seguro

Proceso riguroso para actualizar Hermes Agent sin riesgo de romper el entorno productivo:
```text
UPDATE AVAILABLE
      ↓
Download en Sandbox / Directorio Canary
      ↓
Verificación de Hash SHA-256 y Origen
      ↓
Backup Completo del Entorno de Producción
      ↓
Smoke Tests y Regression Suite en Canary
      ↓
¿PASS? ── SÍ ──> Promover a Producción y actualizar VERSIONS.lock
   │
   └── NO ──> Rollback Inmediato y Registro de Incidencia
```
Se prohíbe terminantemente la ejecución desatendida de `hermes update` directamente sobre producción.

---

# 45. Secuencia de una noche típica

```text
23:55 usuario abre sistema
00:00 preflight y contrato
00:05 usuario aprueba
00:06 llama-server inicia y health responde
00:07 Hermes reconstruye estado desde .autopilot
00:08 ciclo 1
00:20 Qwen Code implementa en worktree aislado
00:35 tests fallan
00:40 Qwen corrige
01:10 tests PASS, checkpoint
01:11 Hermes Reviewer audita diff y aprueba
01:12 merge a rama principal, ciclo 2
02:30 problema externo (API / lib)
02:35 Hermes investiga web
02:50 nuevo intento
03:20 bloqueo persistente
03:25 Hermes consulta ChatGPT con consultation_id único
03:30 asesoría recibida, nueva estrategia
04:15 checkpoint
04:16 nueva sesión limpia de Qwen
06:30 Completion Gate verifica tests, build y criterios
06:45 PASS
06:50 informe final generado
06:51 cleanup de procesos, worktrees y locks
06:52 llama-server cerrado
```

---

# 46. Responsabilidades resumidas

| Componente | Capa | Responsabilidad principal |
|---|---|---|
| Usuario | Humana | Objetivo, preflight y aprobación inicial |
| Runner | Determinista | Ciclo de vida de procesos, timeouts y orquestación |
| Hermes Supervisor | Hermes Capability | Estrategia, contratos y supervisión |
| Qwen Code | Worker | Implementación, refactorización y tests |
| Hermes Reviewer | Hermes Capability | Auditoría independiente de diffs |
| llama.cpp (qwen36) | Inferencia Local | Modelo compartido local serializado (`parallel = 1`) |
| Inference Lock | Determinista | Exclusión mutua estricta de inferencia (.NET Mutex) |
| Git & Worktrees | Determinista | Evidencia, control de versiones y aislamiento |
| STATE & EVENTS | Determinista | Continuidad operacional y auditoría append-only |
| Watchdog | Determinista | Monitor de fallos, heartbeat y recuperación de procesos |
| Completion Gate | Determinista | Validación multi-criterio previa a COMPLETED |
| Cleanup | Determinista | Terminación garantizada tipo `finally` sin huérfanos |

---

# 47. Criterio de arquitectura correcta

La arquitectura se considera correctamente implementada si:
- Hermes y Qwen Code comparten el mismo Qwen local a 64K context;
- Nunca ocurren dos inferencias simultáneas (Inference Lock serializa 100%);
- Una caída de proceso no obliga a recomenzar (reconstrucción desde Git/STATE);
- El sistema puede operar durante horas sin intervención tras aprobación inicial;
- Las consultas a ChatGPT son idempotentes y deducadas;
- Se previene el consumo infinito mediante motor anti-loop y guardrails deterministas;
- La finalización (`COMPLETED`) exige verificación objetiva completa;
- El cleanup libera todos los procesos y locks al terminar.

---

# 48. Regla para Antigravity

Antigravity debe implementar esta arquitectura de forma incremental por fases.
Puede proponer mejoras, pero:
- no debe sustituir Hermes ni Qwen Code;
- no debe cambiar el modelo local `qwen36`;
- no debe reducir el contexto de 64K sin evidencia;
- no debe eliminar las capas de estado ni la jerarquía de verdad;
- no debe retirar el Runner ni el Watchdog deterministas;
- no debe introducir inferencia concurrente bajo `parallel = 1`.

Cualquier cambio a la arquitectura base debe documentarse y someterse a aprobación previa.
