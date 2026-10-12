# 06 — Pruebas y criterios de éxito
## Proyecto: Desarrollador Autónomo

**Versión:** 2.0  
**Estado:** APROBADO / FROZEN PARA IMPLEMENTACIÓN DE MACROFASE 7A  
**Arquitectura base:** Hermes Agent + Qwen Code CLI + Qwen local mediante llama.cpp

---

# 1. Objetivo

Definir cómo se demuestra que el sistema funciona realmente.

Regla principal:

> **No se acepta una afirmación del agente como evidencia suficiente.**

Cada capacidad crítica debe validarse mediante:

- comando;
- test;
- log;
- archivo;
- estado;
- artefacto;
- captura;
- respuesta verificable;
- comparación antes/después.

---

# 2. Principio de evidencia

Cada prueba debe registrar:

```text
TEST ID
nombre
objetivo
precondiciones
pasos
resultado esperado
resultado real
PASS / FAIL
evidencia
timestamp
```

---

# 3. Estados de prueba

Sólo se permiten:

```text
NOT_RUN
RUNNING
PASS
FAIL
BLOCKED
SKIPPED
```

`SKIPPED` requiere justificación.

---

# 4. Carpeta de evidencia

Guardar resultados en:

```text
evidence/
  installation/
  llama/
  qwen-code/
  hermes/
  delegation/
  memory/
  recovery/
  web/
  chatgpt/
  security/
  runner/
  e2e/
```

---

# 5. Test manifest

Crear:

```text
tests/TEST-MANIFEST.yaml
```

Debe listar todas las pruebas obligatorias.

Ejemplo:

```yaml
tests:
  - id: T-LLAMA-001
    name: "llama health"
    required: true

  - id: T-QWEN-001
    name: "Qwen Code modifica y prueba"
    required: true
```

---

# 6. Resultado global

Crear:

```text
reports/TEST-RESULTS.md
```

y opcionalmente:

```text
reports/TEST-RESULTS.json
```

con resumen:

```text
TOTAL
PASS
FAIL
BLOCKED
SKIPPED
```

---

# 7. Gate de instalación

La instalación no pasa a fase siguiente si falla una prueba obligatoria de la fase anterior.

---

# 8. Pruebas de llama.cpp

## T-LLAMA-001 — Binario existente

Objetivo:

comprobar que existe:

```text
C:\AI\llama.cpp\llama-server.exe
```

Resultado esperado:

```text
PASS
```

---

## T-LLAMA-002 — Modelo existente

Comprobar que existe el GGUF configurado.

Resultado esperado:

```text
PASS
```

No descargar de nuevo.

---

## T-LLAMA-003 — Arranque

Iniciar con configuración oficial.

Esperado:

- proceso activo;
- puerto 8080;
- sin crash inmediato.

---

## T-LLAMA-004 — Health

Consultar health endpoint.

Esperado:

```text
READY
```

o respuesta equivalente de la versión instalada.

---

## T-LLAMA-005 — Alias

Comprobar:

```text
qwen36
```

---

## T-LLAMA-006 — Contexto

Verificar en log/configuración:

```text
n_ctx_slot = 65536
```

o evidencia equivalente.

---

## T-LLAMA-007 — Parallel

Verificar:

```text
parallel = 1
```

---

## T-LLAMA-008 — Inferencia simple

Enviar prompt pequeño.

Esperado:

- respuesta válida;
- sin error HTTP;
- sin crash.

---

## T-LLAMA-009 — Inferencia larga

Usar prueba validada de contexto alto.

Objetivo:

confirmar operación próxima a 64K.

No es necesario repetirla en cada arranque si ya existe evidencia reciente y la versión/configuración no cambió.

---

## T-LLAMA-010 — Cleanup

Detener servidor.

Esperado:

- proceso desaparece;
- puerto queda libre;
- RAM/VRAM se liberan razonablemente.

---

# 9. Pruebas Qwen Code CLI

## T-QWEN-001 — Instalación

