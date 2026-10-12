# 03 — Memoria y continuidad
## Proyecto: Desarrollador Autónomo

**Versión:** 2.0  
**Estado:** APROBADO / FROZEN PARA IMPLEMENTACIÓN DE MACROFASE 7A  
**Arquitectura base:** Hermes Agent + Qwen Code CLI + Qwen local mediante llama.cpp

---

# 1. Objetivo

Garantizar que el sistema pueda continuar un proyecto durante horas, días o múltiples sesiones sin depender de una conversación infinita.

La continuidad debe sobrevivir a:

- compactación de contexto;
- cierre de Qwen Code;
- cierre de Hermes;
- reinicio de llama.cpp;
- nueva sesión;
- crash;
- reinicio de Windows;
- cambio de estrategia;
- ejecución nocturna interrumpida.

La regla principal es:

> **El proyecto debe poder reconstruir su propio estado sin depender de que el modelo recuerde todo.**

---

# 2. Principio de memoria: Modelo de 3 Niveles y Memoria Procedimental

La memoria del sistema se organiza formalmente en tres niveles de persistencia operativa y una categoría procedimental:

```text
┌────────────────────────────────────────────────────────────────────────┐
│             NIVEL 1 — MEMORIA OPERATIVA AUTORITATIVA                   │
│  - Filesystem y código fuente real    - RUN-CONTRACT.yaml              │
│  - Git (árbol de trabajo, commits)    - EVENTS.jsonl (append-only)     │
│  - Tests y builds ejecutados en vivo  - Checkpoints inmutables         │
│  - STATE.json (fuente de verdad canónica del estado de tareas)         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Prevalece sobre cualquier nivel
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│             NIVEL 2 — MEMORIA PERSISTENTE HERMES                       │
│  - Lecciones aprendidas y errores resueltos en ejecuciones previas     │
│  - Preferencias técnicas y decisiones arquitectónicas estables         │
│  - Contexto semántico acumulado del proyecto                           │
│  - Patrones exitosos de implementación                                 │
│  * RESTRICCIÓN: Jamás puede dar por hecho el éxito de un test, un      │
│    build o el contenido de un archivo; eso se verifica siempre en N1.  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│             NIVEL 3 — MEMORIA DE SESIÓN (AUXILIAR Y VOLÁTIL)           │
│  - Conversación activa de Hermes y Qwen Code                          │
│  - Razonamiento transitorio en ventana de contexto                     │
│  * Puede compactarse, reiniciarse o descartarse por completo sin       │
│    comprometer la continuidad ni el estado del proyecto.               │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│             MEMORIA PROCEDIMENTAL (SKILLS REUTILIZABLES)               │
│  - Procedimientos operativos estandarizados (SOPs en Markdown)         │
│  - Metodologías de diagnóstico, auditoría de migraciones SQL, etc.     │
│  * Ciclo de promoción: Experiencia repetida → Procedimiento validado → │
│    Auditoría humana / seguridad → Skill reusable (~/.hermes/skills/). │
│  * RESTRICCIÓN: Un Skill no puede modificar políticas de seguridad.   │
└────────────────────────────────────────────────────────────────────────┘
```

---

# 3. Jerarquía de verdad

En caso de discrepancia o contradicción entre componentes, prevalece este orden estricto:

1. Estado real del filesystem (archivos en disco);
2. Repositorio Git local (`git status`, `git diff`, commits);
3. Salida de tests y builds ejecutados objetivamente;
4. Artefactos verificables generados;
5. `.autopilot/STATE.json` (estado canónico estructurado);
6. `.autopilot/RUN-CONTRACT.yaml` (contrato de ejecución);
7. `.autopilot/STATE.md` (resumen visual para humanos);
8. `.autopilot/EVENTS.jsonl` (registro cronológico monotónico);
9. Logs de ejecución en `.autopilot/logs/`;
10. `QWEN.md` y memoria de instrucciones del repositorio;
11. Nivel 2: Memoria persistente nativa de Hermes;
12. Nivel 3: Historial de sesiones de Hermes o Qwen Code;
13. Memoria conversacional / razonamiento en contexto.

