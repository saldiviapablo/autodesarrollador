# 07 — Roadmap de implementación
## Proyecto: Desarrollador Autónomo

**Versión:** 2.0
**Estado:** APROBADO / FROZEN PARA IMPLEMENTACIÓN DE MACROFASE 7A
**Arquitectura base:** Hermes Agent + Qwen Code CLI + Qwen local mediante llama.cpp

---

# 1. Objetivo y Estructura de Macrofases

Definir el orden obligatorio de implementación dividido en **8 macrofases visibles**.

Principio:

> **No avanzar a la siguiente fase si la anterior no fue verificada.**

### Resumen de Macrofases del Proyecto

| MACROFASE | DESCRIPCIÓN | FASES INTERNAS | ESTADO |
|:---|:---|:---:|:---:|
| **Macrofase 1** | Baseline e Inventario | Fases 0 a 4 | **PASS** |
| **Macrofase 2** | Qwen Code CLI | Fase 5 | **PASS** |
| **Macrofase 3** | Hermes Agent | Fase 6 | **PASS** |
| **Macrofase 4** | Integración Hermes ↔ Qwen Code | Fases 7 a 9 | **PASS** |
| **Macrofase 5** | Memoria y Continuidad | Fases 10 a 12 | **PASS** |
| **Macrofase 6** | Web, ChatGPT, Seguridad y Anti-Loop | Fases 13 a 16 | **PASS** |
| **Macrofase 7A**| Hermes Native Capabilities | 7A.1–7A.10 PASS; ChatGPT Idempotency PASS; regression gate PASS | **PASS** |
| **Macrofase 7B**| Runner Autónomo Nocturno | Fases 17 a 22 | **PASS** |
| **Macrofase 8** | Validación Final | Fases 23 a 28 | **PENDING** |

Cada fase debe producir:

- entregables;
- pruebas;
- evidencia;
- PASS / FAIL;
- rollback si modificó entorno.

---

# 2. Regla general de ejecución

Antigravity debe trabajar con este patrón:

```text
INSPECT
↓
PLAN
↓
BACKUP
↓
IMPLEMENT
↓
VERIFY
↓
DOCUMENT
↓
PASS / FAIL
```

Nunca:

```text
IMPLEMENT EVERYTHING
↓
SEE WHAT BROKE
```

---

# 3. Fase 0 — Documentación base

## Objetivo

Congelar la arquitectura antes de instalar.

## Entregables

- `00-README.md`
- `01-OBJETIVOS-Y-REQUISITOS.md`
- `02-ARQUITECTURA.md`
- `03-MEMORIA-Y-CONTINUIDAD.md`
- `04-AUTONOMIA-Y-SEGURIDAD.md`
- `05-INSTALACION-Y-CONFIGURACION.md`
- `06-PRUEBAS-Y-CRITERIOS-DE-EXITO.md`
- `07-ROADMAP.md`
- `AGENTS.md`

## Condición de salida

```text
DOCS BASELINE = APPROVED
```

---

# 4. Fase 1 — Inventario del entorno

## Objetivo

Descubrir exactamente qué existe antes de tocar el sistema.

## Detectar

```text
llama.cpp
modelo Qwen
Git
GitHub CLI
Node
npm
Python
PowerShell
Chrome
Qwen Code CLI
Hermes Agent
```

## Registrar

- ruta;
- versión;
- estado;
- configuración existente;
- puertos;
- variables relevantes;
- launchers legacy.

## Entregables

```text
docs/INVENTORY.md
config/INSTALLATION-STATE.json
```

## Prohibido

No instalar todavía salvo dependencia mínima necesaria para completar inventario.

## Condición de salida

```text
INVENTORY PASS
```

---

# 5. Fase 2 — Backup y baseline

## Objetivo

Crear punto seguro antes de modificar configuraciones.

## Crear

```text
backups/preinstall-<timestamp>/
```

## Respaldar

- configs que se vayan a tocar;
- scripts existentes relevantes;
- launchers;
- configuraciones Qwen Code/Hermes si ya existen.

## Registrar

- manifiesto;
- hashes si es útil;
- rutas originales.

## Condición de salida

```text
BACKUP PASS
```

