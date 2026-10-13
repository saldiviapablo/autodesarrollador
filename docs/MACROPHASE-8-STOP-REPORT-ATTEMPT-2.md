# Macrofase 8 — parada del intento 2

Fecha: 2026-10-13. Rama: agent/macro8-20261013. NO PUSH.

La regresión de Prepare solicitada está corregida y verificada. F23 integral
continúa FAIL por un segundo hallazgo de seguridad en el Path Guard existente.
Se aplicó la condición de parada inmediata antes de inferencia local, web o
consulta ChatGPT. No se modificó ese guardrail fuera del alcance autorizado.

| Gate | Resultado |
| --- | --- |
| Preflight original de Macrofase 8 | PASS histórico, preservado |
| Fix de Prepare | PASS |
| PREPARE_ZERO_WRITE_ON_DENY | PASS |
| Fronteras A–H | PASS, incluido symlink real |
| Smokes acotados del fix | PASS con clasificaciones documentadas |
| F23 integral, intento 1 | FAIL histórico, evidencia intacta |
| F23 integral, intento 2 | FAIL / SECURITY_REGRESSION |
| F24 | NOT_RUN / gate F23 FAIL |
| F25 / 2H | NOT_RUN / gate F23 FAIL |
| 4H | NOT_RUN / gate F23 FAIL |
| F26 | NOT_RUN / gate F23 FAIL |
| Regression gate final | NOT_RUN / gate F23 FAIL |
| Cleanup final | PASS |
| Integridad de componentes preservados | PASS |
| F27 y F28 | NOT_RUN |
| READY FOR REAL PILOT | NO |

## Corrección terminada

Causa raíz exacta: run.ps1 invocaba initializer, copias y escrituras de draft
antes de contract.inspect. Ese inspect detectaba la junction después de los
efectos laterales. Antes: WRITE → VALIDATE → DENY. Ahora: VALIDATE EVERYTHING
read-only → revalidate → APPLY → inspect final; el mutex cubre Prepare.

Se comparte la lógica canónica de contract.py con Prepare y se admiten juntos
todos los directorios, archivos y temporales. Fallos anteriores a Apply producen
DENY con prepare_write_count=0, corroborado por snapshots independientes.
Errores de Apply producen FAIL, cleanup limitado a los destinos nuevos conocidos
y conservación de datos preexistentes. Se reutilizan initializer, State Manager
atómico y Job Object existentes.

Commit separado: **b6e421bc039877cebbc58531b0549a801f8bc73d**
`fix: validate prepare boundary before side effects`.

A normal y H espacios/Unicode: ALLOW / Prepare PASS. B junction raíz,
C junction padre, D destino junction, E traversal, F ruta fuera del ámbito
declarado y G symlink: DENY / ZERO WRITES. El caso original confirma ausencia
de QWEN.md y .autopilot, de los ocho archivos históricos y de cambios en sentinel.

Smokes: RUN-CONTRACT draft no autorizado, STATE INITIALIZED, escritura atómica,
mutex real, cleanup propio, plan inválido/conflictos y revalidación de junction
PASS. Launcher no tiene Prepare: no aplica. F15: 5/5 PASS con rutas absolutas.
El smoke backend probe ejecuta tests/checkpoint y cleanup, y Completion Gate
rechaza correctamente el falso COMPLETED. No se presenta ese probe como E2E real.

La primera invocación de F15 con SandboxDir relativo falló por doble combinación
en el harness; se corrigió el llamador. La expectativa inicial COMPLETED para
probe era incorrecta; se conservó el resultado y se clasificó contra el gate
real. La primera comparación de bytes Git/Windows confundió CRLF con cambios;
la comprobación corregida usa SHA raw registrado y contenido Git normalizado.
No se cambiaron componentes para hacer pasar esas comprobaciones.

TOCTOU residual: la revalidación ocurre inmediatamente antes del initializer,
pero éste escribe mediante rutas, sin handles que fijen el namespace. Un actor
externo ajeno al mutex aún puede cambiarlo o crear un nombre reservado durante
Apply. No se afirma aislamiento frente a ese actor; detalle y cleanup en
docs/PREPARE-BOUNDARY-FIX.md.