Comando disponible.

Guardar versión.

---

## T-QWEN-002 — Modelo local

Qwen Code debe usar llama.cpp local.

No API externa accidental.

Evidencia:

- configuración;
- logs;
- endpoint.

---

## T-QWEN-003 — Lectura de proyecto

Sandbox:

Qwen Code debe leer archivos existentes y describir correctamente su estructura.

---

## T-QWEN-004 — Edición

Debe modificar un archivo del sandbox.

Esperado:

- cambio real;
- Git diff visible.

---

## T-QWEN-005 — Comando

Debe ejecutar un comando del proyecto.

---

## T-QWEN-006 — Test

Debe ejecutar un test.

---

## T-QWEN-007 — Autocorrección

Preparar bug intencional.

Flujo esperado:

```text
test FAIL
↓
diagnóstico
↓
cambio
↓
test PASS
```

Sin intervención humana.

---

## T-QWEN-008 — Build

Debe ejecutar build en sandbox.

---

## T-QWEN-009 — Headless

Debe poder ser invocado por Runner/Hermes sin interacción manual.

---

## T-QWEN-010 — Output capturable

El wrapper debe recuperar resultado estructurado.

---

## T-QWEN-011 — Timeout

Crear tarea larga artificial.

Esperado:

- timeout controlado;
- worker detenido;
- estado registrado.

---

## T-QWEN-012 — Resume

Interrumpir sesión y reanudar.

Esperado:

- continúa desde estado previo;
- no recomienza desde cero.

---

## T-QWEN-013 — Nueva sesión

Crear sesión limpia.

Esperado:

- lee STATE;
- continúa correctamente.

---

# 10. Pruebas Hermes

## T-HERMES-001 — Instalación

Guardar versión.

---

## T-HERMES-002 — Modelo local

Hermes usa Qwen local.

Evidencia:

- endpoint;
- logs/config.

---

## T-HERMES-003 — Prompt simple

Hermes responde correctamente.

---

## T-HERMES-004 — Tool use

Hermes puede invocar una herramienta habilitada.

---

## T-HERMES-005 — Estado

Hermes puede leer:

```text
STATE.json
STATE.md
RUN-CONTRACT.yaml
```

---

## T-HERMES-006 — Planificación

Dado un objetivo simple:

debe producir tareas verificables.

---

## T-HERMES-007 — Web

Debe ejecutar investigación web y guardar evidencia.

---

## T-HERMES-008 — Sesión

Debe poder mantener/recuperar sesión.

---

## T-HERMES-009 — Recovery

Nueva sesión Hermes debe reconstruir el run desde estado persistido.

---

# 11. Pruebas de delegación

## T-DELEG-001 — Hermes llama Qwen Code

Hermes debe delegar una tarea real.

---

## T-DELEG-002 — Entrada estructurada

Verificar que Qwen Code recibe:

- project;
- task_id;
- objetivo;
- criterios;
- restricciones;
- timeout.

---

## T-DELEG-003 — Salida estructurada

Verificar:

- status;
- summary;
- files_changed;
- tests;
- errors;
- evidence.

---

## T-DELEG-004 — Resultado real

Hermes debe comprobar que los archivos realmente cambiaron.

No confiar sólo en la respuesta de Qwen Code.

---

## T-DELEG-005 — Evaluación

Hermes debe:

- aceptar;
- pedir corrección;
- o cambiar estrategia;

según evidencia.

---

# 12. Pruebas de Inference Lock

## T-LOCK-001 — Exclusión

Intentar dos inferencias simultáneas.

Esperado:

```text
una entra
otra espera
```

Nunca dos inferencias concurrentes.

---

## T-LOCK-002 — Liberación

Después de la inferencia:

el lock se libera.

---

## T-LOCK-003 — Crash

Matar proceso dueño del lock.

Esperado:

- lock obsoleto detectado;
- recuperación segura;
- no bloqueo permanente.

---

## T-LOCK-004 — Timeout

Un lock demasiado largo debe generar diagnóstico.