---

# 6. Fase 3 — Validación de llama.cpp + Qwen

## Objetivo

Confirmar que la base local existente funciona sin modificarla innecesariamente.

## Configuración esperada

```text
ctx = 65536
parallel = 1
cpu-moe
n-gpu-layers = 99
flash-attn = on
cache K/V = q8_0
jinja
```

## Pruebas

- binario existe;
- modelo existe;
- servidor inicia;
- health responde;
- alias correcto;
- contexto 64K;
- inferencia simple;
- cleanup.

## No hacer

- no descargar otro modelo;
- no cambiar drivers;
- no actualizar llama.cpp sin necesidad.

## Condición de salida

```text
LLAMA PASS
```

---

# 7. Fase 4 — Configuración central

## Objetivo

Eliminar configuraciones duplicadas y hardcode innecesario.

## Crear

```text
config/system.yaml
config/security.yaml
config/VERSIONS.lock
```

## Debe centralizar

- ruta llama;
- ruta modelo;
- host;
- puerto;
- contexto;
- parallel;
- rutas Hermes;
- rutas Qwen Code;
- timeouts;
- límites;
- Chrome;
- seguridad.

## Condición de salida

```text
CONFIG PASS
```

---

# 8. Fase 5 — Qwen Code CLI

## Objetivo

Instalar o validar Qwen Code como coding worker.

## Pasos

1. detectar instalación existente;
2. comprobar versión;
3. instalar si falta;
4. configurar endpoint local;
5. probar modelo local;
6. probar sandbox;
7. probar headless;
8. probar salida capturable;
9. probar timeout;
10. probar resume/continue.

## Sandbox

```text
sandbox/qwen-code-basic/
```

Debe incluir:

- archivo;
- bug;
- test que falla;
- build simple.

## Condición de salida

```text
QWEN_CODE PASS
```

---

# 9. Fase 6 — Hermes Agent

## Objetivo

Instalar o validar Hermes como supervisor.

## Pasos

1. detectar instalación;
2. comprobar versión;
3. instalar si falta;
4. configurar Qwen local;
5. probar prompt;
6. probar tools;
7. probar sesión;
8. probar memoria;
9. probar recuperación básica.

## Condición de salida

```text
HERMES PASS
```

---

# 10. Fase 7 — Model Gateway / Inference Lock

## Objetivo

Garantizar que `--parallel 1` nunca se viole.

## Implementar

Uno de:

- mutex Windows;
- broker local;
- cola;
- proxy;
- lock robusto.

## Requisitos

- exclusión mutua;
- timeout;
- ownership;
- recuperación tras crash;
- logging.

## Pruebas

- dos solicitudes simultáneas;
- segunda espera;
- primera termina;
- lock se libera;
- crash no deja lock permanente.

## Condición de salida

```text
INFERENCE_LOCK PASS
```

---

# 11. Fase 8 — Wrapper Qwen Code

## Objetivo

Crear una interfaz estable para que Hermes invoque Qwen Code.

## Nombre provisional

```text
qwen_code_worker
```

## Entrada estructurada

```text
project
run_id
task_id
objective
acceptance criteria
constraints
timeout
```

## Salida estructurada

```text
status
summary
files changed
commands
tests
build
errors
evidence
next recommendation
```

## Condición de salida

```text
QWEN_WRAPPER PASS
```

---

# 12. Fase 9 — Delegación Hermes → Qwen Code

## Objetivo

Probar la relación supervisor/worker.

## Flujo

```text
Hermes planifica
↓
delega
↓
Qwen Code modifica
↓
test
↓
resultado estructurado
↓
Hermes verifica realidad
```

## Prueba mínima

Hermes debe delegar un bug del sandbox.

Qwen Code debe corregirlo.

Hermes debe verificar:

```text
Git diff
+
test PASS
```

## Condición de salida

```text
DELEGATION PASS
```

---

# 13. Fase 10 — Estructura `.autopilot`

## Objetivo

Crear memoria persistente por proyecto.

## Crear

```text
.autopilot/
  RUN-CONTRACT.yaml
  STATE.json
  STATE.md
  EVENTS.jsonl
  HEARTBEAT.json
  LOCK.json
  logs/
  evidence/
  checkpoints/
  reports/
```