## Nuevo hallazgo que impide continuar

**T-F23-PATHGUARD-EXISTING-TARGET-JUNCTION = FAIL.**

Se creó un sandbox nuevo con bug de suma, feature decimal pendiente, test
inicialmente fallido, build real, README incompleto, requisitos de web/consulta
ChatGPT/recovery y operación prohibida contra sentinel. El test de baseline
falló como se esperaba; el build de baseline pasó. La prueba de seguridad previa
al arranque detectó el nuevo bloqueo y el resto de F23 quedó NOT_RUN.

Test-WorkspacePathGuard recibió una ruta absoluta de un archivo existente:
`project/escape-junction/nested/existing.txt`. Su destino canónico es
`outside-approved-project/nested/existing.txt`, fuera del proyecto. Sin embargo,
devolvió **Allowed=true / ALLOWED_WORKSPACE_PATH**.

La función examina sólo el primer elemento existente de la ruta. Cuando el
archivo ya existe no recorre sus padres para detectar la junction; después
acepta el prefijo textual del workspace. La prueba anterior de F15 ejercita un
archivo inexistente directamente bajo la junction, por lo que no cubre este caso.
Es un defecto preexistente recién demostrado, no causado por el fix de Prepare:
security-guard.ps1 mantiene su SHA-256
`2294a5e9d5338feab4f7c6945a4250a350f1c72b0c17ade17c993bbd21640b66`.

No se ejecutó la escritura permitida incorrectamente. Sentinel intacto, junction
propia retirada de forma no recursiva, ningún dato productivo tocado.
La corrección siguiente requiere ampliar el alcance a Path Guard; no se aplicó
silenciosamente dentro del fix exclusivo de Prepare.

## Recursos y cierre

Inferencias locales: 0. Llama no arrancó. Web: 0. ChatGPT: 0. Reinicios: 0.
Recoveries de runtime: 0; se probó cleanup con fallo de initializer inyectado.
No hubo ejecución de resistencia, por lo que RAM mínima, tendencia RAM y VRAM
máxima de 2h/4h son **NO MEDIDAS**. Snapshot final: RAM total 31.667 GiB,
RAM libre 21.149 GiB, VRAM usada 1295/8188 MiB. No permite inferir estabilidad
prolongada ni resolver el antecedente de 0.38 GiB de 7B.

Cleanup: cero supervivientes propios verificados por PID y start_ticks, cero
helpers Runner, mutex de run e inferencia libres y cero listeners 8080/9119/9222.
Se retiró metadata de inicialización propia con owner muerto bajo el mutex.
Fixtures inertes permanecen en sandbox como evidencia; no hay procesos activos.

Hermes productivo v0.21.6, HEAD 818c13be1dc4fd28987e1e881a9408224afd4535;
modelo y ejecutable preservados, SHA-256 completo revalidado. Se mantienen
qwen36 / 127.0.0.1:8080 / ctx 65536 / parallel 1. Cero dependencias nuevas,
actualizaciones, cambios de security.yaml o Inference Lock y cero push.

Archivos funcionales del fix: runner/run.ps1, runner/contract.py,
runner/prepare.py y runner/prepare-apply.ps1. Pruebas: test-phase23-prepare-boundary.py,
test-phase23-prepare-admission.py y test-phase23-integral-security.py. Se actualizaron
README, ROADMAP, MANIFEST, IMPLEMENTATION-STATUS e INSTALLATION-STATE para el estado
actual; la evidencia histórica y el STOP-REPORT original no se alteraron.

Evidencias: evidence/phase-23-attempt-2/prepare-boundary.json,
prepare-admission.json, security-smoke-invocations.json,
runtime-smoke-classification.json, integral-security.json, cleanup-final.json,
protected-integrity-final.json e historical-bindings.json.

Git final y commits: runtime/macro8-f23-attempt2-final-git.json, generado después
del commit de parada. Working tree limpio requerido. Macrofases 1–7B conservan
su certificación histórica; la revalidación actual de seguridad es FAIL.

**MACROFASE 8 = FAIL / STOPPED_SECURITY_REGRESSION. READY FOR REAL PILOT = NO.**
