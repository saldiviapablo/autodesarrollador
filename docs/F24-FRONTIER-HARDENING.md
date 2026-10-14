# Fronteras antes de F24 ATTEMPT 4

ATTEMPT 3: HISTORICAL FAIL / BLOCKED_REQUIRES_HUMAN. Su consulta y ledger no se reenvían ni se reconcilian. Se preservan 419 archivos históricos por SHA-256.

A — CHATGPT_BRIDGE_FIX = PASS (tests deterministas, cero mensajes reales).
SENT_CONFIRMED es irreversible y retry devuelve ALREADY_SENT incluso con RESPONSE_PENDING. La confirmación exige user +1, SHA y conversación exacta; el caso de conversación nueva sólo admite transición explícita desde baseline 0/0 a un ID nuevo que queda vinculado. Composer vacío es una señal adicional. Los estados históricos no se migran.

Presupuesto respuesta60s: readiness15 + prepare15 + click4 + confirmación12 + respuesta60 + finalización4 = internal110s. Padre118s > internal110s + cleanup5s. CDP acotado por fase/global, click2s/evento; deadline interno de emergencia. El padre termina su hijo propio con handle y espera cleanup. SENT nunca se degrada por salida/error ni por deadline padre.

Trace fsync con UTC y reloj monotónico registra intent, press/release start/end, probes y decisiones, SENT, espera/captura de respuesta, timeout y cleanup. El padre registra su espera/timeout/terminación. Sin prompt completo en trace ni resultado de consultas; sólo hashes y IDs. Unicode-roundtrip de prueba conserva su fixture público.

El envío usa un botón único, visible, habilitado y comprobado por hit-test, composer estable y un único par físico con buttons/pointerType explícitos. No hay fallback. Una conversación nueva reutiliza sólo la pestaña del perfil dedicado y evita sobrescribir el composer histórico.

Pruebas: ocho casos de delivery/UTF-8/identidad/plazos/traza; 13 domain; 41 human reconciliation; ocho idempotency; cuatro input único; timeout real de hijo y cleanup. Código de reconcileObservation automático intacto. Evidencia: evidence/f24-frontiers-20261014/chatgpt/.

B — WEB_HANDOFF = PENDING.
C — RECOVERY_CONTINUATION = PENDING.
Regresión conjunta y F24 ATTEMPT 4 todavía no ejecutados. NO PUSH; F25/F27/F28 no iniciadas. Sin dependencias nuevas ni actualizaciones.
