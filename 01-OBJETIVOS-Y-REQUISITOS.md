# 01 — Objetivos y requisitos
## Proyecto: Desarrollador Autónomo

**Versión:** 2.0  
**Estado:** BORRADOR PARA APROBACIÓN  
**Arquitectura base:** Hermes Agent + Qwen Code CLI + Qwen local mediante llama.cpp

---

# 1. Objetivo general

Construir un sistema local de programación autónoma capaz de recibir:

1. una carpeta de proyecto;
2. un objetivo general;
3. criterios de aceptación;

y trabajar de forma autónoma durante períodos prolongados hasta:

- completar el objetivo y demostrarlo con evidencia;
- o detenerse de forma segura porque existe un bloqueo real que requiere intervención humana.

El sistema debe ser apto para trabajo nocturno y no debe depender de supervisión humana continua.

---

# 2. Principios obligatorios

## P-01 — El chat no es la fuente de verdad

El estado del proyecto debe persistir fuera de las conversaciones.

La fuente de verdad debe estar compuesta por:

1. filesystem/código real;
2. Git;
3. tests/builds;
4. `STATE.json`;
5. `STATE.md`;
6. `QWEN.md`;
7. `EVENTS.jsonl`;
8. logs;
9. sesiones persistentes de Qwen Code;
10. sesiones persistentes de Hermes.

Una compactación, reinicio o cambio de sesión no debe obligar a recomenzar el proyecto.

---

## P-02 — Evidencia antes que afirmaciones

El sistema no debe considerar completada una tarea solamente porque un agente diga “terminado”.

Debe existir evidencia verificable, por ejemplo:

- test PASS;
- build PASS;
- endpoint responde;
- archivo esperado existe;
- Git diff coherente;
- artefacto generado;
- criterio de aceptación cumplido.

---

## P-03 — Autonomía contenida

Después de una autorización inicial, el sistema debe trabajar sin pedir permisos repetitivos para acciones permitidas.

La autonomía no implica acceso irrestricto al sistema operativo.

---

## P-04 — Recuperación antes que dependencia del contexto

Si Hermes, Qwen Code o llama.cpp se reinician, el sistema debe reconstruir el estado y continuar usando información persistida.

---

## P-05 — Seguridad por defecto

Toda operación destructiva, irreversible, de producción, de credenciales o fuera del workspace debe estar bloqueada salvo autorización explícita.

---

## P-06 — Capacidades nativas subordinadas a la capa determinista

Las capacidades nativas de Hermes (memoria Nivel 2, skills, MCP, browser, bots, cron, subagentes, gateway) amplían la funcionalidad pero no constituyen la fuente de verdad operativa.
En caso de conflicto, la verdad técnica de la Deterministic Control Layer (Git, tests/builds, `STATE.json`, `RUN-CONTRACT.yaml`) prevalece de forma absoluta.

---

## P-07 — Prefer Native When Verified

Se preferirán las capacidades nativas provistas por Hermes Agent frente a desarrollos custom únicamente cuando:
- Estén presentes y comprobadas en la versión congelada instalada (v0.21.6);
- Hayan superado una revisión de seguridad y encuadre de privilegios mínimos;
- Hayan superado pruebas deterministas completas;
- No reduzcan ni degraden las garantías de contención y reproducibilidad.

---

# 3. Componentes obligatorios

## C-01 — Hermes Supervisor
Rol: supervisor / orquestador principal.
Debe:
- recibir el objetivo general y ejecutar preflight;
- planificar y emitir contratos `DelegationRequest`;
- dividir tareas e investigar (web y ChatGPT);
- controlar el progreso y supervisar a los workers;
- validar entregables y emitir aceptación/rechazo formal (`DECISION: ACCEPTED/REJECTED`).

Hermes no debe competir con Qwen Code editando simultáneamente los mismos archivos.

---

## C-02 — Qwen Code CLI
Rol: especialista autónomo de programación (Coding Worker).
Debe:
- analizar repositorios y arquitectura de código;
- leer, crear y editar archivos;
- ejecutar comandos, linters, tests y builds;
- utilizar Git local;
- diagnosticar errores y autocorregirse;
- devolver resultados estructurados `DelegationResult` con diffs y evidencia.

---

## C-03 — llama.cpp + Qwen local
Modelo principal local compartido.
Configuración base validada:
```text
--ctx-size 65536
--parallel 1
--cpu-moe
--n-gpu-layers 99
--flash-attn on
--cache-type-k q8_0
--cache-type-v q8_0
--jinja
```
Endpoint base: `http://127.0.0.1:8080` | Alias: `qwen36`

