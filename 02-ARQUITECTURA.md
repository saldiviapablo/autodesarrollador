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
│                                                             │
│  Selecciona proyecto + objetivo + aprobación inicial       │
└────────────────────────────┬────────────────────────────────┘
                             │
                             v
┌─────────────────────────────────────────────────────────────┐
│                     HERMES AGENT                            │
│                  Supervisor / Orquestador                   │
│                                                             │
│  - preflight                                                │
│  - planificación                                            │
│  - investigación web                                       │
│  - memoria/sesiones                                        │
│  - control de progreso                                     │
│  - consulta ChatGPT                                        │
│  - delegación                                              │
│  - validación                                              │
└────────────────────────────┬────────────────────────────────┘
                             │
                             │ delega tareas de programación
                             v
┌─────────────────────────────────────────────────────────────┐
│                    QWEN CODE CLI                            │
│                    Coding Worker                            │
│                                                             │
│  - inspección de repo                                      │
│  - edición de archivos                                     │
│  - terminal                                                │
│  - tests                                                   │
│  - builds                                                  │
│  - Git local                                               │
│  - diagnóstico                                             │
│  - autocorrección                                          │
└────────────────────────────┬────────────────────────────────┘
                             │
                             │ inferencia
                             v
┌─────────────────────────────────────────────────────────────┐
│                       LLAMA.CPP                             │
│                                                             │
│  Qwen3.6-35B-A3B Q4_K_M                                   │
│  ctx 65536                                                 │
│  parallel 1                                                │
│  endpoint 127.0.0.1:8080                                  │
└────────────────────────────┬────────────────────────────────┘
                             │
                             v
┌─────────────────────────────────────────────────────────────┐
│                    PROYECTO REAL                            │
│                                                             │
│  Código | Git | tests | build | artefactos | .autopilot/  │
└─────────────────────────────────────────────────────────────┘
```

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

Consultor externo.

No es worker.

No modifica archivos.

---

## 14.2 Chrome dedicado

Debe existir un perfil separado de Chrome para automatización.

Nombre provisional:

```text
HERMES-CHATGPT
```

### Reglas

- una pestaña principal;
- `chatgpt.com`;
- sesión iniciada manualmente por el usuario;
- no acceder a otras pestañas;
- no navegar a otros dominios;
- no pedir credenciales;
- no almacenar contraseña.

---

## 14.3 Herramienta `consultar_chatgpt`

Debe:

1. validar que Chrome esté disponible;
2. validar dominio;
3. tomar contexto resumido;
4. escribir prompt;
5. esperar respuesta;
6. recuperar respuesta;
7. guardar evidencia;
8. devolver texto a Hermes.

### Protección

Si el dominio cambia:

```text
ABORT
```

---

# 15. Web Research

Hermes debe preferir:

1. documentación oficial;
2. repositorios oficiales;
3. issues/releases;
4. fuentes técnicas fiables.

Cada investigación relevante debe poder quedar registrada en:

```text
.autopilot/evidence/web/
```

---

# 16. Memoria y continuidad

La arquitectura usa varias capas:

```text
Nivel 1:
contexto activo

Nivel 2:
sesiones Hermes/Qwen

Nivel 3:
STATE / QWEN.md / EVENTS

Nivel 4:
Git / tests / filesystem
```

La capa superior puede fallar y el sistema debe reconstruirse desde las inferiores.

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

# 37. Interfaz futura

Primera versión:

- Hermes como interfaz principal;
- runner en segundo plano;
- logs/reportes como evidencia.

Una GUI propia es opcional y queda fuera de alcance inicial.

---

# 38. Secuencia de una noche típica

```text
23:55 usuario abre sistema

00:00 preflight
00:05 usuario aprueba

00:06 llama inicia
00:07 Hermes reconstruye estado
00:08 ciclo 1

00:20 Qwen Code implementa
00:35 tests fallan
00:40 Qwen corrige

01:10 checkpoint
01:11 ciclo 2

02:30 problema externo
02:35 Hermes investiga web
02:50 nuevo intento

03:20 sigue bloqueado
03:25 Hermes consulta ChatGPT
03:30 nueva estrategia

04:15 checkpoint
04:16 nueva sesión Qwen

06:30 Completion Gate
06:45 PASS

06:50 informe final
06:51 cleanup
06:52 llama cerrado
```

---

# 39. Responsabilidades resumidas

| Componente | Responsabilidad principal |
|---|---|
| Usuario | objetivo + aprobación inicial |
| Runner | ciclo de vida y seguridad operacional |
| Hermes | estrategia y supervisión |
| Qwen Code | programación |
| Qwen local | razonamiento/inferencia |
| Git | evidencia y recuperación |
| STATE | continuidad operacional |
| EVENTS | auditoría |
| ChatGPT | consulta externa |
| Watchdog | detección de fallos |
| Completion Gate | validación final |

---

# 40. Criterio de arquitectura correcta

La arquitectura se considera correctamente implementada si:

- Hermes y Qwen Code pueden compartir el mismo Qwen a 64K;
- nunca hay dos inferencias simultáneas;
- una caída no obliga a recomenzar;
- el proyecto puede recuperarse desde STATE + Git + tests;
- ChatGPT puede consultarse de forma controlada;
- una ejecución puede durar horas sin permisos repetidos;
- existe anti-loop externo;
- COMPLETED exige evidencia;
- llama-server se cierra al finalizar.

---

# 41. Regla para Antigravity

Antigravity debe implementar esta arquitectura de forma incremental.

Puede proponer mejoras, pero:

- no debe sustituir Hermes;
- no debe sustituir Qwen Code;
- no debe cambiar el modelo principal;
- no debe reducir el contexto;
- no debe eliminar las capas de estado;
- no debe quitar el Runner/Watchdog;
- no debe introducir concurrencia de inferencia con `parallel 1`;

sin aprobación explícita.

Si una pieza no es viable, debe documentar evidencia antes de proponer alternativa.
