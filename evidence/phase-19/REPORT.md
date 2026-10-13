# F19 — Launcher único y STOP

BAT solo invocan launch.ps1 y stop.ps1, con PROJECT_ROOT entre comillas.
Launcher hace preflight y muestra el digest para una sola aprobación APROBAR
cuando falta receipt. Unattended devuelve BLOCKED_REQUIRES_HUMAN sin esperar input.
STOP escribe .autopilot/STOP con run_id. Runner detecta en su loop, guarda STATE,
checkpoint, reporte básico y cierra su Job Object; no mata procesos por nombre.

Prueba real de ambos BAT en ruta con espacios: watchdog iniciado, stop controlado,
ABORTED, checkpoint/estado persistidos, LOCK liberado. T-STOP-001 PASS.
El harness usa cmd /d /s /c con quoting Win32 explícito; listas de argumentos de
Python no equivalen al quoting de cmd para nombres BAT con espacios.
Evidencia evidence/phase-19/. F20 agrega gate completo antes de aceptar COMPLETED.