---

## C-04 — Night Supervisor / Runner
Capa determinista externa a los LLM responsable del ciclo de vida de procesos.
Responsabilidades:
- iniciar llama.cpp y verificar health check;
- orquestar la ejecución, gestionar timeouts y heartbeats;
- detectar caídas de procesos y activar Watchdog;
- coordinar checkpoints y recovery determinista;
- ejecutar cleanup garantizado y emitir reportes finales.

---

## C-05 — Inference Lock
Primitiva de exclusión mutua cross-process (.NET Mutex) que garantiza acceso serializado estricto al modelo local (`--parallel 1`).
Impide terminantemente que dos agentes o subagentes ejecuten inferencias simultáneas.

---

## C-06 — Hermes Reviewer y Bot Mode
Roles especializados de Hermes configurados para segregar funciones:
- `HERMES REVIEWER`: auditor independiente que verifica diffs y criterios de aceptación sin sesgo del implementador;
- `HERMES RESEARCHER`: asistente enfocado en documentación técnica.
Todos los roles de Bot Mode operan bajo el mismo modelo local y bajo serialización estricta del `Inference Lock`.

---

## C-07 — Servidores MCP y Plugins
Mecanismo de integración de herramientas externas bajo el principio de mínima superficie:
- Allowlist explícito de herramientas activas;
- Confinamiento de scope y timeouts deterministas;
- No se admiten servidores MCP sobredimensionados sin justificación.

---

## C-08 — Git Worktrees Isolados
Aislamiento físico en `.autopilot-worktrees/task-<ID>/` para ejecución segura de tareas de refactorización o workers paralelos, integrando cambios al árbol principal sólo tras el `Completion Gate`.

---

## C-09 — Cron y Jobs sin Agente
- `Cron / Routines`: disparadores periódicos subordinados al Runner;
- `Jobs sin Agente`: tareas deterministas de mantenimiento (limpieza de logs, hash checks, backups) con **cero inferencias LLM**.

---

## C-10 — Extracción Documental
Capacidad de ingesta de especificaciones y documentación de proyecto en formatos DOCX, XLSX, PPTX, PDF, RTF y Markdown, distinguiendo dependencias nativas de opcionales.

---

## C-11 — Pipeline de Auto-Update Seguro
Procedimiento de actualización de Hermes Agent estructurado en sandbox canary, verificación de hash/origen, suite de regresión y rollback automático en caso de anomalías.

---

## C-12 — Idempotencia del Bridge ChatGPT
Mecanismo en el puente CDP a `chatgpt.com` que garantiza que cada consulta con identificador `consultation_id` sea transmitida a lo sumo una única vez, retornando `ALREADY_SENT` ante reintentos.

---

# 4. Requisitos funcionales

## RF-001 — Selección de proyecto

El usuario debe poder indicar una carpeta de proyecto existente.

### Aceptación
- el sistema valida que la carpeta exista;
- detecta si es repositorio Git;
- detecta stack básico;
- registra ruta absoluta;
- no modifica nada durante la detección inicial.

**Prioridad:** CRÍTICA

---

## RF-002 — Objetivo general

El usuario debe poder expresar el trabajo en lenguaje natural.

Ejemplo:

> “Tomá este proyecto, implementá autenticación OAuth, investigá lo necesario, probalo y no termines hasta que funcione.”

### Aceptación
Hermes convierte el objetivo en un plan verificable sin exigir que el usuario indique archivos o comandos concretos.

**Prioridad:** CRÍTICA

---

## RF-003 — Preflight único

Antes del modo autónomo, Hermes puede hacer preguntas necesarias.

Debe preguntar únicamente por ambigüedades que puedan cambiar:

- alcance;
- arquitectura;
- seguridad;
- comportamiento visible;
- datos;
- operaciones irreversibles.

No debe preguntar por detalles menores que pueda resolver de forma segura.

### Aceptación
Al finalizar preflight se genera `RUN-CONTRACT.yaml`.

**Prioridad:** CRÍTICA

---

## RF-004 — Autorización única

Después del preflight, el usuario puede aprobar la ejecución completa.

Luego de aprobar:

- no pedir autorización para editar dentro del workspace;
- no pedir autorización para ejecutar tests;
- no pedir autorización para builds;
- no pedir autorización para instalar dependencias del proyecto;
- no pedir autorización para Git local permitido;
- no pedir autorización para investigación web.

### Aceptación
Una ejecución de prueba completa puede realizarse sin intervención humana adicional.

**Prioridad:** CRÍTICA

---

## RF-005 — Planificación

Hermes debe dividir el objetivo en hitos/tareas verificables.

