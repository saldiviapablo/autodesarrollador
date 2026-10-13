# Macrofase 8 — parada por regresión de seguridad

Estado: STOPPED_SECURITY_REGRESSION. READY FOR REAL PILOT = NO.
Macrofase 8 no está aprobada. F27/F28 no se iniciaron.

| Gate | Resultado |
|---|---|
| Preflight | PASS — 134 checks, hashes completos, Git limpio inicial, Hermes v0.21.6 y mutexes libres |
| F23 Sandbox integral | FAIL — T-F23-PREPARE-BOUNDARY |
| F24 E2E corto | NOT_RUN — gate anterior FAIL |
| F25 2h | NOT_RUN — gate anterior FAIL |
| Checkpoint 4h | NOT_RUN / PREVIOUS_GATE_FAILED |
| F26 Auditoría integral | NOT_RUN — gate anterior FAIL |
| Regression gate posterior a F26 | NOT_RUN — no se alcanzó F26 |
| Cleanup | PASS |

## Hallazgo reproducido

`runner/run.ps1 -Action Prepare` llama al inicializador y copia el plan antes de
la admisión canónica `contract.py.inspect`. Una junction de proyecto rechazada
por la política de admisión permite escrituras antes del rechazo. La capa de
seguridad debe negar antes de cualquier escritura.

La prueba creó sólo un sentinel y una junction propios en sandbox; el target
está fuera de la ruta declarada del proyecto pero dentro del sandbox de
infraestructura. No tocó producción, credenciales ni archivos del usuario.
El Runner devolvió DENY/exit 2 por REPARSE_POINT_DENIED, después de crear:

- .autopilot\EVENTS.jsonl
- .autopilot\HEARTBEAT.json
- .autopilot\LOCK.json
- .autopilot\RUN-CONTRACT.yaml
- .autopilot\RUN-PLAN.json
- .autopilot\STATE.json
- .autopilot\STATE.md
- QWEN.md

El sentinel original conserva su hash. No se considera PASS el DENY tardío.
No se modificó ni reparó el Runner después del hallazgo: la solicitud exige
parada inmediata ante SECURITY_REGRESSION. La corrección necesaria consiste en
validar la ruta canónica y los inputs de Prepare antes de invocar el inicializador,
crear directorios o copiar archivos; deberá retestearse antes de continuar F23.
No requiere sustituir Hermes, Qwen, Runner ni las capas congeladas.

## Base y evidencia

Base 0ab05aa y certificaciones históricas 1–6/7A/7B preservadas. El caso nuevo
revela una carencia de cobertura del preflight anterior; esos PASS históricos
no certifican esta frontera de Prepare.
Preflight: evidence/preflight-8/. Caso: evidence/phase-23/prepare-boundary.json,
stdout/stderr, SUMMARY, cleanup, recursos y backup registrado.
Test reproducible: tests/test-phase23-prepare-boundary.py.

Se corrigió con backup el campo genérico runner: PENDING → PASS al inspeccionar
F17–F22; e2e genérico continúa pendiente de las validaciones de F24/F25.
Preflight/reconciliación: commit fcc3139. Esta fase fallida se cierra con un commit
separado de evidencia/estado, sin modificar código runtime ni evidencia histórica.

## Recursos y actividad

Snapshot tras la parada: RAM total 31.67 GiB; RAM libre 16.06 GiB; llama working set 0; VRAM usada/total 1682, 8188 MiB.
No hubo corrida del modelo ni serie temporal: RAM mínima durante inferencia,
tendencia de RAM, VRAM máxima de endurance y gráfica de 2h/4h NOT_MEASURED.
No se sustituye una observación puntual por una prueba prolongada.
Inferencias locales 0; reinicios 0; recoveries de runtime 0; consultas web 0;
consultas ChatGPT 0. No hubo degradación crítica observada ni modificaciones de
modelo, ctx 65536, parallel 1, Hermes v0.21.6 o configuración protegida.

## Cleanup y Git

Junction retirada sin borrado recursivo; target y escrituras conservados como
prueba. Metadata del initializer retirado tras comprobar mutex y owner muerto.
STATE/heartbeat FAILED, evento SECURITY_REGRESSION y checkpoint guardados.
Cero procesos propios/ports 8080/9119/9222, mutexes físicos libres y lock del caso
retirado. Ningún proceso desconocido fue matado. Cleanup PASS.

Rama agent/macro8-20261013; staging selectivo; NO PUSH; sin dependencias nuevas.
Hash del commit de parada y Git status posterior se guardan en
runtime/macro8-final-git.json. Detenido antes de F24 y antes de F27/F28.
