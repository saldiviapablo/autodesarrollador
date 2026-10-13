# Watchdog — F18 PASS

Observer independiente controla birth identity del Runner, heartbeat y diagnóstico.
Si el padre suspendido no vuelve a emitir heartbeat, persiste FAILED y reporte;
solo entonces termina ese PID/birth identity. El cierre kernel del Job Object
elimina descendientes y modelo propios. No hay reinicio infinito del padre.

Dentro del Runner, health perdido, proceso de agente caído y deadline producen
teardown del Job Object de la fase, retry presupuestado y recuperación desde STATE
por protocolo existente. Modelo EXTERNAL perdido: BLOCKED_REQUIRES_HUMAN, no
apropiación. Reinicios persistidos en RESTARTS.json, incluidos al recuperar el run.
No-progress >=3 produce STALLED. Mutex kernel abandonado es recuperable.

Pruebas: procesos REALES llama-server PID27100, Hermes Python PID14084 y Qwen
Node PID33508 terminados por identidad/ancestry registrada. Pipeline recuperado:
llama1/supervisor1/worker1/reviewer0. Heartbeat stale mediante suspensión del padre
propio; observer diagnostica y termina, STATE FAILED. Límite1 observado y no excedido.
Evidencia evidence/phase-18/. Cero nuevos paquetes, updates o cambios Windows globales.
Reader del harness corrige PermissionError transitorio durante File.Replace;
inyecciones se persisten antes de matar. Writer reintenta sharing violation con
límite6; budgets no se reinician al volver desde disco. Fuente: tests y filesystem.