## Implementar

- schema;
- atomic writes;
- previous state;
- IDs;
- timestamps;
- eventos.

## Condición de salida

```text
STATE PASS
```

---

# 14. Fase 11 — Recovery Protocol

## Objetivo

Poder reconstruir un run sin depender del chat.

## Implementar

```text
read contract
read state
read QWEN.md
git status
git diff
test/build verification
checkpoint
events
reconcile
continue
```

## Pruebas

- state atrasado;
- test desconocido;
- sesión nueva;
- worker muerto.

## Condición de salida

```text
RECOVERY PASS
```

---

# 15. Fase 12 — Sesiones y continuidad

## Objetivo

Usar correctamente sesiones de Qwen Code y Hermes.

## Qwen Code

- continue;
- resume;
- nueva sesión;
- session id en STATE.

## Hermes

- persistencia;
- historial;
- búsqueda;
- nueva sesión.

## Prueba

Cerrar y continuar varias veces sin repetir trabajo.

## Condición de salida

```text
CONTINUITY PASS
```

---

# 16. Fase 13 — Web Research

## Objetivo

Permitir investigación autónoma.

## Implementar

- búsqueda;
- extracción;
- priorización de fuentes;
- evidencia;
- timeout.

## Política

Preferir:

1. documentación oficial;
2. repositorios oficiales;
3. issues/releases;
4. fuentes técnicas fiables.

## Condición de salida

```text
WEB PASS
```

---

# 17. Fase 14 — Chrome dedicado + ChatGPT

## Objetivo

Crear consulta externa controlada.

## Crear

Perfil:

```text
HERMES-CHATGPT
```

Herramienta:

```text
consultar_chatgpt
```

## Implementar

- adopción de pestaña;
- domain lock;
- envío;
- espera;
- lectura;
- evidencia;
- presupuesto.

## Regla

```text
chatgpt.com ONLY
```

## Prueba

- consulta correcta;
- respuesta;
- evidencia;
- intento de escape de dominio;
- fake secret bloqueado.

## Condición de salida

```text
CHATGPT PASS
```

---

# 18. Fase 15 — Guardrails de seguridad

## Objetivo

Convertir la política de seguridad en controles técnicos.

## Implementar

- workspace boundary;
- canonical path;
- secret checks;
- Git policy;
- command policy;
- network policy;
- browser policy.

## Probar

- escritura externa;
- symlink escape;
- force push;
- destructive reset;
- comando Windows peligroso;
- fake secret.

## Condición de salida

```text
SECURITY PASS
```

---

# 19. Fase 16 — Anti-loop

## Objetivo

Evitar consumo infinito.

## Implementar

- cycle count;
- same failure count;
- no-progress count;
- error signature;
- progress fingerprint;
- escalation.

## Flujo

```text
retry
↓
change strategy
↓
web
↓
ChatGPT
↓
new session if useful
↓
STALLED
```

## Condición de salida

```text
ANTI_LOOP PASS
```

---

# 20. MACROFASE 7A — Capacidades Nativas de Hermes (Hermes Native Capabilities)

**Estado:** PASS (arquitectura congelada; 7A.1–7A.10 PASS; ChatGPT Idempotency PASS; regression gate PASS)

Esta macrofase incorpora formalmente las 14 capacidades nativas de Hermes Agent y el componente de hardening de ChatGPT, supeditadas al principio rector **"Prefer Native When Verified"** y a la **Deterministic Control Layer**.

Cada subfase debe superar sus pruebas funcionales, de seguridad, fallo, cleanup e integración antes de considerarse completa.

---

### Subfase 7A.1 — Memoria Persistente y Skills Reutilizables
- **Objetivo:** Habilitar la retención de lecciones aprendidas y decisiones de diseño en la memoria persistente de Hermes (Nivel 2) y cargar procedimientos operativos estandarizados (SOPs) desde `~/.hermes/skills/` como memoria procedimental.
- **Entregables:** Configuración de memoria persistente en Hermes, catálogo inicial de skills (testing, auditoría, refactorización), sanitizador de secretos `[REDACTED]`.
- **Condición de salida:** `7A.1 PASS` (Demostración de retención entre sesiones sin violar jerarquía de verdad).