### Ejemplo canónico:
Si la memoria persistente o `STATE.md` dice:
```text
build: PASS
```
pero la ejecución real de `npm run build` falla en el filesystem:
```text
REALIDAD = FAIL
```
El sistema reconcilia de inmediato el estado, imponiendo la realidad física (Nivel 1) por encima de cualquier memoria previa.

---

# 4. Archivos principales de memoria

Cada proyecto autónomo debe contener:

```text
PROJECT_ROOT/
│
├── QWEN.md
│
└── .autopilot/
    ├── RUN-CONTRACT.yaml
    ├── STATE.json
    ├── STATE.md
    ├── EVENTS.jsonl
    ├── HEARTBEAT.json
    ├── LOCK.json
    │
    ├── logs/
    ├── evidence/
    ├── checkpoints/
    └── reports/
```

---

# 5. RUN-CONTRACT.yaml

Es el contrato de una ejecución.

Se genera después del preflight y antes de comenzar el modo autónomo.

Debe ser relativamente inmutable durante esa ejecución.

Ejemplo:

```yaml
run_id: "RUN-2026-10-11-001"

project_path: "C:\\Proyectos\\PEDIDOS"

objective: >
  Implementar autenticación OAuth y verificarla.

acceptance_criteria:
  - "Login Google funciona"
  - "Tests pasan"
  - "Build pasa"

autonomy:
  unattended: true
  ask_after_start: false

limits:
  max_cycles: 20
  max_no_progress_cycles: 3
  max_same_failure: 3
  max_chatgpt_queries: 5

git:
  push: false
  force_push: false

security:
  allow_outside_workspace: false
```

---

# 6. STATE.json

`STATE.json` es la fuente operativa principal para máquinas.

Debe mantenerse pequeño, claro y actualizado.

No debe convertirse en un log histórico.

---

## 6.1 Esquema lógico mínimo

```json
{
  "schema_version": "1.0",
  "run_id": "RUN-2026-10-11-001",
  "project_path": "C:\\Proyectos\\PEDIDOS",
  "status": "RUNNING",
  "cycle": 7,

  "objective": "Implementar OAuth",

  "milestones": [
    {
      "id": "M1",
      "title": "Backend OAuth",
      "status": "COMPLETED"
    }
  ],

  "active_task": {
    "id": "AUTH-04",
    "title": "Corregir renovación de token",
    "status": "RUNNING"
  },

  "completed_tasks": [],
  "pending_tasks": [],

  "decisions": [],

  "last_failure": {
    "signature": "invalid_grant",
    "attempts": 2
  },

  "verification": {
    "tests": "PASS",
    "build": "FAIL"
  },

  "files_modified": [],

  "next_action": "Investigar refresh token y corregir",

  "progress_score": 63,

  "sessions": {
    "hermes": null,
    "qwen": null
  },

  "timestamps": {
    "created_at": "",
    "updated_at": ""
  }
}
```

---

# 7. Estados permitidos

El campo `status` sólo puede tener:

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

No inventar estados nuevos sin actualizar el esquema.

---

# 8. STATE.md

`STATE.md` es una representación humana.

Debe poder ser leído rápidamente por:

- usuario;
- Hermes;
- Qwen Code;
- auditor;
- Antigravity.

Formato recomendado:

```markdown
# Estado actual

## Objetivo

## Estado

## Hitos completados

## Tarea activa

## Decisiones importantes

## Último error

## Tests

## Build

## Archivos modificados

## Próximo paso

## Pendientes

## Bloqueos
```

---

# 9. Regla STATE.json vs STATE.md

`STATE.json` es la versión canónica.

`STATE.md` es una vista humana.

Si difieren:

```text
STATE.json
    ↓
regenerar
STATE.md
```

Nunca al revés automáticamente sin validación.

---

# 10. QWEN.md

Debe contener conocimiento relativamente estable.

Ejemplos:

- arquitectura del proyecto;
- convenciones;
- comandos;
- restricciones;
- rutas;
- cómo ejecutar tests;
- cómo ejecutar build;
- qué no debe tocarse;
- política Git.

No debe incluir:

- ciclo actual;
- último error temporal;
- lista diaria de tareas;
- progreso de la noche.

Eso pertenece a `STATE`.

---

# 11. Hermes memory

Hermes puede utilizar su memoria persistente para:

- preferencias;
- entorno;
- información útil recurrente;
- convenciones.

Pero no debe usarse como reemplazo de `STATE.json`.

La memoria interna de Hermes es auxiliar.

---

# 12. Qwen auto-memory

Qwen Code puede conservar información aprendida entre sesiones.

Se permite utilizarla.

Pero:

- no es fuente principal;
- no debe contener secretos;
- no debe reemplazar STATE;
- no debe ser necesaria para recuperar una ejecución.

---

# 13. EVENTS.jsonl

Es la caja negra cronológica del sistema.

Formato:

una línea JSON por evento.

Ejemplo:

```json
{"ts":"...","cycle":3,"type":"TASK_START","task_id":"AUTH-04"}
{"ts":"...","cycle":3,"type":"FILE_MODIFIED","path":"src/auth.ts"}
{"ts":"...","cycle":3,"type":"TEST","command":"npm test","result":"FAIL"}
{"ts":"...","cycle":3,"type":"ERROR","signature":"invalid_grant"}
{"ts":"...","cycle":3,"type":"WEB_SEARCH","query":"OAuth invalid_grant"}
{"ts":"...","cycle":3,"type":"CHATGPT_QUERY","id":"CHATGPT-002"}
{"ts":"...","cycle":3,"type":"TEST","command":"npm test","result":"PASS"}
{"ts":"...","cycle":3,"type":"CHECKPOINT","id":"CP-003"}
```

---

# 14. Eventos mínimos

Tipos recomendados:

```text
RUN_CREATED
RUN_STARTED
RUN_STOPPED

SESSION_STARTED
SESSION_RESUMED
SESSION_REPLACED

TASK_CREATED
TASK_STARTED
TASK_COMPLETED
TASK_FAILED

FILE_CREATED
FILE_MODIFIED
FILE_DELETED

COMMAND
TEST
BUILD

ERROR
WARNING

WEB_SEARCH
WEB_RESULT

CHATGPT_QUERY
CHATGPT_RESULT

DECISION

CHECKPOINT

RECOVERY_START
RECOVERY_SUCCESS
RECOVERY_FAILED

NO_PROGRESS

COMPLETION_GATE_START
COMPLETION_GATE_PASS
COMPLETION_GATE_FAIL

CLEANUP_START
CLEANUP_END
```

---

# 15. Logs

Los logs pueden ser grandes.

Por eso no deben copiarse completos al contexto.

Se guardan en:

```text
.autopilot/logs/
```

Ejemplo:

```text
runner/
hermes/
qwen/
llama/
tests/
builds/
```

Los agentes deben leer:

- fragmentos relevantes;
- últimas líneas;
- búsquedas específicas.

No reinyectar logs completos sin necesidad.

---

# 16. Evidence

Todo resultado externo importante debe quedar persistido.

```text
.autopilot/evidence/
```

Subcarpetas:

```text
web/
chatgpt/
tests/
artifacts/
```

Ejemplos:

```text
web/WEB-003.md
chatgpt/CHATGPT-002.md
tests/TEST-018.json
artifacts/screenshot-login.png
```

---

# 17. Checkpoints

Los checkpoints son puntos de recuperación consistentes.

Debe crearse un checkpoint:

- al completar un hito;
- antes de una nueva sesión;
- antes de cambiar estrategia;
- antes de una operación importante;
- antes del Completion Gate.

---

## 17.1 Contenido mínimo

```text
checkpoint id
timestamp
run_id
cycle
task
STATE.json snapshot
STATE.md snapshot
git status
git diff summary
tests status
build status
session IDs
next action
```