Cada tarea debe tener:

- ID;
- descripción;
- criterios de aceptación;
- estado;
- dependencias;
- evidencia esperada.

**Prioridad:** ALTA

---

## RF-006 — Delegación Hermes → Qwen Code

Hermes debe poder invocar Qwen Code CLI automáticamente.

La delegación debe incluir como mínimo:

- proyecto;
- tarea;
- restricciones;
- criterios de aceptación;
- archivos/estado relevante;
- límite de tiempo;
- formato esperado de respuesta.

### Aceptación
Hermes delega una tarea real, Qwen Code modifica un sandbox, prueba el resultado y Hermes recibe evidencia.

**Prioridad:** CRÍTICA

---

## RF-007 — Investigación web

Hermes debe poder buscar información actual cuando sea necesaria.

Orden preferido:

1. documentación oficial;
2. repositorios/issues oficiales;
3. fuentes técnicas fiables;
4. otras fuentes relevantes.

### Aceptación
Las conclusiones técnicas importantes deben registrar fuente o evidencia.

**Prioridad:** ALTA

---

## RF-008 — Consulta a ChatGPT

Debe existir una herramienta específica `consultar_chatgpt`.

Uso previsto:

- problemas estancados;
- segunda opinión;
- revisión de estrategia;
- interpretación compleja;
- búsqueda de alternativa.

ChatGPT es consultor, no ejecutor.

### Aceptación
Hermes puede enviar contexto resumido, obtener respuesta, guardarla como evidencia y decidir qué hacer.

**Prioridad:** ALTA

---

## RF-009 — Chrome dedicado

La consulta a ChatGPT debe usar un perfil/pestaña controlada.

Reglas:

- dominio permitido: `chatgpt.com`;
- no navegar a otros dominios;
- no usar pestañas personales;
- no abrir nuevas pestañas innecesarias;
- no cerrar la pestaña dedicada;
- no exponer credenciales.

### Aceptación
La herramienta aborta si el dominio cambia.

**Prioridad:** ALTA

---

## RF-010 — Autocorrección

Qwen Code debe poder ejecutar:

```text
analizar
→ implementar
→ ejecutar
→ detectar fallo
→ diagnosticar
→ corregir
→ volver a probar
```

### Aceptación
Un test inicialmente fallido debe poder quedar PASS sin intervención humana en un sandbox diseñado para la prueba.

**Prioridad:** CRÍTICA

---

## RF-011 — Ciclos controlados

Cada vuelta importante debe ser un ciclo numerado.

Ejemplo:

```text
cycle 1
cycle 2
cycle 3
...
```

Cada ciclo debe registrar:

- tarea;
- acciones;
- cambios;
- resultado;
- progreso;
- siguiente paso.

**Prioridad:** ALTA

---

## RF-012 — Anti-loop

Debe detectar ausencia de progreso.

Valores iniciales sugeridos:

- mismo fallo sin progreso: 3;
- ciclos sin progreso: 3;
- máximo de ciclos por objetivo: 20.

Debe cambiar de estrategia antes de detenerse.

### Aceptación
Una tarea imposible simulada no puede ejecutarse indefinidamente.

**Prioridad:** CRÍTICA

---

## RF-013 — Persistencia de estado

Cada proyecto autónomo debe disponer de:

```text
.autopilot/
  RUN-CONTRACT.yaml
  STATE.json
  STATE.md
  EVENTS.jsonl
  logs/
  evidence/
  checkpoints/
  reports/
```

**Prioridad:** CRÍTICA

---

## RF-014 — STATE.json

Debe ser la fuente estructurada de estado para máquinas.

Debe registrar como mínimo:

- run_id;
- objetivo;
- estado;
- ciclo;
- tareas completadas;
- tarea activa;
- pendientes;
- decisiones;
- fallos;
- tests;
- build;
- archivos modificados;
- próxima acción;
- progreso.

**Prioridad:** CRÍTICA

---

## RF-015 — STATE.md

Debe ser una representación legible para humanos del mismo estado operativo.

No debe sustituir a `STATE.json`.

**Prioridad:** ALTA

---

## RF-016 — QWEN.md

Debe contener información estable:

- arquitectura;
- convenciones;
- comandos;
- reglas;
- validación;
- restricciones.

No debe utilizarse como diario de ejecución.

**Prioridad:** ALTA

---

## RF-017 — EVENTS.jsonl

Debe registrar cronológicamente eventos relevantes.

Ejemplos:

- COMMAND;
- TEST;
- BUILD;
- ERROR;
- WEB_SEARCH;
- CHATGPT_QUERY;
- FILE_MODIFIED;
- CHECKPOINT;
- RECOVERY;
- COMPLETION_GATE.