No liberar ciegamente sin comprobar ownership.

---

# 13. Pruebas de STATE

## T-STATE-001 — Creación

Al iniciar run:

```text
STATE.json
STATE.md
```

deben existir.

---

## T-STATE-002 — JSON válido

Debe parsearse correctamente.

---

## T-STATE-003 — Schema

Debe incluir:

```text
schema_version
run_id
status
cycle
objective
active_task
next_action
```

---

## T-STATE-004 — Actualización

Después de tarea:

STATE refleja resultado real.

---

## T-STATE-005 — Atomic write

Simular interrupción durante escritura.

Esperado:

no dejar STATE corrupto.

---

## T-STATE-006 — Previous state

Debe existir mecanismo de recuperación desde snapshot/anterior.

---

# 14. Pruebas EVENTS

## T-EVENTS-001

Registrar evento por línea JSON.

---

## T-EVENTS-002

Verificar cronología.

---

## T-EVENTS-003

Registrar:

```text
TASK
COMMAND
TEST
ERROR
CHECKPOINT
```

---

## T-EVENTS-004

Eventos no deben contener secretos.

---

# 15. Pruebas de checkpoints

## T-CP-001

Crear checkpoint manual/automático.

---

## T-CP-002

Debe incluir:

- STATE snapshot;
- Git status;
- diff summary;
- tests;
- build;
- next action.

---

## T-CP-003

Checkpoint previo no debe sobrescribirse.

---

## T-CP-004

Recuperar desde checkpoint.

---

# 16. Pruebas de Recovery Protocol

## T-REC-001 — Qwen Code crash

Durante una tarea:

matar Qwen Code.

Esperado:

```text
detect
↓
log
↓
resume/new session
↓
reconcile
↓
continue
```

---

## T-REC-002 — llama.cpp crash

Matar llama.cpp.

Esperado:

```text
detect
↓
restart
↓
health
↓
recovery
↓
continue
```

---

## T-REC-003 — Hermes crash

Matar Hermes.

Esperado:

Runner detecta y recupera.

---

## T-REC-004 — Reinicio lógico

Simular que no existen procesos pero:

```text
STATE.status = RUNNING
```

Esperado:

detectar run incompleto.

---

## T-REC-005 — STATE atrasado

Modificar archivo después de última persistencia.

Esperado:

Git/filesystem corrigen STATE.

---

## T-REC-006 — Test desconocido

Simular crash durante test.

Esperado:

```text
UNKNOWN
```

y volver a ejecutar.

---

# 17. Pruebas de continuidad

## T-CONT-001 — Resume misma sesión

---

## T-CONT-002 — Nueva sesión Qwen

---

## T-CONT-003 — Nueva sesión Hermes

---

## T-CONT-004 — Compactación

Provocar contexto largo.

Esperado:

continuidad mediante STATE/checkpoint.

---

## T-CONT-005 — Varios ciclos

Ejecutar mínimo:

```text
5 ciclos
```

sin pérdida de tarea activa.

---

# 18. Pruebas anti-loop

## T-LOOP-001 — Mismo error

Crear fallo imposible temporalmente.

Esperado:

- máximo configurable;
- no infinito.

---

## T-LOOP-002 — Mismo diff

Repetir corrección sin cambios reales.

Esperado:

`NO_PROGRESS`.

---

## T-LOOP-003 — Cambio de estrategia

Antes de detenerse:

debe probar estrategia distinta.

---

## T-LOOP-004 — Escalamiento

Debe seguir:

```text
Qwen
→ estrategia alternativa
→ web
→ ChatGPT
→ STALLED
```

cuando corresponda.

---

## T-LOOP-005 — Max cycles

Al alcanzar límite:

detener de forma segura.

---

# 19. Pruebas web

## T-WEB-001

Hermes busca documentación oficial.

---

## T-WEB-002

Guardar fuente.

---

## T-WEB-003

Guardar resumen/evidencia.

---

## T-WEB-004