---

# 18. Carpeta checkpoints

Formato sugerido:

```text
.autopilot/checkpoints/
  CP-0001/
  CP-0002/
  CP-0003/
```

Cada checkpoint debe ser inmutable.

No sobrescribir checkpoints anteriores.

---

# 19. Frecuencia de persistencia

Actualizar `STATE.json`:

- al iniciar tarea;
- después de cambios importantes;
- después de test/build;
- al detectar error importante;
- al cambiar estrategia;
- al finalizar tarea;
- antes de nueva sesión;
- antes de cleanup.

No esperar hasta el final de la ejecución.

---

# 20. Escritura atómica

Para evitar corrupción:

```text
STATE.json.tmp
   ↓
validar JSON
   ↓
rename/replace
   ↓
STATE.json
```

La actualización debe ser atómica cuando sea posible.

Nunca dejar un JSON parcialmente escrito.

---

# 21. Backup de STATE

Mantener como mínimo:

```text
STATE.json
STATE.previous.json
```

Opcionalmente:

```text
STATE.history/
```

con snapshots limitados.

---

# 22. Recovery Protocol

Ante:

- crash;
- reinicio;
- nueva sesión;
- cambio de worker;
- contexto contaminado;

ejecutar:

```text
1. identificar project root
2. validar RUN-CONTRACT
3. leer STATE.json
4. validar schema
5. leer STATE.md
6. leer QWEN.md
7. git status
8. git diff
9. revisar tests/build relevantes
10. revisar último checkpoint
11. revisar últimos EVENTS
12. comparar estado persistido con realidad
13. reconciliar
14. recuperar sesión si conviene
15. continuar
```

---

# 23. Reconciliación

El estado persistido puede estar atrasado respecto del filesystem.

Ejemplo:

```text
STATE:
archivo A no modificado

Git:
archivo A modificado
```

El sistema debe investigar antes de continuar.

No sobrescribir inmediatamente.

---

# 24. Caso: crash durante edición

Si Qwen Code muere después de modificar archivos pero antes de actualizar STATE:

```text
Recovery
  ↓
git status / diff
  ↓
detectar cambio
  ↓
tests
  ↓
determinar intención probable
  ↓
actualizar STATE
  ↓
continuar
```

---

# 25. Caso: crash durante test

Si el test quedó incompleto:

- no asumir PASS;
- no asumir FAIL;
- estado = UNKNOWN;
- ejecutar nuevamente.

---

# 26. Caso: crash de llama.cpp

El estado del proyecto no depende de llama.cpp.

Runner:

```text
detecta caída
  ↓
EVENTS
  ↓
reinicia llama
  ↓
health
  ↓
RECOVERING
  ↓
Recovery Protocol
```

---

# 27. Caso: crash de Hermes

Runner detecta ausencia de heartbeat/proceso.

Debe:

```text
reiniciar Hermes
  ↓
nueva sesión o resume
  ↓
Recovery Protocol
  ↓
continuar
```

---

# 28. Caso: crash de Qwen Code

Hermes/Runner:

```text
registrar fallo
  ↓
revisar session id
  ↓
intentar resume
  ↓
si no funciona:
nueva sesión
  ↓
Recovery Protocol
```

---

# 29. Sesiones Qwen Code

Guardar ID de sesión activa en STATE.

Ejemplo:

```json
"sessions": {
  "qwen": {
    "id": "...",
    "status": "ACTIVE",
    "started_at": "..."
  }
}
```

---

# 30. Política de resume Qwen

Continuar sesión cuando:

- sigue coherente;
- contexto no está contaminado;
- no repite trabajo;
- tiene información útil.

Crear nueva sesión cuando:

- compresiones reiteradas;
- comportamiento circular;
- contradicciones;
- fase nueva grande;
- contexto irrelevante acumulado.

---

# 31. Sesiones Hermes

Guardar:

- ID;
- nombre;
- relación con run_id;
- fecha;
- estado.

Hermes puede usar historial y búsqueda para recuperar decisiones históricas.

