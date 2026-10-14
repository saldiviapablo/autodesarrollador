# Fronteras antes de F24 ATTEMPT 4

ATTEMPT 3: HISTORICAL FAIL / BLOCKED_REQUIRES_HUMAN. Su consulta y ledger no se reenvían ni se reconcilian. Se preservan 419 archivos históricos por SHA-256.

A — CHATGPT_BRIDGE_FIX = PASS (tests deterministas, cero mensajes reales).
SENT_CONFIRMED es irreversible y retry devuelve ALREADY_SENT incluso con RESPONSE_PENDING. La confirmación exige user +1, SHA y conversación exacta; el caso de conversación nueva sólo admite transición explícita desde baseline 0/0 a un ID nuevo que queda vinculado. Composer vacío es una señal adicional. Los estados históricos no se migran.

Presupuesto respuesta60s: readiness15 + prepare15 + click4 + confirmación12 + respuesta60 + finalización4 = internal110s. Padre118s > internal110s + cleanup5s. CDP acotado por fase/global, click2s/evento; deadline interno de emergencia. El padre termina su hijo propio con handle y espera cleanup. SENT nunca se degrada por salida/error ni por deadline padre.

Trace fsync con UTC y reloj monotónico registra intent, press/release start/end, probes y decisiones, SENT, espera/captura de respuesta, timeout y cleanup. El padre registra su espera/timeout/terminación. Sin prompt completo en trace ni resultado de consultas; sólo hashes y IDs. Unicode-roundtrip de prueba conserva su fixture público.

El envío usa un botón único, visible, habilitado y comprobado por hit-test, composer estable y un único par físico con buttons/pointerType explícitos. No hay fallback. Una conversación nueva reutiliza sólo la pestaña del perfil dedicado y evita sobrescribir el composer histórico.

Pruebas: ocho casos de delivery/UTF-8/identidad/plazos/traza; 13 domain; 41 human reconciliation; ocho idempotency; cuatro input único; timeout real de hijo y cleanup. Código de reconcileObservation automático intacto. Evidencia: evidence/f24-frontiers-20261014/chatgpt/.

B — WEB_HANDOFF = PASS determinista. El plan puede declarar research (URL HTTPS explícita y diagnose_before_fetch). Runner ejecuta diagnóstico Worker sin modificar fuentes, comprueba FAIL inicial, hace fetch gobernado con proceso propio y entrega un envelope inline acotado/sanitizado con ruta absoluta, SHA y nonce. No depende de glob. Sólo salida producida por el modelo que use nonce y SHA certifica WEB_RESULT_READ; echo de input/tool no basta. Completion Gate requiere evidencia ligada al SHA actual. El dato web no otorga permisos. Nuevos runs aprueban los nuevos hashes; las aprobaciones antiguas quedan como registros históricos, sin alterarlas.

Test sandbox: servidor HTTP propio → payload recibido por consumidor determinista en proceso separado → marcador/SHA utilizados; input echo y cambio de fuente DENY; cleanup del servidor PASS. No se atribuye esta prueba a Qwen real: ATTEMPT4 deberá demostrarlo con Qwen.

Se detectó que verify-runner-syntax.ps1 tiene destino histórico fijo; se restauró sólo su salida regenerada mediante Git y no se vuelve a usar ese destino para estas pruebas. Los smokes nuevos guardan evidencias en la carpeta de fronteras.
C — RECOVERY_CONTINUATION = PASS en sandbox: crash propio real, Watchdog, limpieza, corrupción controlada de STATE/current+previous, restauración desde checkpoint íntegro y START-Recover real. Worker/tests continuaron; reloj original intacto, cleanup PASS. Backend probe explícito: su terminal FAILED es intencional y no acredita E2E live.

El harness nuevo exige START-Recover ANTES de ChatGPT. Un boundary de crash aprobado sólo para sandbox espera con Tick y reloj global activo, evitando la carrera con Reviewer. El consultor es ahora un proceso administrado por Runner, después de checks tras recovery y antes de Reviewer; conserva heartbeat/Job Object y no genera otra inferencia. El estado comparte el mutex de presupuesto existente para preservar reservas frente al STATE cacheado de Runner. Smoke concurrente de reserva PASS. El retry lógico se verifica en el paso administrado sin envío adicional. Completion requiere consumo web y consulta/respuesta/idempotencia reales.

ATTEMPT4 exige todos esos gates y 2700s/restart2/maxcycles5. No se modifican relojes ni ledgers anteriores.
Regresión conjunta PASS: estados/idempotencia/human/domain/UTF-8, syntax, Runner/Watchdog/checkpoint/recovery, presupuesto concurrente, Inference Lock real entre procesos y cleanup. Modelo y hashes de seguridad preservados. ATTEMPT4 autorizado por gate, aún no iniciado al certificar estas fronteras. NO PUSH; F25/F27/F28 no iniciadas. Sin dependencias nuevas ni actualizaciones.
