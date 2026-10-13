# Macrofase 8 — intento 3 bloqueado

Fecha: 2026-10-13. Rama agent/macro8-20261013. NO PUSH.

Path Guard está corregido y sus gates PASS. F23 completa no pasó: la consulta
real a ChatGPT quedó UNKNOWN_DELIVERY y su reconciliación read-only no pudo
confirmarla. Se preservó el ledger, no se reenvió y se detuvo con
BLOCKED_REQUIRES_HUMAN. No se ejecutaron F24–F28.

| Gate | Resultado |
| --- | --- |
| Fix Path Guard | PASS |
| Caso original externo / writes=0 | PASS |
| A–J READ y WRITE | PASS |
| Prepare regression | PASS |
| MCP/plugin/Runner boundary smokes | PASS |
| Path/Security Guard histórico | PASS, 5/5; comandos 11/11 DENY |
| Web real | Fetch oficial HTTP 200; persistencia PASS |
| Sesión ChatGPT | SUCCESS / session_ready=true |
| Consulta ChatGPT real | FAIL / UNKNOWN_DELIVERY |
| Reconciliación de consulta | UNKNOWN_DELIVERY / reconciled=false / no_resend=true |
| F23 integral | FAIL / BLOCKED_REQUIRES_HUMAN |
| F24, F25/2H, 4H, F26 | NOT_RUN / gate F23 incompleto |
| Regression final | NOT_RUN / gate F23 incompleto |
| F27/F28 | NOT_RUN |
| Cleanup, locks e integridad | PASS |
| READY FOR REAL PILOT | NO |

## Causa y corrección

El guard antiguo inspeccionaba el primer objeto existente y autorizaba después
por prefijo textual. Un archivo normal existente evitaba la inspección de su
padre junction; el destino físico fuera del proyecto recibía ALLOW.

scripts/canonical_path.py centraliza resolución física de todos los componentes,
incluidos los padres de los destinos de enlaces. Se compara por componentes
canónicos, no por StartsWith. Los destinos futuros se construyen sobre el
ancestro existente ya resuelto. Ciclos, dangling links, reparse no interpretable,
ambigüedad y más de 32 saltos son DENY. READ y WRITE usan el mismo guard.
Runner/Prepare y adapters MCP/plugin reutilizan el resolver; sus restricciones
adicionales y los hashes nativos aprobados no se amplían ni se modifican.

Commit **6e0a5077505378be5bd7d1187f871f1e1640a321**:
`fix: resolve reparse targets in canonical path guard`.

A normal y I espacios/Unicode ALLOW. B archivo existente/C inexistente/D
directorio detrás de junction externa, F anidada, G traversal externo, H absoluta
externa y J case-insensitive DENY. E permite solamente destino físico interno
según la política 04 y comportamiento anterior de Path Guard; Prepare/Runner/MCP
mantienen su rechazo de todo reparse. PASS también para prefijo hermano,
destrucción de raíz, ciclos reales, límite de enlaces y error de readlink inyectado.
Snapshots independientes confirman cero modificaciones durante los checks.

El caso original ahora devuelve PATH_BOUNDARY_VIOLATION y el sentinel permanece
intacto. La evidencia histórica ALLOW/FAIL de intentos 1/2 y sus STOP-REPORTS se
preserva byte por byte. El resultado unitario previo al commit registra HEAD
f279e3c como base; el SHA del guard corregido lo liga a la implementación nueva.

Prepare sigue VALIDATE → REVALIDATE → APPLY: boundary original y A–H PASS,
draft no autorizado, STATE, escritura atómica, mutex y cleanup PASS. MCP normal
ALLOW/escape DENY; plugin normal ALLOW/escape DENY y SHA-256 PASS. Command Guard
y Secret Guard conservan sus cuerpos originales; security.yaml, hook integrity,
Inference Lock, allowlists y código/hash nativo MCP/plugin permanecen intactos.

## Intento integral y bloqueo real

Sandbox nuevo: sandbox/f23-full-feac8aea/project. Contiene bug, feature pendiente,
test inicialmente fallido, build y README incompleto. Los checks de seguridad se
ejecutaron antes del intento integral. La documentación oficial decimal se obtuvo
mediante web-research real y quedó en WEB.json como datos no confiables. El
extracto recibido tiene algunos caracteres mal decodificados; no se certificó
calidad completa de extracción ni se corrigió ese componente fuera del alcance.

