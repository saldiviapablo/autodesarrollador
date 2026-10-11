# 07 — Roadmap de implementación
## Proyecto: Desarrollador Autónomo

**Versión:** 2.0  
**Estado:** BORRADOR PARA APROBACIÓN  
**Arquitectura base:** Hermes Agent + Qwen Code CLI + Qwen local mediante llama.cpp

---

# 1. Objetivo

Definir el orden obligatorio de implementación.

Principio:

> **No avanzar a la siguiente fase si la anterior no fue verificada.**

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

# 20. Fase 17 — Runner

## Objetivo

Crear supervisor determinista del ciclo de vida.

## Responsabilidades

- leer config;
- validar proyecto;
- run_id;
- iniciar llama;
- health;
- iniciar Hermes;
- heartbeat;
- timeout;
- watchdog;
- cleanup;
- report.

## Condición de salida

```text
RUNNER PASS
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

# 26. Fase 23 — Sandbox integral

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