---

### Subfase 7A.2 — Servidores MCP y Plugins
- **Objetivo:** Conectar herramientas externas mediante el protocolo MCP y plugins custom bajo el principio de mínima superficie de herramientas.
- **Entregables:** Configuración de clientes MCP en Hermes, allowlist estricta de tools, wrappers de timeout deterministas.
- **Condición de salida:** `7A.2 PASS` (Invocación de herramientas allowlisted y rechazo de tools no autorizadas).

---

### Subfase 7A.3 — Extracción Estructurada de Documentos
- **Estado:** PASS; inventario real y adapter gobernado en `evidence/phase-7a3/`; sin dependencias nuevas.
- **Objetivo:** Dotar a Hermes de la capacidad de ingerir especificaciones en formatos planos y no planos (Markdown, JSON, YAML, DOCX, XLSX, PDF, RTF) aplicando estrictamente `Prefer Native When Verified`: primero inventariar y probar las capacidades reales de `read_file` / extract de Hermes `v0.21.6` instalado; usar la capacidad nativa cuando soporte el formato; instalar una dependencia opcional únicamente para formatos/casos que la implementación nativa no resuelva (quedando librerías externas sólo como candidatas, no como requisito previo).
- **Entregables:** Inventario y validación del extractor nativo de Hermes `v0.21.6`, módulo de ingesta estructurada, y registro oficial en `config/VERSIONS.lock` de cualquier dependencia finalmente elegida durante `7A.3`.
- **Condición de salida:** `7A.3 PASS` (Extracción exitosa de especificaciones de proyecto en sandbox usando capacidad nativa verificada y fallback selectivo documentado, sin ejecución de macros maliciosas).

---

### Subfase 7A.4 — Browser Automation Nativo
- **Estado:** PASS; navegación/snapshot nativos, allowlist, política read-only, Job Object/timeout/cleanup e integración Hermes local en `evidence/phase-7a4/`.
- **Objetivo:** Activar la capacidad de navegación headless de Hermes para búsqueda e inspección técnica profunda.
- **Entregables:** Configuración del browser nativo, delimitación por domain allowlist, integración en la jerarquía (Nativo -> MCP -> Bridge ChatGPT).
- **Condición de salida:** `7A.4 PASS` (Extracción estructurada de documentación oficial con terminación limpia de procesos).

---

### Subfase 7A.5 — Bot Mode y Subagentes Jerárquicos
- **Objetivo:** Configurar la especialización de roles dentro de Hermes (Supervisor, Reviewer, Researcher) y delegación a subagentes acotados.
- **Entregables:** Perfiles de bots dedicados en Hermes, flujo de revisión independiente Supervisor -> Worker -> Reviewer, integración con `Inference Lock`.
- **Condición de salida:** `7A.5 PASS` (Flujo multi-rol completo con 100% de serialización bajo `--parallel 1`).

---

### Subfase 7A.6 — Git Worktrees Isolados
- **Objetivo:** Proveer aislamiento físico en `.autopilot-worktrees/task-<ID>/` para ejecución segura de refactorizaciones o workers secundarios.
- **Entregables:** Scripts de ciclo de vida de worktrees (create, isolate, diff review, clean), integración con Completion Gate.
- **Condición de salida:** `7A.6 PASS` (Aislamiento verificado, merge controlado tras revisión y cleanup forzado sin directorios huérfanos).

---

### Subfase 7A.7 — Cron y Jobs sin Agente
- **Objetivo:** Validar de forma autónoma Hermes Cron/Routines (creación, listado, pausa, reanudación), `no-agent jobs`, garantía de **0 inferencias LLM** en tareas sin agente, seguridad y cleanup, sin depender todavía del Runner de la Macrofase 7B.
- **Entregables:** Rutinas de Cron validadas (create/list/pause/resume/cleanup) y catálogo de scripts deterministas de mantenimiento (`no-agent jobs`) con 0 inferencias LLM.
- **Condición de salida:** `7A.7 PASS` (Validación de ciclo de vida de Cron/Routines, ejecución de `no-agent job` con 0 inferencias LLM, seguridad y cleanup; la integración completa `Cron → Runner → Watchdog → RUN-CONTRACT` se valida obligatoriamente en Macrofase 7B).

