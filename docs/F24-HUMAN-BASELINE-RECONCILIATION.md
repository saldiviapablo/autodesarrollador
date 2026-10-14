# F24 — reconciliación humana sobre conversación existente

PHASE: corrección acotada del mecanismo humano ChatGPT. STATUS: PASS.
F24 permanece detenida; esta corrección no certifica su E2E ni inicia F25.

## Auditoría previa

La restricción 0/0 apareció en cd44d38689b81e233b4dac43602d4e68eabfc01c,
dentro de confirmNotDelivered, para la conversación nueva de F23. No pertenece
a reconcileObservation automático ni a sus invariancias de entrega confirmada.
El documento histórico F23 y sus evidencias se conservan sin cambios.

BASELINE_PROVEN = YES para f24-7257c739e1fd449aae1f1f93856aef7f:
user_turns_before = 1; assistant_turns_before = 1. Ledger original SHA-256:
96e77ee4e05e76c1fa1821c0f4e03aaa9856c6521d826c37181cd6ed67ab782e.
Coincide con el fingerprint comprometido en 4e8ba72, anterior al reinicio.
Su historial conserva RESERVED→RESERVED, intentos 0, 05:18:30.379Z, antes de
RESERVED→DELIVERY_INTENT, intentos 1, 05:18:30.698Z, del 2026-10-14.
El código original vigente, comparado con fea2a71, captura los contadores y
persiste baseline/URL con fsync antes de preparar el composer y guardar intent.
No hubo actualizaciones posteriores en el ledger original.

Las entradas antiguas del historial no duplican los valores modificados.
La demostración combina ledger persistido, fingerprint anterior, orden del
historial y código vigente durante ese intento; no afirma disponer de un
snapshot independiente tomado antes del click ni reconstruye el baseline
a partir de los contadores actuales.

## Cambio y garantías

Sólo la ruta HUMAN_VISUAL_RECONCILIATION admite baseline válido distinto de cero.
Exige recibo humano explícito, ID/hash exactos, baseline auditado y sus hashes
vinculados al ledger actual, conversación HTTPS chatgpt.com con ID coincidente,
contadores actuales idénticos, composer UTF-8 con SHA esperado, ausencia de
streaming y botón disponible. Rechaza historial inconsistente, evidencia SENT,
respuesta/turnos posteriores, retry consumido y replay. Root sin conversation_id
se admite únicamente para conversación nueva con baseline 0/0.

El recibo humano es una frontera de autorización de confianza. El procedimiento
externo debe auditar realmente la persistencia previa y verificar el hash del
artefacto antes de crear el recibo; un marcador RESERVED del historial por sí
solo no demuestra esa persistencia. baseline-proof.json y human-resolution.json
documentan y vinculan la auditoría concreta de F24. El ledger guarda los hashes
del recibo y de esa prueba, sin almacenar texto del prompt.

reconcileObservation, tools/chatgpt-bridge.js, wrapper, caminos físicos de envío
y controles de consumo de retry permanecen intactos. La ruta automática sólo
confirma entrega observable con último mensaje/hash, user +1, assistant +1 y
ausencia de streaming; igualdad con baseline sigue UNKNOWN_DELIVERY/no_resend.

## Verificación y resultado real

Tests humanos deterministas PASS: 0/0, 1/1, 5/5; discrepancias 2/1 y 2/2;
hash, conversación, ID, recibo, baseline/provenance, historial, UTF-8, streaming,
evidencia SENT, retry consumido y segundo retry físico DENY. Suite determinista
anterior de idempotencia PASS; domain lock Node, 13 casos, PASS. Pruebas físicas
de retry sólo simuladas en sandbox; cero envíos reales en esta corrección.

La acción normal inspect-prepared confirmó conversación
6acefadc-36b8-83e8-9172-7e3e9421dc21 y turnos 1/1. Composer SHA-256:
5c978846eab33716662508b28ef5adb50bde6c211b11fbbb81c193eb8896d708.
Coincide con el prompt original reconstruido desde el literal del harness sólo
para comparación offline, sin escribirlo en el navegador. Sanitizer PASS.

La acción normal reconcile-human registró NOT_DELIVERED_CONFIRMED / RETRY_SAFE,
human_retry_remaining = 1, send_attempts = 1. Conservó todo el historial original
e incluyó logical_previous = UNKNOWN_DELIVERY. Ningún click, inserción ni envío.
El composer continúa preparado, los turnos permanecen 1/1, presupuesto 1/5 y
STATE sin cambios. RETRY_SAFE permite un futuro intento físico único; el recibo
explicita send_authorized_now = false y esta ejecución se detiene sin consult.

F23 sigue PASS; ledger COMPLETED/ALREADY_SENT y evidencias históricas intactos.
Cleanup PASS: procesos de prueba terminados, sandboxes de prueba retirados,
lease del bridge liberada; Chrome del usuario permanece abierto. Ninguna
inferencia, dependencia, actualización Hermes, modificación de políticas,
hooks, Inference Lock, RUN-CONTRACT o hashes aprobados. NO PUSH.

EVIDENCE: evidence/f24-human-baseline-reconciliation-20261014/.
Sus JSON/TXT se guardan sin conversión de finales de línea mediante atributos
Git locales a esa carpeta, preservando los vínculos SHA-256 byte por byte.
BACKUP: backups/f24-human-baseline-reconciliation-20261014/.
NEXT PHASE: ninguna; esperar instrucción humana antes de enviar o reanudar.