---

# 32. Nueva sesión no significa pérdida

Cuando se crea una nueva sesión:

```text
sesión vieja
   ↓
checkpoint
   ↓
STATE
   ↓
EVENTS
   ↓
nueva sesión
   ↓
Recovery Protocol
   ↓
continúa
```

---

# 33. Compactación

La compactación es aceptable.

No debe considerarse fallo.

Pero antes o después de compactaciones importantes, el sistema debe asegurar que:

- decisiones críticas estén en STATE;
- tarea activa esté registrada;
- próximo paso esté registrado;
- tests/build estén registrados.

---

# 34. Qué información debe persistirse siempre

Nunca depender del chat para recordar:

- objetivo;
- criterios;
- arquitectura elegida;
- restricciones;
- decisiones críticas;
- tareas terminadas;
- tarea activa;
- errores repetidos;
- intentos fallidos relevantes;
- tests;
- build;
- archivos modificados;
- próximo paso;
- bloqueos;
- session ids.

---

# 35. Qué información NO debe inflar STATE

No guardar en STATE:

- logs completos;
- código fuente completo;
- respuestas web completas;
- dumps enormes;
- stack traces completos;
- diffs completos.

Guardar referencia:

```text
"evidence": "evidence/tests/TEST-18.txt"
```

---

# 36. Resúmenes de sesión

Al cerrar una sesión Qwen o Hermes:

generar resumen estructurado:

```text
SESSION SUMMARY

- objetivo trabajado
- tareas terminadas
- tareas pendientes
- decisiones
- archivos
- tests
- errores
- próximo paso
```

Guardar en:

```text
.autopilot/checkpoints/<id>/session-summary.md
```

---

# 37. Detección de repetición

El sistema debe poder detectar que una nueva sesión está repitiendo trabajo ya hecho.

Comparar:

- archivos inspeccionados;
- comandos;
- errores;
- diff;
- tarea activa;
- EVENTS recientes.

Si hay repetición sin nueva evidencia:

```text
NO_PROGRESS
```

---

# 38. Error signature

Errores repetidos deben tener firma estable.

Ejemplo:

```text
ERR-AUTH-INVALID-GRANT
```

o hash basado en:

- comando;
- código;
- mensaje normalizado.

Esto permite contar intentos reales.

---

# 39. Progress fingerprint

Cada ciclo puede producir un fingerprint:

```text
hash(
  task_id
  git_diff_hash
  test_state
  build_state
  error_signature
)
```

Si el fingerprint no cambia durante varios ciclos:

```text
NO_PROGRESS
```

---

# 40. Heartbeat

Archivo:

```text
.autopilot/HEARTBEAT.json
```

Ejemplo:

```json
{
  "run_id": "...",
  "timestamp": "...",
  "status": "RUNNING",
  "cycle": 7,
  "task_id": "AUTH-04",
  "hermes_pid": 1234,
  "qwen_pid": 5678,
  "llama_health": "OK"
}
```

Debe actualizarse periódicamente.

---

# 41. Run lock

Archivo:

```text
.autopilot/LOCK.json
```

Previene dos runs sobre el mismo proyecto.

Debe incluir:

- run_id;
- pid;
- started_at;
- heartbeat;
- hostname.

Si lock está obsoleto:

no borrarlo ciegamente.

Primero comprobar proceso/heartbeat.

---

# 42. Reinicio de Windows

Después de reinicio:

el sistema debe poder detectar un run incompleto.

Ejemplo:

```text
STATE.status = RUNNING
pero no existen procesos
```

Debe ofrecer/ejecutar:

```text
RECOVER RUN
```

según política.

---

# 43. Estado incompleto al arrancar

Si encuentra:

```text
RUNNING
RECOVERING
VERIFYING
CLEANING_UP
```

de una ejecución anterior:

debe revisar consistencia antes de crear un nuevo run.

---

# 44. Integridad

Al arrancar:

validar:

- JSON válido;
- schema version soportado;
- run_id consistente;
- project path consistente;
- archivos esenciales presentes.