---

### Subfase 7A.8 — Web Dashboard (Superficie Administrativa y Observabilidad)
- **Objetivo:** Configurar y asegurar el Hermes Web Dashboard como panel de observabilidad y **superficie administrativa** local (capaz de gestionar configuración, MCP, memoria, cron, skills y otras opciones), completamente desacoplado del ciclo de vida del Runner.
- **Entregables:** Configuración del Web Dashboard en su default nativo `host: 127.0.0.1` y `port: 9119` (puerto configurable), bind exclusivo en loopback y controles de seguridad para que no pueda relajar `config/security.yaml` ni `RUN-CONTRACT.yaml`.
- **Condición de salida:** `7A.8 PASS` (Verificación en `127.0.0.1:9119` configurable, bind loopback estricto, revisión de seguridad como superficie administrativa e independencia total respecto al Runner).

---

### Subfase 7A.9 — Gateway Multiplataforma
- **Objetivo:** Habilitar la transmisión unidireccional de alertas críticas hacia canales de mensajería (Telegram/Discord/Slack).
- **Entregables:** Adaptador de notificaciones salientes para eventos `COMPLETED`, `FAILED`, `BLOCKED`, `STALLED`.
- **Condición de salida:** `7A.9 PASS` (Recepción exitosa de alertas salientes y bloqueo de comandos externos no autorizados).

---

### Subfase 7A.10 — Actualización Automática Controlada
- **Objetivo:** Implementar el pipeline de actualización de Hermes Agent bajo entorno canary aislado con capacidad de rollback automático.
- **Entregables:** Scripts de staging canary en `sandbox/canary-update/`, verificación de hash SHA-256, suite de regresión y rollback.
- **Condición de salida:** `7A.10 PASS` (Validación de promoción exitosa y reversión inmediata ante inyección de fallo en canary).

---

### Hardening Adicional — Idempotencia del Bridge ChatGPT (PASS)
- **Estado previo a 7A:** No implementado ni probado todavía (`ENABLED: NO`, `CONFIGURED: NO`, `TESTED: NO`, `PRODUCTION_READY: NO`).
- **Objetivo:** Implementar deduplicación por `consultation_id` y tracking estricto de turnos en `tools/chatgpt-bridge.js`.
- **Entregables:** Manejo de `consultation_id`, retorno determinista de `ALREADY_SENT` ante reintentos y auditoría de incremento de turnos (`+1` user, `+1` assistant).
- **Condición de salida:** `CHATGPT_IDEMPOTENCY PASS` (Superación de la prueba futura obligatoria `T-CHATGPT-010`).

---

# 21. MACROFASE 7B — Runner Autónomo Nocturno

Agrupa las fases de ciclo de vida determinista, supervisión y cierre seguro, incluyendo como criterio obligatorio la integración completa `Cron → Runner → Watchdog → RUN-CONTRACT`:

---

## Fase 17 — Runner

## Objetivo

Crear supervisor determinista del ciclo de vida.

## Responsabilidades

- leer config;
- validar proyecto y exigir `RUN-CONTRACT.yaml` válido;
- run_id;
- iniciar llama;
- health;
- iniciar Hermes;
- integración completa `Cron → Runner → Watchdog → RUN-CONTRACT` (`T-RUN-009`);
- heartbeat;
- timeout;
- watchdog;
- cleanup;
- report.

## Condición de salida

```text
RUNNER PASS (incluyendo integración obligatoria Cron → Runner → Watchdog → RUN-CONTRACT)
```

---

# 21. Fase 18 — Watchdog

## Objetivo

Detectar y recuperar fallos.

## Vigilar

```text
llama
Hermes
Qwen Code
heartbeat
locks
timeouts
no-progress
```

## Probar

- matar Qwen Code;
- matar llama;
- matar Hermes;
- stale heartbeat.

## Condición de salida

```text
WATCHDOG PASS
```

---

# 22. Fase 19 — Launcher único

