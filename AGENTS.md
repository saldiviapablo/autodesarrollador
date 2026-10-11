# AGENTS.md
## Proyecto: Desarrollador Autónomo

**Versión:** 2.0  
**Estado:** BORRADOR PARA APROBACIÓN  
**Aplicación:** Antigravity, Codex y cualquier agente que trabaje sobre esta infraestructura.

---

# 1. Propósito

Este archivo contiene las reglas operativas obligatorias para cualquier agente que trabaje dentro del proyecto **Desarrollador Autónomo**.

Debe leerse antes de:

- instalar;
- configurar;
- modificar;
- probar;
- crear scripts;
- cambiar arquitectura;
- tocar componentes existentes.

---

# 2. Arquitectura obligatoria

La arquitectura base aprobada es:

```text
Hermes Agent
    ↓
Supervisor / Orquestador
    ↓
Qwen Code CLI
    ↓
Coding Worker
    ↓
llama.cpp
    ↓
Qwen3.6-35B-A3B Q4_K_M
```

Componentes adicionales obligatorios:

```text
Runner
Watchdog
Inference Lock
STATE
EVENTS
Checkpoints
Completion Gate
Cleanup
```

No sustituir silenciosamente ninguno de estos componentes.

---

# 3. Roles

## Hermes

Responsabilidad:

- planificación;
- investigación;
- supervisión;
- recuperación;
- escalamiento;
- validación;
- consulta ChatGPT;
- delegación.

Hermes NO es el coding worker principal.

---

## Qwen Code CLI

Responsabilidad:

- analizar código;
- modificar archivos;
- ejecutar comandos;
- tests;
- builds;
- Git local;
- autocorrección.

---

## Runner

Responsabilidad:

- ciclo de vida;
- procesos;
- timeouts;
- health;
- watchdog;
- locks;
- cleanup.

---

# 4. Orden de trabajo obligatorio

Seguir siempre:

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

No usar:

```text
IMPLEMENT EVERYTHING FIRST
```

---

# 5. Documentación obligatoria

Antes de empezar, leer:

```text
00-README.md
01-OBJETIVOS-Y-REQUISITOS.md
02-ARQUITECTURA.md
03-MEMORIA-Y-CONTINUIDAD.md
04-AUTONOMIA-Y-SEGURIDAD.md
05-INSTALACION-Y-CONFIGURACION.md
06-PRUEBAS-Y-CRITERIOS-DE-EXITO.md
07-ROADMAP.md
AGENTS.md
```

---

# 6. Precedencia

Si existe contradicción:

```text
1. AGENTS.md
2. 04-AUTONOMIA-Y-SEGURIDAD.md
3. 01-OBJETIVOS-Y-REQUISITOS.md
4. 02-ARQUITECTURA.md
5. 03-MEMORIA-Y-CONTINUIDAD.md
6. 05-INSTALACION-Y-CONFIGURACION.md
7. 06-PRUEBAS-Y-CRITERIOS-DE-EXITO.md
8. 07-ROADMAP.md
9. instrucciones temporales de implementación
```

No resolver contradicciones ocultándolas.

Documentarlas.

---

# 7. Workspace de infraestructura

Trabajar principalmente dentro de:

```text
Desarrollador autonomo\
```

Se permite crear:

```text
config\
runner\
scripts\
tools\
tests\
sandbox\
backups\
docs\
logs\
evidence\
```

---

# 8. Escrituras fuera del workspace

No escribir fuera de la carpeta de infraestructura salvo que una fase explícita lo requiera.

Ejemplos válidos:

- configuración de Hermes;
- configuración de Qwen Code;
- perfil dedicado Chrome;
- integración necesaria;
- instalación de dependencia.

Siempre:

- justificar;
- backup;
- registrar;
- validar.

---

# 9. Componentes existentes que deben preservarse

## llama.cpp

Ruta conocida:

```text
C:\AI\llama.cpp\llama-server.exe
```

No reinstalar sin necesidad.

---

## Modelo Qwen

```text
Qwen3.6-35B-A3B-Q4_K_M.gguf
```

Ruta conocida:

```text
C:\Users\Pc\.cache\huggingface\hub\models--ggml-org--Qwen3.6-35B-A3B-GGUF\snapshots\baec3ebee244827cda0f4557eafa8b28f7545fa6\Qwen3.6-35B-A3B-Q4_K_M.gguf
```

No:

- borrar;
- mover;
- reemplazar;
- volver a descargar;

sin motivo aprobado.

---

# 10. Configuración Qwen validada

Usar como base:

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

Alias:

```text
qwen36
```

Host:

```text
127.0.0.1
```

Puerto:

```text
8080
```

---

# 11. Regla de contexto

No reducir a:

```text
16K
32K
```

sin una razón técnica demostrada y documentada.

Existe evidencia de funcionamiento hasta 60K tokens reales con margen de RAM.

---

# 12. `--parallel 1`

Regla crítica:

```text
NUNCA dos inferencias locales simultáneas.
```

Debe existir:

```text
Inference Lock
```

o mecanismo equivalente.

---

# 13. Concurrencia permitida

Sí pueden coexistir:

```text
web search
tests
build
filesystem
Git
procesos externos
```

si no requieren inferencia Qwen simultánea.

---

# 14. Configuración central

No hardcodear rutas/parámetros repetidamente.

Crear y usar:

```text
config/system.yaml
```

También:

```text
config/security.yaml
config/VERSIONS.lock
```

---

# 15. Legacy Goose

Archivos detectados:

```text
C:\Users\Pc\Desktop\Iniciar Qwen - Goose 16K.bat
C:\Users\Pc\Desktop\Iniciar Qwen.bat
C:\Users\Pc\Documents\Proyectos Tech\GOOSE-TEST\goose-night.ps1
```

Reglas:

- no reutilizar como configuración oficial;
- no borrar automáticamente;
- no asumir que representan el sistema nuevo.

---

# 16. Inventario antes de instalación

Antes de instalar:

detectar:

```text
llama.cpp
Qwen model
Git
GitHub CLI
Node
npm
Python
PowerShell
Chrome
Qwen Code
Hermes
```

Guardar evidencia.

---

# 17. No reinstalar por reflejo

Si algo ya existe:

```text
DETECT
↓
VERIFY
↓
REUSE
```

No:

```text
INSTALL AGAIN
```

salvo razón técnica.

---

# 18. Backups

Antes de tocar configuración existente:

crear:

```text
backups/<timestamp>/
```

Registrar:

- original;
- copia;
- motivo.

---

# 19. No tocar drivers

No modificar:

- NVIDIA drivers;
- CUDA global;
- chipset;
- BIOS;
- firmware;

salvo proyecto explícito distinto.

---

# 20. No cambiar Windows globalmente

Evitar:

- Registry;
- firewall;
- execution policy global;
- servicios;
- usuarios;
- PATH global innecesario.

Preferir cambios locales o por proceso.

---

# 21. Privilegios

Runtime normal:

```text
usuario estándar
```

No ejecutar todo como Administrador.

UAC sólo cuando sea estrictamente necesario.

---

# 22. Memoria del proyecto

Toda ejecución autónoma debe usar:

```text
QWEN.md

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

---

# 23. El chat no es fuente de verdad

Nunca dejar conocimiento crítico sólo en:

- conversación Hermes;
- conversación Qwen;
- ChatGPT;
- memoria interna.

Persistirlo.

---

# 24. STATE.json

Es la fuente operativa canónica.

Debe actualizarse durante el trabajo.

No esperar al final.

---

# 25. STATE.md

Vista humana.

Debe derivarse de estado real.

No sustituye STATE.json.

---

# 26. Git y tests superan a STATE

Si existe contradicción:

```text
filesystem / Git / tests
```

tienen prioridad sobre la memoria del agente.

---

# 27. Recovery Protocol

Ante crash, reinicio o nueva sesión:

```text
RUN-CONTRACT
STATE
STATE.md
QWEN.md
git status
git diff
tests/build
checkpoint
EVENTS
reconcile
continue
```

---

# 28. Qwen Code sessions

Usar resume/continue mientras sea útil.

Crear sesión nueva si:

- repite;
- se contradice;
- contexto contaminado;
- fase nueva grande;
- compactación excesiva.

Checkpoint antes.

---

# 29. Hermes sessions

Usar persistencia/historial si ayuda.

Pero no depender de ello para recuperar el run.

---

# 30. Autonomía

Después de aprobación inicial:

no pedir permisos repetidos para:

- editar proyecto;
- ejecutar comandos permitidos;
- tests;
- builds;
- dependencias del proyecto;
- Git local;
- web;
- ChatGPT;
- checkpoints.

---

# 31. Acciones bloqueadas

No ejecutar automáticamente:

```text
git push
git push --force
git reset --hard peligroso
git clean -fdx
format
diskpart
bcdedit
reg delete
shutdown
restart-computer
borrado masivo
operaciones destructivas producción
```

---

# 32. Git

Preferir rama:

```text
agent/<run_id>
```

Permitido:

```text
status
diff
log
branch
commit local
```

No push por defecto.

---

# 33. Staging

Preferir staging selectivo.

No usar:

```text
git add .
```

ciegamente si puede incluir secretos, logs o basura.

---

# 34. Secretos

Nunca incluir secretos en:

```text
Git
STATE
EVENTS
logs
reportes
ChatGPT
```

Usar referencias indirectas y sanitización.

---

# 35. ChatGPT

ChatGPT es:

```text
CONSULTOR
```

No:

```text
WORKER
```

Hermes decide si usar su respuesta.

Qwen Code ejecuta cambios.

---

# 36. Browser ChatGPT

Perfil dedicado:

```text
HERMES-CHATGPT
```

Reglas:

- una pestaña;
- `chatgpt.com`;
- no otras pestañas;
- no cambio de dominio;
- no credenciales en scripts.

---

# 37. Web

Prioridad de fuentes:

```text
1. documentación oficial
2. repositorio oficial
3. issues/releases
4. fuente técnica fiable
```

Registrar evidencia importante.

---

# 38. Anti-loop

Nunca repetir indefinidamente.

Límites iniciales:

```text
max_cycles = 20
max_same_failure = 3
max_no_progress = 3
max_chatgpt_queries = 5
```

---

# 39. Progreso real

Cuenta como progreso:

- nuevo test PASS;
- menos errores;
- diff relevante;
- artefacto válido;
- build avanza;
- tarea finalizada.

No cuenta:

- explicación;
- reread;
- mismo intento;
- promesa de corregir.

---

# 40. Escalamiento

Secuencia recomendada:

```text
retry
↓
new approach
↓
web
↓
ChatGPT
↓
new session if useful
↓
STALLED
```

---

# 41. Estado crítico humano

Si requiere:

- producción;
- datos reales;
- credenciales;
- publicación;
- gasto;
- acción irreversible;

usar:

```text
BLOCKED_REQUIRES_HUMAN
```

---

# 42. No esperar indefinidamente

En Night Mode:

si requiere humano:

```text
checkpoint
↓
BLOCKED.md
↓
cleanup
↓
exit
```

---

# 43. Pruebas

No marcar una fase PASS sin ejecutar las pruebas indicadas en:

```text
06-PRUEBAS-Y-CRITERIOS-DE-EXITO.md
```

---

# 44. Evidencia

Toda fase importante debe producir evidencia.

Ejemplo:

```text
evidence/installation/
evidence/tests/
evidence/chatgpt/
evidence/recovery/
```

---

# 45. Completion Gate

Un agente diciendo:

```text
DONE
```

no significa:

```text
COMPLETED
```

Antes verificar:

```text
objective
acceptance criteria
tests
build
artifacts
git diff
pending
STATE
```

---

# 46. Cleanup

Siempre debe ejecutarse.

Tanto en:

```text
SUCCESS
FAIL
TIMEOUT
BLOCKED
STALLED
ABORT
```

---

# 47. Cleanup mínimo

```text
detener Qwen Code worker
detener procesos auxiliares propios
guardar STATE
guardar logs
generar reporte
cerrar llama-server
verificar proceso
liberar locks
```

---

# 48. Ownership de procesos

No matar procesos basándose sólo en nombre.

Preferir:

- PID registrado;
- run_id;
- command line;
- start time.

---

# 49. llama-server

Durante un run:

```text
START ONCE
KEEP RUNNING
STOP AT END
```

No apagar entre llamadas normales.

---

# 50. Health

No considerar llama listo porque exista proceso.

Validar health endpoint.

---

# 51. Runner

La lógica de ciclo de vida debe vivir en Runner.

No meterla toda dentro de:

```text
.bat
```

---

# 52. Launchers

Visible:

```text
INICIAR-DESARROLLADOR-AUTONOMO.bat
DETENER-DESARROLLADOR-AUTONOMO.bat
```

Deben ser simples.

---

# 53. Sandbox primero

Nunca validar guardrails destructivos en un proyecto real.

Usar:

```text
sandbox/
```

---

# 54. Desarrollo por fases

Seguir:

```text
07-ROADMAP.md
```

No saltar fases críticas.

---

# 55. Si una fase falla

```text
FAIL
↓
diagnose
↓
fix
↓
retest
```

No seguir acumulando fallos.

---

# 56. Cambios de arquitectura

Si aparece una limitación técnica real:

1. documentar evidencia;
2. indicar impacto;
3. proponer alternativa;
4. no cambiar silenciosamente;
5. pedir aprobación si afecta arquitectura base.

---

# 57. Actualizaciones

No actualizar durante un run normal:

- llama.cpp;
- Qwen Code;
- Hermes;
- Node;
- Python.

Las actualizaciones son tareas de mantenimiento separadas.

---

# 58. Código del propio sistema

Durante un run de un proyecto externo:

Qwen Code no debe modificar automáticamente:

```text
runner/
security config
guardrails
watchdog
```

del Desarrollador Autónomo.

Infraestructura y proyecto gestionado deben estar separados.

---

# 59. Integridad de documentación

Si una ruta, versión o arquitectura cambia:

actualizar el documento correspondiente.

No dejar documentación falsa.

---

# 60. Estado de implementación

Mantener:

```text
docs/IMPLEMENTATION-STATUS.md
```

con:

```text
fase
estado
evidencia
bloqueos
```

---

# 61. Estado de instalación

Mantener:

```text
config/INSTALLATION-STATE.json
```

---

# 62. Versiones

Mantener:

```text
config/VERSIONS.lock
```

---

# 63. Calidad de scripts

Scripts deben:

- soportar rutas con espacios;
- usar UTF-8;
- manejar errores;
- tener timeout;
- generar logs;
- devolver resultado interpretable;
- hacer cleanup.

---

# 64. PowerShell

Si se usa:

- evitar fragilidad de pegado interactivo;
- preferir scripts `.ps1`;
- no depender sólo de `$LASTEXITCODE`;
- validar outputs reales;
- manejar `try/catch/finally`.

---

# 65. Código temporal

No dejar scripts experimentales como piezas productivas sin:

- limpiar;
- documentar;
- probar;
- mover a ubicación correcta.

---

# 66. Robustez

Preferir:

```text
deterministic checks
```

sobre:

```text
LLM says OK
```

---

# 67. Simplicidad

No introducir:

- bases de datos adicionales;
- brokers complejos;
- Docker;
- Kubernetes;
- Kafka;
- servicios cloud;

si no resuelven una necesidad real demostrada.

---

# 68. Dependencias

Toda dependencia nueva debe responder:

```text
¿Por qué es necesaria?
¿Qué problema resuelve?
¿Cómo se prueba?
¿Cómo se quita?
```

---

# 69. No sobrearquitecturar

La arquitectura debe ser robusta, pero comprensible y mantenible en una sola PC Windows.

---

# 70. Informe por fase

Al terminar cada fase, informar:

```text
PHASE
STATUS
CHANGES
TESTS
EVIDENCE
RISKS
NEXT PHASE
```

---

# 71. No ocultar limitaciones

Si algo no funciona:

decir:

```text
FAIL
```

No:

```text
“prácticamente listo”
```

---

# 72. Regla final

El objetivo no es que Antigravity produzca muchos archivos.

El objetivo es construir un sistema que pueda:

```text
trabajar solo
recordar
recuperarse
corregirse
demostrar lo que hizo
detenerse con seguridad
```

durante horas.

Cualquier decisión técnica debe evaluarse contra ese objetivo.
