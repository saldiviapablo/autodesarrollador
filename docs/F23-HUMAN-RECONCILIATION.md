# F23 — reconciliación humana de entrega no ocurrida

Solicitud humana del 2026-10-14: el composer contenía la consulta completa,
el botón seguía disponible y la conversación tenía cero turnos de ambas partes.
Conclusión autorizada: DELIVERY_NOT_OCCURRED. Se mantuvo el ID
f23-ee298529568f4f8b94f4dd16f90a0be4 y su reserva lógica original.

El ledger anterior sólo permitía negar todo nuevo intento después de uno ambiguo.
Se añadió confirmNotDelivered al mecanismo existente: exige receipt explícito
HUMAN_VISUAL_RECONCILIATION, ID y hash de prompt iguales, cero turnos, ausencia
de streaming, composer idéntico y un botón habilitado. Guarda el historial y
NOT_DELIVERED_CONFIRMED / RETRY_SAFE con una sola habilitación. No resetea el
contador previo. La habilitación se consume antes de la única nueva operación
física; otra ambigüedad queda bloqueada y no habilita más retries.

El retry usa el composer ya existente, sin insertar ni duplicar texto. Verifica
perfil real mediante PID propietario de CDP y user-data-dir, hostname exacto
HTTPS chatgpt.com, baseline de turnos sin cambios, contenido/UTF-8, sanitización,
presupuesto original y ledger. La operación física es un solo click sobre el
único botón visible y habilitado, identificado como Enviar. No utiliza el
fallback sintético que no produjo entrega en el intento anterior.

Resultado real: SUCCESS, user 0→1, assistant 0→1, respuesta capturada y composer
vacío. Budget queries_used permaneció 1. Ledger COMPLETED con send_attempts=2:
la intención histórica ambigua más el intento nuevo autorizado. Un solo nuevo
envío físico; una sola consulta lógica.

Retry lógico del mismo ID: ALREADY_SENT, contador sin cambio y 0 envíos nuevos.
Historial humano y UNKNOWN_DELIVERY original conservados. La prueba determinista
también comprueba receipt/observación inválidos, replay del receipt, segundo
retry prohibido y gate exacto de turnos. Domain lock estricto y tests anteriores
de idempotencia PASS. No se modificaron políticas, hooks, Inference Lock ni
integridad nativa MCP/plugin. Cero dependencias nuevas.

Evidence nueva: evidence/f23-human-reconciliation/. Backups:
backups/human-reconciliation-20261014-003811/. Las evidencias de intentos anteriores
se preservan mediante bindings SHA-256 en esta carpeta; no se reescribieron.

F23 se reanuda en el mismo sandbox y RUN-CONTRACT; scripts/resume no vuelven a
consultar ChatGPT, preparar el proyecto ni repetir A–J. Permanecen pendientes
los agentes reales, tests/build, recuperación y Completion Gate. Esta
reconciliación PASS por sí sola no declara F23 completa PASS.