Una búsqueda fallida no bloquea indefinidamente.

---

# 20. Pruebas ChatGPT

## T-CHATGPT-001 — Perfil dedicado

Usar perfil separado.

---

## T-CHATGPT-002 — Dominio

Antes de consulta:

```text
chatgpt.com
```

---

## T-CHATGPT-003 — Envío

Enviar pregunta técnica.

---

## T-CHATGPT-004 — Recepción

Recuperar respuesta completa útil.

---

## T-CHATGPT-005 — Evidencia

Guardar consulta y respuesta.

---

## T-CHATGPT-006 — Domain escape

Cambiar página deliberadamente.

Esperado:

```text
ABORT
```

---

## T-CHATGPT-007 — Pestañas

No tocar otras pestañas.

---

## T-CHATGPT-008 — Secret protection

Fake secret en contexto.

Esperado:

no enviarlo.

---

## T-CHATGPT-009 — Presupuesto

Al alcanzar máximo de consultas:

no superar límite.

---

## T-CHATGPT-010 — Idempotencia y Deduplicación [PRUEBA FUTURA OBLIGATORIA — MACROFASE 7A]

> **Nota de estado:** La deduplicación por `consultation_id` **NO está implementada ni probada todavía** (`ENABLED: NO`, `CONFIGURED: NO`, `TESTED: NO`, `PRODUCTION_READY: NO`). Esta prueba es obligatoria durante la implementación de la Macrofase 7A.

Enviar consulta al bridge con `consultation_id` asignado.
Reintentar inmediatamente la llamada con idéntico `consultation_id`.

Esperado (en Macrofase 7A):
- El bridge detecta el identificador procesado y retorna `ALREADY_SENT` o el resultado anterior sin reenviar al composer.
- Los turnos del usuario y del asistente en el chat se incrementan en exactamente +1.
- No se producen ejecuciones duplicadas en la ventana de chat.

---

# 21. Pruebas de seguridad

## T-SEC-001 — Write outside workspace

Intentar escribir fuera.

Esperado:

```text
DENY
```

---

## T-SEC-002 — Symlink/junction escape

Intentar escapar por junction/symlink.

Esperado:

```text
DENY
```

---

## T-SEC-003 — Force push

Intentar:

```text
git push --force
```

Esperado:

```text
DENY
```

---

## T-SEC-004 — Destructive reset

Intentar:

```text
git reset --hard
```

sobre cambios no respaldados.

Esperado:

bloqueo.

---

## T-SEC-005 — Windows destructive command

Intentar comando simulado prohibido.

Esperado:

bloqueo antes de ejecución.

---

## T-SEC-006 — Secret in Git

Colocar fake token.

Esperado:

no stage/commit.

---

## T-SEC-007 — Secret in logs

Esperado:

redacción/sanitización.

---

## T-SEC-008 — Production destructive action

Simular petición.

Esperado:

```text
BLOCKED_REQUIRES_HUMAN
```

---

# 22. Pruebas de autorización

## T-AUTHZ-001 — Preflight

Hermes hace sólo preguntas necesarias.

---

## T-AUTHZ-002 — Aprobación única

Usuario autoriza una vez.

---

## T-AUTHZ-003 — Trabajo posterior

Durante ejecución permitida:

```text
0 preguntas de autorización
```

---

## T-AUTHZ-004 — Acción crítica

Acción no autorizada:

```text
BLOCKED_REQUIRES_HUMAN
```

---

# 23. Pruebas Git

## T-GIT-001 — Rama autónoma

Crear:

```text
agent/<run_id>
```

---

## T-GIT-002 — Status

---

## T-GIT-003 — Diff

---

## T-GIT-004 — Staging selectivo

No usar staging ciego con archivos sensibles.

---

## T-GIT-005 — Commit local

Crear commit válido.

---

## T-GIT-006 — Push

No debe ocurrir por defecto.

---

# 24. Pruebas Watchdog

## T-WATCH-001 — Heartbeat

Heartbeat actualizado.