El bridge verificó sesión lista. La consulta técnica real reservó el ID:
**f23-ee298529568f4f8b94f4dd16f90a0be4**.
El padre alcanzó su deadline y el ledger quedó DELIVERY_INTENT, send_attempts=1,
sin confirmación de user/assistant turns. La reconciliación real posterior
devolvió UNKNOWN_DELIVERY, reconciled=false y no_resend=true. No se ejecutó otra
consulta, no se cambió el ID y no se borró ni forzó el ledger.

No está confirmada la causa del timeout ni si la entrega ocurrió. No se afirma
que haga falta login: check-session fue SUCCESS. Hace falta verificar la entrega
de ese ID antes de reanudar; no se debe reenviar ciegamente.

Hermes/Qwen/llama no arrancaron. Las correcciones funcionales de bug/feature,
tests/build finales, crash/recovery de runtime y Completion Gate quedaron NOT_RUN.
El test inicial falló como se esperaba, lo que no equivale a una corrección PASS.
Se guardó STATE BLOCKED_REQUIRES_HUMAN, BLOCKED.md, evento y checkpoint inmutable
chk-20261013-203029-005. Ese checkpoint de bloqueo no se presenta como recovery
de agentes ejecutado.

## Autocorrecciones de harness y límites

El batch A–J excedía el límite de comando Windows; se cambió a JSON en sandbox,
con cleanup finally de enlaces propios. La primera inspección final de procesos
contó el pwsh verificador porque su comando incluía los nombres buscados;
se excluyeron sus ancestros, sin matar procesos por esa coincidencia.

El harness inicial preparaba Git del fixture después de la consulta. Prepare
había observado el repositorio padre antes de crear el Git aislado. Se corrigió
el orden del harness para próximos intentos y se aisló el fixture bloqueado;
se reconciliaron STATE.git y un nuevo checkpoint, conservando el checkpoint
anterior inmutable. No se alteró el Runner para corregir ese error del harness.

TOCTOU residual: la validación no mantiene handles durante toda la operación.
Prepare revalida antes de Apply y el adapter plugin antes de invocar; MCP conserva
su chequeo estricto previo al read. No se afirma un sandbox de kernel.

## Recursos, cleanup y Git

0 inferencias locales, 0 reinicios de modelo, 0 recoveries de runtime. Una
obtención web real y un intento de consulta real, seguido de reconciliación sin
envío. No hubo corrida 2h/4h; mínimos/tendencias de RAM y VRAM de resistencia
son NO MEDIDOS. Snapshot final en cleanup-final.json: 31.667 GiB RAM total,
16.068 GiB disponible, VRAM 1508/8188 MiB; llama working set=0. No demuestra
estabilidad prolongada ni resuelve el antecedente de 0.38 GiB de 7B.

Cleanup PASS: navegadores nuevos propios cerrados por PID/birth, ningún proceso
Runner propio restante, puertos 8080/9119/9222 sin listeners, mutex de run e
inferencia libres, metadata de inicialización retirada y browser lease libre.
Ledger y fixtures/checkpoints inertes se conservan. No se tocó producción.

Hermes v0.21.6 y HEAD 818c13be1dc4fd28987e1e881a9408224afd4535 preservados.
Modelo y llama SHA-256 completos revalidados; qwen36 / 127.0.0.1:8080 /
ctx 65536 / parallel 1 intactos. Ninguna dependencia nueva ni actualización.
El launcher observó Chrome/155.0.8059.40, distinto del snapshot 154.0.8037.99 de
VERSIONS.lock; se registra el dato sin actualizar el lock ni atribuirle el timeout.

Archivos funcionales: scripts/canonical_path.py, scripts/security-guard.ps1,
scripts/hermes-mcp-plugin-guard.ps1, runner/contract.py y runner/prepare.py.
Pruebas: test-fase15-security.ps1, tres retests F23 existentes, nuevo
test-phase23-pathguard.py y test-phase23-integral.py. Documentación/estado y
evidencia nueva se actualizaron. Backups bajo backups/pathguard-fix-20261013-201419/.

Evidencia: evidence/phase-23-attempt-3/; pathguard-A-J.json, prepare-boundary.json,
prepare-admission.json, fix-integrity.json, web.json, chatgpt-session.json,
chatgpt.json, chatgpt-reconciliation.json, integral-result.json,
block-checkpoint.json, cleanup-final.json, mutex-final.json,
protected-integrity-final.json e historical-bindings.json.

Git final: rama agent/macro8-20261013, limpio tras commit de bloqueo separado,
sin push. Registro exacto de commits/estado:
runtime/macro8-f23-attempt3-final-git.json.

**F23 = FAIL / BLOCKED_REQUIRES_HUMAN. READY FOR REAL PILOT = NO.**
