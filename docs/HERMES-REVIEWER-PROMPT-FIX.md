# Transporte del Reviewer y cierre F23 — 2026-10-14

Fix PASS. F23 PASS. Macrofase 8 IN_PROGRESS. F24–F26 pendientes de ejecución; F27/F28 no autorizadas.

PowerShell 5 alteraba el prompt en la invocación nativa `hermes.exe --print-runtime-command -- @argList`. La reproducción sin inferencia demuestra que el SHA-256 del argumento recibido era distinto. El wrapper volvía a construir una línea de argumentos para Python con ese contenido ya alterado. El Reviewer histórico terminó en argparse, ExitCode 2, antes de realizar una revisión técnica.

La CLI congelada v0.21.6 ofrece `chat --query-file -`. El wrapper de los modos `chat` y `chat-stream-json` ahora envía bytes UTF-8 por stdin y cierra el pipe sin añadir una nueva línea. El contenido no aparece en argv. La codificación se configura dentro de Python porque el runtime oficial usa `-I`. Se preservan CRLF, comillas y Unicode. El timeout incluye la escritura del pipe; el job propio se cierra también ante fallo/timeout. No se modificó Hermes instalado ni el modo superior legacy `-z`.

El test determinista usa el parser y lector stdin instalados sin cambios. Intercepta solamente el límite posterior a la lectura para comparar contenido/SHA sin inferencia. Incluye texto multilínea, JSON anidado, diff, opciones aparentes, rutas con espacios, `& | > <`, expansión aparente de shell, comillas, áéíóú ñ ¿? € ° y CRLF. Reviewer y Supervisor PASS; ARGPARSE_ERROR false; PROMPT_INTEGRITY PASS; UTF8 PASS. Timeout de proceso nativo PASS.

El Reviewer real se ejecutó sobre el prompt original y el sandbox `sandbox/f23-full-feac8aea/project`, antes de cualquier edición del resultado del Worker. Devolvió `{"decision": "ACCEPTED"}`. Perfil sin herramientas/MCP/plugins, hash aprobado, archivos del proyecto intactos. Tests/build se revalidaron sobre el mismo resultado y el Completion Gate autoritativo devolvió COMPLETED con todos sus checks PASS.

Esta continuación fue mantenimiento explícitamente autorizado y limitado a 600 segundos. No se reinició el Runner completo ni se reiniciaron contadores: RESTARTS.json y el reloj histórico permanecieron intactos. Se preservaron Supervisor/Worker exitosos, consulta ChatGPT completada, Prepare/Path Guard, web y recuperación real de la ejecución anterior. No hubo nuevos envíos ChatGPT ni nuevas invocaciones del Worker. La evidencia operativa previa se copió antes de actualizar STATE y generar el nuevo reporte mediante los mecanismos existentes.

Smokes PASS: transporte Supervisor, invocación nativa Qwen 0.25.1 mediante su wrapper, aislamiento Reviewer, exclusión cross-process del Inference Lock, liberación física del mutex, UTF-8, hook/plugin SHA y sanitización de secretos. Componentes protegidos, modelo y llama-server conservan hashes aprobados. Hermes conserva commit 818c13be1dc4fd28987e1e881a9408224afd4535. qwen36 / 127.0.0.1:8080 / ctx 65536 / parallel 1 intactos. Dependencias nuevas: ninguna.

Continuación real: 98,78 segundos. RAM libre mínima 279,45 MiB; pagefile máximo usado 2,398 GiB; VRAM máxima 7092 MiB. El umbral de 3 muestras consecutivas cada 5 segundos bajo 150 MiB no se activó. Estos valores no certifican estabilidad prolongada. El mínimo histórico de la corrida anterior, 68,64 MiB, permanece registrado sin cambios.

Cleanup PASS: job cerrado, cero procesos propios supervivientes, lock del run eliminado, mutex del run liberado e Inference Lock FREE. Chrome dedicado preexistente se conserva abierto. Evidencia: `evidence/hermes-prompt-transport-20261014/`; gate consolidado `fix-and-f23-gate.json`; hashes históricos completos verificados. Los FAIL anteriores y sus reportes permanecen intactos.

Próximo gate autorizado: F24 real de 15–45 minutos; después F25 de 2 horas, 4H si corresponde y F26. READY FOR REAL PILOT NO hasta completar los gates requeridos. NO PUSH.