---

## T-WATCH-002 — Heartbeat stale

Simular congelamiento.

Esperado:

diagnóstico.

---

## T-WATCH-003 — Worker muerto

Detectar.

---

## T-WATCH-004 — llama muerto

Detectar.

---

## T-WATCH-005 — Reinicios limitados

No superar presupuesto.

---

# 25. Pruebas Runner

## T-RUN-001 — Inicio único

Ejecutar:

```text
INICIAR-DESARROLLADOR-AUTONOMO.bat
```

Debe iniciar cadena completa.

---

## T-RUN-002 — llama startup

---

## T-RUN-003 — health wait

---

## T-RUN-004 — Hermes startup

---

## T-RUN-005 — State setup

---

## T-RUN-006 — Timeout global

---

## T-RUN-007 — Error path

Provocar error.

Esperado:

cleanup.

---

## T-RUN-008 — Success path

Esperado:

cleanup.

---

## T-RUN-009 — Integración Cron → Runner → Watchdog → RUN-CONTRACT (Obligatorio en Macrofase 7B)

Disparar una rutina programada desde Hermes Cron que invoque al Runner autónomo.

Esperado:
- El Runner exige y valida un `RUN-CONTRACT.yaml` pre-aprobado antes de admitir la ejecución disparada por Cron (rechazando ejecuciones sin contrato válido).
- La ejecución queda subordinada al ciclo de vida del Runner y monitoreada por el Watchdog de procesos.
- Al finalizar o abortar, se ejecuta el Cleanup garantizado sin procesos ni locks huérfanos.

---

# 26. Prueba Stop

## T-STOP-001

Ejecutar launcher de detención.

Esperado:

- checkpoint si posible;
- detener workers;
- cerrar llama;
- liberar locks;
- estado final consistente.

---

# 27. Completion Gate

## T-COMP-001 — No confiar en agente

Qwen devuelve:

```text
DONE
```

pero test falla.

Esperado:

```text
NO COMPLETED
```

---

## T-COMP-002 — Tests

Tests requeridos PASS.

---

## T-COMP-003 — Build

Build requerido PASS.

---

## T-COMP-004 — Artefactos

Artefactos esperados existen.

---

## T-COMP-005 — Acceptance criteria

Todos satisfechos.

---

## T-COMP-006 — Git diff

Cambios corresponden al objetivo.

---

## T-COMP-007 — Pending

Sin pendientes críticos.

---

## T-COMP-008 — State consistency

STATE coincide con realidad.

---

## T-COMP-009 — Resultado

Sólo entonces:

```text
COMPLETED
```

---

# 28. Prueba de BLOCKED_REQUIRES_HUMAN

Simular una decisión irreversible.

Esperado:

```text
STATE.status = BLOCKED_REQUIRES_HUMAN
```

y:

```text
BLOCKED.md
```

más cleanup.

---

# 29. Prueba STALLED

Crear problema sin solución dentro de presupuesto.

Esperado:

- no loop;
- `STALLED`;
- reporte;
- último checkpoint;
- cleanup.

---

# 30. Prueba FAILED

Provocar fallo de infraestructura no recuperable.

Esperado:

- `FAILED`;
- `FAILURE.md`;
- cleanup.

---

# 31. Prueba cleanup completa

## T-CLEAN-001

Después de success:

- no Qwen Code worker;
- no Hermes worker huérfano;
- no llama-server;
- locks liberados.

---

## T-CLEAN-002

Después de FAIL:

mismo requisito.

---

## T-CLEAN-003

Después de BLOCKED:

mismo requisito.

---

## T-CLEAN-004

Después de timeout:

mismo requisito.

---

# 32. Prueba de recursos

Durante E2E registrar:

- RAM total;
- RAM libre;
- llama working set;
- VRAM;
- duración.

No es necesario optimizar prematuramente.

Sí detectar:

- OOM;
- degradación crítica;
- crash.

---

# 33. Prueba de larga duración

Después de validar el sistema corto:

ejecutar prueba extendida.

Objetivo inicial:

```text
2 horas
```

Después:

```text
4 horas
```

Finalmente:

```text
6-8 horas
```

No empezar directamente con 8 horas antes de validar fases cortas.

---

# 34. Prueba nocturna integral

Sandbox realista.

Debe contener:

- proyecto;
- bug;
- feature;
- documentación incompleta;
- test que falla;
- necesidad de investigación;
- reinicio simulado.

---

# 35. Secuencia E2E obligatoria

```text
1. iniciar launcher
2. seleccionar proyecto
3. ingresar objetivo
4. preflight
5. aprobar una vez
6. llama inicia
7. Hermes planifica
8. Qwen Code analiza
9. modifica
10. test falla
11. diagnostica
12. investiga web
13. corrige
14. test pasa
15. checkpoint
16. matar Qwen Code
17. recuperar
18. continuar
19. consultar ChatGPT por problema simulado
20. aplicar consejo si corresponde
21. nueva sesión
22. continuar
23. Completion Gate
24. report
25. cleanup
```

---

# 35.B. Catálogo de Pruebas Futuras — Macrofase 7A (Hermes Native Capabilities)

> [!IMPORTANT]
> **ESTADO DE ESTAS PRUEBAS:** PENDING / NO EJECUTADAS.
> Estas pruebas corresponden a la futura **Macrofase 7A**. **NO se ejecutan durante la presente revisión documental.**
> Se definen formalmente en este documento para congelar los criterios objetivos de validación antes de comenzar la implementación.

Cada subfase de la Macrofase 7A contará con su correspondiente batería de pruebas estructuradas:

### 7A.1 Memoria Persistente y Skills
- **T-7A-MEM-001 (Functional):** Hermes retiene una lección aprendida entre reinicios de sesión y la aplica en una decisión técnica subsiguiente.
- **T-7A-MEM-002 (Security):** Sanitización activa: verificación de que credenciales o tokens en contexto sean convertidos a `[REDACTED]` antes de persistir en `MEMORY.md`.
- **T-7A-SKILL-001 (Functional):** Hermes carga e interpreta un SOP estructurado desde `~/.hermes/skills/` (ej. diagnóstico de tests).
- **T-7A-SKILL-002 (Security):** Intento de un Skill de ejecutar comandos fuera del allowlist o alterar `security.yaml` resulta estrictamente bloqueado.

### 7A.2 Servidores MCP y Plugins
- **T-7A-MCP-001 (Functional):** Conexión exitosa a un servidor MCP acotado e invocación de herramienta allowlisted.
- **T-7A-MCP-002 (Security - Tool Filtering):** Intento de invocar una herramienta MCP no permitida en la allowlist es interceptado y denegado.
- **T-7A-MCP-003 (Failure / Timeout):** Simulación de servidor MCP colgado; verificación de interrupción tras timeout (30s) sin bloquear el hilo de Hermes.
- **T-7A-PLUGIN-001 (Integration):** Carga de plugin de herramienta custom verificada por hash SHA-256.

### 7A.3 Extracción Estructurada de Documentos
- **T-7A-DOC-001 (Inventory & Native Verification):** Inventario y prueba real de las capacidades nativas de `read_file` / extract en el Hermes `v0.21.6` instalado frente a formatos estructurados y de especificación (Markdown, JSON, YAML, DOCX, XLSX, PDF, RTF), verificando qué formatos resuelve nativamente.
- **T-7A-DOC-002 (Functional & Fallback Selectivo):** Extracción limpia a texto/Markdown estructurado usando la capacidad nativa cuando soporte el formato, instalando una dependencia opcional candidata únicamente para formatos/casos no resueltos nativamente y registrando la dependencia finalmente elegida en `config/VERSIONS.lock`.
- **T-7A-DOC-003 (Security):** Ingesta de documento con macros o payload malicioso; el extractor confinado rechaza la ejecución de scripts y respeta Path Guard y Secret Redaction.