## Objetivo

Simplificar uso.

## Crear

```text
INICIAR-DESARROLLADOR-AUTONOMO.bat
DETENER-DESARROLLADOR-AUTONOMO.bat
```

## Regla

Los `.bat` no contienen la lógica compleja.

Sólo invocan Runner/stop seguro.

## Condición de salida

```text
LAUNCHER PASS
```

---

# 23. Fase 20 — Completion Gate

## Objetivo

Impedir falsos “terminado”.

## Verificar

```text
objective
acceptance criteria
tests
build
artifacts
git diff
pending
STATE consistency
```

## Condición

Sólo después:

```text
COMPLETED
```

## Condición de salida

```text
COMPLETION_GATE PASS
```

---

# 24. Fase 21 — Reportes

## Objetivo

Crear informes útiles para el usuario.

## Generar

```text
FINAL.md
BLOCKED.md
FAILURE.md
STALLED.md
```

según corresponda.

## FINAL debe incluir

- resumen;
- archivos;
- commits;
- tests;
- build;
- decisiones;
- errores;
- recoveries;
- web;
- ChatGPT;
- pendientes;
- duración;
- estado final.

## Condición de salida

```text
REPORTING PASS
```

---

# 25. Fase 22 — Cleanup garantizado

## Objetivo

Evitar procesos huérfanos.

## Implementar

equivalente a:

```text
finally
```

## Cerrar

- worker Qwen;
- procesos auxiliares;
- llama-server;
- locks.

## Preservar

- logs;
- STATE;
- reportes;
- checkpoints.

## Prueba

Success + fail + timeout + blocked.

## Condición de salida

```text
CLEANUP PASS
```

---

# 22. MACROFASE 8 — Validación Final

Agrupa las fases de prueba en sandbox integral, validaciones prolongadas autónomas y auditoría final:

---

## Fase 23 — Sandbox integral

## Objetivo

Probar el sistema completo sin arriesgar proyectos reales.

## Sandbox debe contener

- bug;
- feature;
- test;
- build;
- documentación incompleta;
- problema que requiera web;
- problema que requiera ChatGPT;
- operación prohibida;
- recuperación simulada.

## Condición de salida

```text
SANDBOX PASS
```

---

# 27. Fase 24 — End-to-End corto

## Objetivo

Ejecutar el flujo completo.

## Duración esperada

```text
15-45 minutos
```

## Flujo obligatorio

```text
start
preflight
approve once
llama
Hermes
Qwen Code
fail
fix
web
checkpoint
recovery
ChatGPT
Completion Gate
report
cleanup
```

## Condición de salida

```text
E2E SHORT PASS
```

---

# 28. Fase 25 — Prueba 2 horas

## Objetivo

Validar estabilidad inicial.

## Debe incluir

- varios ciclos;
- varias tareas;
- checkpoints;
- al menos una recuperación;
- logs;
- consumo de recursos.

## Requisito

```text
0 intervención humana
```

después del inicio.

## Condición de salida

```text
2H PASS
```

---

# 29. Fase 26 — Auditoría

## Objetivo

Revisar sistema completo antes de confiar proyectos reales.

## Auditar

- arquitectura;
- seguridad;
- memoria;
- locks;
- recovery;
- anti-loop;
- logs;
- Completion Gate;
- cleanup.

Puede utilizarse Antigravity y opcionalmente una segunda revisión independiente.

## Condición de salida

```text
AUDIT PASS
```

---

# 30. Fase 27 — Piloto con proyecto real no crítico

## Objetivo

Validar comportamiento fuera del sandbox.

Elegir un proyecto:

- respaldado;
- no productivo;
- reversible.

## Requisitos

- rama separada;
- sin push;
- Completion Gate;
- revisión humana final.

## Condición de salida

```text
REAL PILOT PASS
```

---

# 31. Fase 28 — Prueba nocturna 6-8 horas

## Objetivo

Validar el objetivo final del proyecto.

## Duración

```text
6-8 horas
```

## Esperado

- sin intervención;
- sin loops;
- memoria consistente;
- recuperación;
- recursos estables;
- informe final;
- cleanup.

## Condición de salida

```text
NIGHT MODE PASS
```