**Prioridad:** ALTA

---

## RF-018 — Reanudación de Qwen Code

Usar `--continue` / `--resume` mientras la sesión siga siendo útil.

Crear sesión limpia cuando convenga.

### Aceptación
Cerrar Qwen Code y reanudar no debe provocar recomenzar el trabajo.

**Prioridad:** CRÍTICA

---

## RF-019 — Reanudación de Hermes

Las sesiones persistentes y búsqueda de sesiones de Hermes deben utilizarse para recuperar contexto histórico cuando sea necesario.

### Aceptación
Una nueva sesión de Hermes puede reconstruir el trabajo mediante estado + historial.

**Prioridad:** ALTA

---

## RF-020 — Recovery Protocol

Ante una nueva sesión o recuperación:

1. leer contrato;
2. leer estado;
3. leer QWEN.md;
4. `git status`;
5. `git diff`;
6. comprobar tests/build relevantes;
7. reconciliar inconsistencias;
8. continuar.

### Aceptación
Simular caída y comprobar continuidad.

**Prioridad:** CRÍTICA

---

## RF-021 — Git

Git se usa como evidencia y recuperación.

Permitido por defecto:

- status;
- diff;
- log;
- branch local;
- commit local;
- checkout seguro cuando corresponda.

Bloqueado por defecto:

- force push;
- push automático;
- reset destructivo;
- reescritura peligrosa de historia.

**Prioridad:** CRÍTICA

---

## RF-022 — Rama de trabajo autónomo

Cuando sea viable, ejecutar en una rama separada.

Ejemplo:

```text
agent/night-YYYY-MM-DD
```

### Aceptación
El agente no modifica `main/master` directamente salvo configuración explícita.

**Prioridad:** ALTA

---

## RF-023 — Logs completos

Guardar logs separados de:

- Hermes;
- Qwen Code;
- llama.cpp;
- tests;
- builds;
- runner.

**Prioridad:** CRÍTICA

---

## RF-024 — Evidencias externas

Guardar las consultas relevantes en:

```text
.autopilot/evidence/web/
.autopilot/evidence/chatgpt/
.autopilot/evidence/tests/
```

**Prioridad:** MEDIA

---

## RF-025 — Completion Gate

Antes de `COMPLETED`, verificar:

- objetivo;
- criterios de aceptación;
- tests;
- build;
- artefactos;
- Git diff;
- pendientes;
- estado.

### Aceptación
Un agente no puede marcar `COMPLETED` únicamente mediante texto.

**Prioridad:** CRÍTICA

---

## RF-026 — Informe final

Generar un reporte que incluya:

- resultado;
- tiempo;
- ciclos;
- archivos cambiados;
- decisiones;
- tests;
- build;
- fallos;
- correcciones;
- consultas web;
- consultas ChatGPT;
- pendientes;
- estado Git;
- motivo de finalización.

**Prioridad:** ALTA

---

## RF-027 — Cleanup

Al finalizar, fallar o abortar:

- detener workers;
- detener procesos auxiliares propios;
- cerrar `llama-server`;
- comprobar que se liberó;
- guardar estado final;
- cerrar logs.

### Aceptación
No queda `llama-server` activo.

**Prioridad:** CRÍTICA

---

## RF-028 — Punto único de inicio

Debe existir un único mecanismo para iniciar el sistema.

Nombre provisional:

```text
INICIAR-DESARROLLADOR-AUTONOMO.bat
```

Puede lanzar internamente otros componentes.

**Prioridad:** ALTA

---

## RF-029 — Reutilización

El sistema no debe depender de un proyecto de prueba concreto.

Debe aceptar diferentes proyectos mediante configuración.

**Prioridad:** CRÍTICA

---

## RF-030 — Modo sandbox

Debe existir un proyecto sandbox para validar cambios en la infraestructura antes de usar proyectos reales.

**Prioridad:** CRÍTICA

---

## RF-031 — Idempotencia del Bridge ChatGPT

Toda consulta hacia ChatGPT debe incluir un `consultation_id` único. El sistema debe garantizar que un identificador se transmita como máximo una única vez al compositor.
Si se produce un reintento con el mismo identificador, el bridge debe retornar `ALREADY_SENT` sin pulsar "Send" nuevamente.
El sistema debe verificar que los turnos del usuario y del asistente se incrementen en exactamente +1.

**Prioridad:** ALTA

---

## RF-032 — Aislamiento mediante Git Worktrees