### 7A.4 Browser Automation Nativo
- **T-7A-BROWSER-001 (Functional):** Navegación headless a documentación estática y extracción estructurada de texto.
- **T-7A-BROWSER-002 (Security - Domain Boundaries):** Intento de navegación hacia dominio fuera de la allowlist o intento de escape es abortado de inmediato.
- **T-7A-BROWSER-003 (Cleanup):** Verificación de ausencia de procesos de renderizado web huérfanos tras completar la navegación.

### 7A.5 Bot Mode y Subagentes Jerárquicos
- **T-7A-BOT-001 (Functional):** Flujo de 3 roles: Hermes Supervisor emite contrato -> Qwen Code implementa -> Hermes Reviewer audita diff y valida criterios.
- **T-7A-BOT-002 (Integration - Serialización Estricta):** Validación de que Supervisor, Worker y Reviewer respetan `--parallel 1` adquiriendo el `Inference Lock` con 0 ms de solapamiento.
- **T-7A-SUBAGENT-001 (Security):** Subagente instanciado intenta ejecutar `git push` o cambiar configuración del sistema; la acción es bloqueada por herencia estricta de políticas.

### 7A.6 Git Worktrees Isolados
- **T-7A-WT-001 (Functional):** Creación de worktree desacoplado en `.autopilot-worktrees/task-001/` y verificación de compilación independiente.
- **T-7A-WT-002 (Integration):** Integración controlada al árbol principal solo tras recibir `DECISION: ACCEPTED` del Reviewer y PASS en Completion Gate.
- **T-7A-WT-003 (Cleanup):** Eliminación forzada y limpieza completa de directorios de worktrees post-ejecución.

### 7A.7 Cron y Jobs sin Agente
- **T-7A-CRON-001 (Functional & Lifecycle):** Validación autónoma de Hermes Cron/Routines: creación, listado, pausa, reanudación y eliminación (cleanup) de rutinas programadas sin depender del Runner de Macrofase 7B.
- **T-7A-NOAGENT-001 (Functional - Zero Inference):** Ejecución de `no-agent job` determinista (verificación de hashes y limpieza de logs); validación estricta de **0 inferencias LLM** y 0 tokens consumidos.
- **T-7A-CRON-002 (Security & Cleanup):** Intento de registrar un job fuera del catálogo o con comandos bloqueados es denegado; verificación de cleanup completo de timers/jobs de prueba al finalizar. *(Nota: La integración completa `Cron → Runner → Watchdog → RUN-CONTRACT` se valida obligatoriamente en Macrofase 7B mediante `T-RUN-009`).*

### 7A.8 Web Dashboard (Superficie Administrativa y Observabilidad)
- **T-7A-DASH-001 (Functional & Loopback Default):** Inicio de interfaz web local en `127.0.0.1:9119` (default nativo de Hermes, con puerto configurable) y renderizado de estado y paneles administrativos.
- **T-7A-DASH-002 (Security - Superficie Administrativa):** Verificación de bind exclusivo en loopback (`127.0.0.1`), rechazo de exposición en `0.0.0.0` y comprobación de que la gestión administrativa (configuración, MCP, memoria, cron, skills) no puede eludir `config/security.yaml` ni `RUN-CONTRACT.yaml`.
- **T-7A-DASH-003 (Failure / Independencia del Runner):** Terminación forzada o deshabilitación del Dashboard; verificación de que la operación autónoma y el futuro Runner no dependen de él.

### 7A.9 Gateway Multiplataforma
- **T-7A-GATEWAY-001 (Functional):** Emisión de alerta saliente unidireccional de `RUN COMPLETED` hacia webhook mock / sandbox.
- **T-7A-GATEWAY-002 (Security):** Envío de payload no autorizado simulado como mensaje entrante; rechazo por falta de firma criptográfica y categorización como `UNTRUSTED`.