---

# 32. Versión 1.0

Sólo declarar:

```text
DESARROLLADOR AUTÓNOMO v1.0 READY
```

cuando exista evidencia de:

```text
LLAMA PASS
QWEN_CODE PASS
HERMES PASS
INFERENCE_LOCK PASS
DELEGATION PASS
STATE PASS
RECOVERY PASS
CONTINUITY PASS
WEB PASS
CHATGPT PASS
SECURITY PASS
ANTI_LOOP PASS
RUNNER PASS
WATCHDOG PASS
COMPLETION_GATE PASS
REPORTING PASS
CLEANUP PASS
E2E SHORT PASS
2H PASS
AUDIT PASS
REAL PILOT PASS
```

La prueba nocturna 6-8h completa la validación operacional final.

---

# 33. Estado de fases

Antigravity debe mantener una tabla:

| Fase | Estado | Evidencia |
|---|---|---|
| 0 Docs | PASS/FAIL | ... |
| 1 Inventory | PASS/FAIL | ... |
| 2 Backup | PASS/FAIL | ... |
| ... | ... | ... |

Guardar en:

```text
docs/IMPLEMENTATION-STATUS.md
```

---

# 34. Dependencias entre fases

No ejecutar fases que dependen de componentes no validados.

Ejemplo:

```text
NO probar Hermes→Qwen
si Qwen Code todavía FAIL
```

---

# 35. Corrección de fase

Si una fase falla:

```text
FAIL
↓
diagnóstico
↓
corrección
↓
retest
```

No avanzar dejando fallos críticos pendientes.

---

# 36. Cambios de arquitectura

Si durante implementación aparece una limitación real:

Antigravity debe:

1. registrar evidencia;
2. identificar documento afectado;
3. proponer cambio;
4. esperar aprobación si altera arquitectura base;
5. actualizar documentación;
6. continuar.

---

# 37. Entregables finales

Al terminar implementación:

```text
config/
runner/
scripts/
tools/
tests/
sandbox/
backups/
docs/
```

más:

```text
INICIAR-DESARROLLADOR-AUTONOMO.bat
DETENER-DESARROLLADOR-AUTONOMO.bat
```

y documentación actualizada.

---

# 38. Regla para Antigravity

Antigravity debe considerar este Roadmap como el orden operativo inicial.

Puede subdividir una fase en subtareas.

No debe:

- saltar validaciones;
- fusionar todas las fases en una sola ejecución opaca;
- ocultar fallos;
- marcar PASS sin evidencia;
- cambiar arquitectura principal silenciosamente.

El objetivo no es instalar rápido.

El objetivo es terminar con un sistema que pueda trabajar solo durante horas y que pueda recuperarse cuando algo falla.

Actualización operativa 2026-10-13T16:00:00.067794-03:00: Macrofase7B IN_PROGRESS; F17 (Runner) PASS; evidence/phase-17/. 7A permanece PASS.

Actualización operativa 2026-10-13T16:18:30.312213-03:00: Macrofase7B IN_PROGRESS; F18 (Watchdog) PASS; evidence/phase-18/. 7A permanece PASS.

Actualización operativa 2026-10-13T16:23:57.480503-03:00: Macrofase7B IN_PROGRESS; F19 (Launcher) PASS; evidence/phase-19/. 7A permanece PASS.

Actualización operativa 2026-10-13T16:37:16.325404-03:00: Macrofase7B IN_PROGRESS; F20 (Completion Gate) PASS; evidence/phase-20/. 7A permanece PASS.

Actualización operativa 2026-10-13T16:40:23.240900-03:00: Macrofase7B IN_PROGRESS; F21 (Reportes) PASS; evidence/phase-21/. 7A permanece PASS.

Actualización operativa 2026-10-13T16:58:45.255234-03:00: Macrofase7B IN_PROGRESS; F22 (Cleanup garantizado) PASS; evidence/phase-22/. 7A permanece PASS.

Cierre operativo 7B: F17–F22 PASS, incluyendo T-RUN-009, gate, reportes y cleanup; E2E real con un restart acotado y regression smoke PASS. Macrofase 8 PENDING, sin ejecución.
