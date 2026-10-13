# ChatGPT Bridge Idempotency — PASS

La reserva por consultation_id usa create-exclusive cross-process, hash de prompt
y fsync ANTES de tocar el composer. El registro no almacena prompts, respuestas
ni credenciales. Una lease serializa acciones del navegador; un propietario muerto
se recupera sin matar procesos por nombre. Un registro corrupto es UNKNOWN_DELIVERY.

ID completado: ALREADY_SENT / no_resend. ID reservado, intento, crash o timeout:
UNKNOWN_DELIVERY / no_resend. Jamás se elimina automáticamente la reserva ni se
repite Send. La acción reconcile solo observa el chat: exige SHA-256 del último
mensaje, user +1, assistant +1 y ausencia de streaming antes de marcar completado.
Si la pestaña cambió, está virtualizada o falta evidencia, conserva UNKNOWN_DELIVERY.
No adivina NOT_SENT ni reenvía. El consumo de presupuesto ocurre antes del intento;
un retry reconocido no consume otro intento, incluso con presupuesto agotado.

El contador soporta los roles/articles anteriores y los wrappers exteriores de
mensajes DIL actuales reflejados en el documento HTTPS de chatgpt.com. No se adjunta
al iframe de cdn.platform.openai.com. La validación del composer se repite dentro
del mismo evaluate que envía, bajo hostname EXACTO antes/después de cada acción.

T-CHATGPT-010 real PASS: normal SUCCESS, retry ALREADY_SENT; deadline 1s causa
UNKNOWN_DELIVERY, retry permanece UNKNOWN, reconcile da ALREADY_SENT sin Send.
Ambos IDs: user/assistant exactamente +1. UTF-8 y domain lock PASS. Unit tests:
8 procesos → 1 reserva; segundo intento/turn gate/corrupt/path/fingerprint DENY.
Budget PASS; cleanup CDP SUCCESS y puerto cerrado. Deps nuevas: ninguna.

Primer intento real: nuevos wrappers de UI no tenían role/articles y el padre
expiró; se conservó evidencia y se reconcilió su ID sin reenviarlo. También se
corrigieron el nombre de acción cleanup y una carrera de cierre WebSocket de
Node Windows. Evidencia: evidence/chatgpt-idempotency/, incluyendo attempt-1/.
Backups previos: backups/chatgpt-idempotency-*/. Próximo: regression gate global.

Persistencia de cuota: el campo opcional chatgpt de STATE ahora tiene ambos
contadores requeridos, enteros 0–5 y additionalProperties=false. Se preservan
todas las restricciones anteriores; RUN-CONTRACT no cambia. La omisión de ese
campo en el esquema impedía persistir la cuota que el wrapper ya contemplaba.
Estado inválido DENY. Mutex cross-process por STATE serializa reserva de cuota
y eventos: 4 callers mock, max2, exactamente 2 permitidos y 2 bloqueados; cero red.
Pruebas de compatibilidad del esquema y persistencia real por State Manager PASS.