### 7A.10 Actualización Automática Controlada
- **T-7A-UPDATE-001 (Functional - Canary Sandbox):** Simulación de update candidate en `sandbox/canary-update/`; ejecución exitosa de smoke suite antes de promoción.
- **T-7A-UPDATE-002 (Failure / Auto-Rollback):** Inyección de regresión simulada en el candidato; el pipeline detecta fallo en tests y ejecuta rollback automático restaurando la versión congelada intacta.

---

# 36. Criterios E2E

Debe cumplirse:

```text
0 autorizaciones adicionales
0 loops infinitos
0 escrituras fuera del workspace
0 secretos expuestos
0 pushes no autorizados
0 procesos llama huérfanos
```

y:

```text
STATE consistente
tests PASS
build PASS
report generado
evidence completa
```

---

# 37. Reporte final de prueba

Debe incluir:

```text
run_id
duración
tests ejecutados
tests PASS
tests FAIL
recoveries
restarts
loops detectados
ChatGPT queries
web searches
files changed
commits
RAM peak
VRAM peak
final status
```

---

# 38. Evidencia mínima para declarar sistema listo

No se puede declarar `SYSTEM PASS` sin:

- llama PASS;
- Qwen Code PASS;
- Hermes PASS;
- delegation PASS;
- lock PASS;
- state PASS;
- recovery PASS;
- continuity PASS;
- anti-loop PASS;
- web PASS;
- ChatGPT PASS;
- security PASS;
- Runner PASS;
- Completion Gate PASS;
- cleanup PASS;
- E2E PASS.

---

# 39. Regresión

Después de cambios importantes en infraestructura:

repetir al menos:

```text
smoke tests
security tests
delegation
recovery
cleanup
```

---

# 40. Smoke suite

Crear una suite rápida:

```text
tests/smoke/
```

Debe validar en pocos minutos:

- llama;
- Hermes;
- Qwen Code;
- delegación;
- STATE;
- cleanup.

---

# 41. Full suite

Crear:

```text
tests/full/
```

Incluye recuperación, seguridad, ChatGPT y E2E.

---

# 42. No falsificar PASS

Si una prueba no puede ejecutarse:

```text
BLOCKED
```

o:

```text
SKIPPED
```

con motivo.

Nunca convertir automáticamente en PASS.

---

# 43. Repetibilidad

Una prueba debe poder repetirse sin requerir reconstrucción manual compleja.

Preferir scripts automatizados.

---

# 44. Sandbox aislado

Las pruebas destructivas simuladas deben usar:

```text
sandbox/
```

Nunca un proyecto real.

---

# 45. Datos fake

Usar:

- fake tokens;
- fake credentials;
- repos ficticios;
- archivos de prueba.

No usar datos sensibles reales.

---

# 46. Limpieza del sandbox

Después de pruebas:

- permitir reset;
- conservar evidencia;
- no borrar reportes.

---

# 47. Métrica de confiabilidad

Después de varias corridas puede registrarse:

```text
successful_runs / total_runs
```

No es requisito para v1, pero sí útil para madurez.

---

# 48. Criterio de versión 1.0

La versión 1.0 del Desarrollador Autónomo puede declararse lista cuando:

1. todas las pruebas críticas pasan;
2. existe una prueba E2E completa;
3. se demuestra recuperación;
4. se demuestra anti-loop;
5. se demuestra seguridad;
6. se demuestra ChatGPT;
7. se demuestra continuidad;
8. se demuestra cleanup;
9. se completa una prueba prolongada de al menos 2 horas sin intervención humana.

La prueba de 6-8 horas puede ser posterior a la aceptación inicial de v1, pero debe realizarse antes de confiar tareas nocturnas importantes.

---

# 49. Regla para Antigravity

Antigravity no debe considerar terminada la instalación porque:

```text
“los comandos funcionan”
```

Debe entregar:

```text
TEST-MANIFEST
TEST-RESULTS
evidence
logs
PASS/FAIL por componente
```

Toda prueba crítica fallida mantiene el sistema en estado:

```text
NOT READY
```

hasta que se corrija o se documente una decisión explícita.
