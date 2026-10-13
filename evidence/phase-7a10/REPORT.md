# 7A.10 — Controlled Auto-update simulation: PASS

controlled-update.py archiva el árbol completo del commit Hermes congelado oficial,
verifica origen/HEAD limpio y SHA-256 del archivo, conserva copias verificadas de
componentes protegidos y ejecuta el smoke sobre código NATIVO del candidato.
Comprueba path allow/escape/traversal/control chars y compilación de cinco entrypoints.
Solo tras PASS promueve un marcador de versión SIMULADO dentro de sandbox/canary-update.

UPDATE-001 PASS. UPDATE-002 inyecta regresión real al path guard del candidato:
el smoke obtiene FAIL (escape dejó de ser DENY) y revierte automáticamente el
marcador a la versión congelada. FAIL inyectado es el resultado esperado de esta
prueba, no un gate fallido. Se verifica que los hashes productivos no cambiaron.
Finally restaura/retira marcador y mueve candidato a backup recuperable; ningún
directorio candidato permanece activo. Sin descarga, instalación o hermes update.
VERSIONS.lock y Hermes v0.21.6/818c13b permanecen intactos. Cero nuevas dependencias.

La certificación corresponde a la simulación canary definida en 06. Un upgrade
productivo real requiere una tarea de mantenimiento, versión/origen/hash concretos
y el mismo gate sobre el candidato efectivo; este script no ofrece promoción live.
Evidencia: evidence/phase-7a10/. Próximo gate: ChatGPT Bridge Idempotency.