Para tareas complejas o workers auxiliares, el sistema debe poder inicializar un árbol de trabajo desacoplado en `.autopilot-worktrees/task-<ID>/`.
Las modificaciones se validan con tests y diffs en el worktree antes de su integración al branch principal mediante el Completion Gate.

**Prioridad:** ALTA

---

## RF-033 — Tareas Deterministas sin Agente (No-Agent Jobs)

El sistema debe permitir la ejecución programada o periódica de rutinas de mantenimiento (limpieza de temporales, backups de estado, verificación de hashes) utilizando scripts deterministas con **cero inferencias LLM**.

**Prioridad:** MEDIA

---

## RF-034 — Extracción Estructurada de Documentos

El sistema debe ser capaz de ingerir especificaciones en formatos no planos (DOCX, XLSX, PDF, RTF) convirtiéndolas a texto estructurado para el análisis por parte de Hermes Supervisor.

**Prioridad:** MEDIA

---

## RF-035 — Pipeline de Auto-Update Seguro

Cualquier actualización de Hermes Agent debe ejecutarse primero en un sandbox canary con verificación de origen, versión y hash, evaluando smoke tests y regresiones antes de su promoción a producción, con capacidad de rollback automático.

**Prioridad:** ALTA

---

# 5. Requisitos de rendimiento y recursos

## RR-001 — Contexto Qwen

Configuración oficial inicial:

```text
65536 tokens
```

No reducir a 16K/32K salvo motivo documentado.

---

## RR-002 — Paralelismo

Configuración inicial:

```text
--parallel 1
```

Sólo una inferencia local activa simultáneamente.

---

## RR-003 — Concurrencia externa

Se permiten tareas simultáneas que no requieran inferencia local.

Ejemplos:

- tests;
- builds;
- web;
- lectura de archivos;
- procesos independientes seguros.

---

## RR-004 — llama.cpp

Debe permanecer activo durante una ejecución autónoma completa.

No reiniciar entre llamadas normales.

---

## RR-005 — Consumo validado

Prueba local realizada con Qwen 64K:

| Tokens reales | RAM máx. usada | RAM libre mín. |
|---:|---:|---:|
| 8K | 21.83 GB | 9.84 GB |
| 16K | 22.12 GB | 9.55 GB |
| 32K | 22.37 GB | 9.30 GB |
| 48K | 22.37 GB | 9.30 GB |
| 60K | 22.39 GB | 9.28 GB |

Esto habilita 64K como configuración base inicial.

---

# 6. Estados globales

Estados válidos del trabajo:

```text
PREFLIGHT
READY
RUNNING
VERIFYING
STALLED
BLOCKED_REQUIRES_HUMAN
FAILED
COMPLETED
```

`COMPLETED` sólo se alcanza tras Completion Gate.

---

# 7. Condiciones para detenerse

El sistema debe detenerse de forma segura cuando:

- alcanza Completion Gate;
- alcanza timeout global;
- alcanza máximo de ciclos;
- no existe progreso tras escalamiento;
- encuentra una acción prohibida imprescindible;
- requiere credenciales no disponibles;
- necesita una decisión irreversible;
- detecta corrupción o riesgo para el proyecto.

---

# 8. No objetivos iniciales

Fuera de alcance de la primera versión:

- despliegues destructivos automáticos a producción;
- push automático a repositorios remotos;
- administración general de Windows;
- actualización de drivers;
- gestión autónoma de credenciales;
- ejecución paralela de múltiples inferencias Qwen;
- multi-PC distribuido.

Se podrán agregar posteriormente.

---

# 9. Criterio de aceptación global del sistema

La primera versión se considera válida sólo si supera una prueba end-to-end donde:

1. usuario selecciona sandbox;
2. proporciona objetivo;
3. Hermes hace preflight;
4. usuario autoriza una vez;
5. llama.cpp inicia;
6. Hermes planifica;
7. Qwen Code modifica código;
8. se ejecuta un test que falla;
9. Qwen Code diagnostica;
10. investiga si hace falta;
11. corrige;
12. test pasa;
13. se crea checkpoint;
14. se simula caída/reanudación;
15. sistema recupera estado;
16. termina objetivo;
17. Completion Gate pasa;
18. genera reporte;
19. cierra llama.cpp;
20. no queda intervención humana adicional durante la ejecución.

---

# 10. Regla para Antigravity

Antigravity debe implementar esta especificación por fases.

No debe declarar una fase completa sin evidencia reproducible.

Si descubre que un requisito no es técnicamente viable, debe:

1. no ocultarlo;
2. registrar evidencia;
3. proponer alternativas;
4. no cambiar silenciosamente la arquitectura.