Si falla:

```text
RECOVERY_REQUIRED
```

No continuar silenciosamente.

---

# 45. Versionado de esquema

`STATE.json` debe incluir:

```json
"schema_version": "1.0"
```

Cambios incompatibles requieren migración.

No romper estados existentes.

---

# 46. Timestamps

Usar formato ISO 8601.

Ejemplo:

```text
2026-10-11T22:15:30-03:00
```

---

# 47. IDs

Formato sugerido:

```text
RUN-20261011-001
TASK-001
CP-001
WEB-001
CHATGPT-001
TEST-001
```

Deben ser únicos dentro del run.

---

# 48. Retención

No borrar automáticamente la evidencia del run recién terminado.

Política inicial:

- conservar logs;
- conservar reports;
- conservar checkpoints;
- permitir limpieza manual posterior.

---

# 49. Informe final y memoria

Al completar:

```text
STATE.status = COMPLETED
```

y crear:

```text
.autopilot/reports/FINAL.md
```

Después:

- cerrar procesos;
- mantener archivos de estado;
- no borrar historial.

---

# 50. Informe de bloqueo

Si termina en:

```text
BLOCKED_REQUIRES_HUMAN
```

crear:

```text
BLOCKED.md
```

con:

- bloqueo;
- por qué no pudo decidir;
- opciones;
- riesgo;
- último estado válido;
- cómo continuar.

---

# 51. Informe de fallo

Si:

```text
FAILED
```

crear:

```text
FAILURE.md
```

incluyendo:

- causa;
- último checkpoint;
- logs relevantes;
- estado Git;
- pasos de recuperación.

---

# 52. Regla de oro

Si una pieza de información es necesaria para continuar correctamente mañana:

**no debe existir únicamente dentro de una conversación.**

Debe persistirse en alguno de:

```text
STATE
QWEN.md
EVENTS
evidence
Git
tests
checkpoint
```

---

# 53. Prueba obligatoria de continuidad

La arquitectura de memoria sólo se considera válida si supera esta prueba:

```text
1. iniciar tarea
2. modificar archivos
3. test falla
4. corregir parcialmente
5. crear checkpoint
6. matar Qwen Code
7. reanudar
8. continuar
9. matar llama.cpp
10. reiniciar llama
11. continuar
12. crear nueva sesión Qwen
13. continuar
14. crear nueva sesión Hermes
15. continuar
16. completar
17. validar
```

El sistema no debe repetir desde cero ninguna fase ya validada.

---

# 54. Prueba de compactación

Durante un sandbox largo:

- forzar o provocar compactación;
- verificar que las decisiones críticas siguen accesibles;
- comprobar que STATE mantiene continuidad;
- comprobar que Qwen no vuelve a realizar tareas ya cerradas.

---

# 55. Prueba de corrupción

Simular:

- `STATE.json` inválido;
- STATE desactualizado;
- lock obsoleto;
- test inconsistente.

Esperado:

- detectar;
- no continuar ciegamente;
- recuperar desde checkpoint/Git;
- registrar incidente.

---

# 56. Criterio de éxito

Este subsistema de memoria se considera correcto cuando:

- una sesión puede cerrarse y retomarse;
- una nueva sesión puede continuar;
- un crash puede recuperarse;
- un reinicio no pierde progreso;
- una compactación no obliga a recomenzar;
- un estado inconsistente se detecta;
- Git/tests pueden corregir STATE;
- nunca se depende únicamente del chat.

---

# 57. Regla para Antigravity

Antigravity debe implementar esta capa de persistencia antes de considerar terminada la autonomía nocturna.

No debe reemplazarla por “memoria del agente” únicamente.

Si una función nativa de Hermes o Qwen Code puede reforzar esta arquitectura:

puede utilizarse.

Pero no debe eliminar:

- `STATE.json`;
- `STATE.md`;
- `EVENTS.jsonl`;
- checkpoints;
- Git/tests como evidencia;
- Recovery Protocol.

