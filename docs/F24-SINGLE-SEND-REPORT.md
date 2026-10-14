# F24 — único envío físico autorizado

Consulta f24-7257c739e1fd449aae1f1f93856aef7f, conversación
6acefadc-36b8-83e8-9172-7e3e9421dc21. Autorización humana explícita para consumir
únicamente el retry reconciliado; sin nuevo ID, conversación o inserción de texto.

```text
PRECHECK = PASS
PHYSICAL_SEND = 1
USER_TURNS = 1→2
ASSISTANT_TURNS = 1→2
COMPOSER_EMPTY = YES
RESPONSE_CAPTURED = YES
LEDGER_FINAL = COMPLETED
LOGICAL_RETRY = ALREADY_SENT
ADDITIONAL_SENDS = 0
HUMAN_RETRY_REMAINING = 0
READY_TO_RESUME_F24 = YES
```

Precheck: ledger idéntico al snapshot certificado, receipt/proof SHA vinculados,
ID/conversación HTTPS chatgpt.com exactos, mismo perfil HERMES-CHATGPT, una pestaña,
baseline/current 1/1, composer completo SHA esperado, UTF-8/sanitizer PASS,
sin streaming, botón visible único habilitado, retry disponible 1 y presupuesto
original 1/5. Timeout conservado de la consulta F24 original: 60 segundos.

El bridge gobernado usó el composer existente, consumió la habilitación antes
de mousePressed/mouseReleased y realizó un único click físico sin fallback.
Ledger: NOT_DELIVERED_CONFIRMED → DELIVERY_INTENT → SENT → COMPLETED;
SENT con message_confirmed=true equivale a SENT_CONFIRMED. Historial anterior
conservado. send_attempts=2 incluye intención ambigua histórica y el intento
físico nuevo; no son dos mensajes F24 entregados.

Respuesta capturada con hash igual al ledger, guardada en response.txt y en
el artefacto nativo .autopilot/evidence/CHATGPT.json. Conversation ID intacto.
Retry lógico del mismo ID salió antes de navegador/budget: ALREADY_SENT;
ledger y STATE idénticos antes/después, cero envíos adicionales, token consumido.

STATE y presupuesto permanecen sin cambios, 1/5. Se añadió exclusivamente un
evento nativo CHATGPT_CONSULTED al historial del run. Integridad de componentes
y evidencias previas PASS; lease liberada, procesos propios finalizados.
Chrome del usuario permanece abierto. No inferencia local, dependencia nueva,
actualización, modificación de políticas ni push.

F24 E2E sigue sin certificarse. READY_TO_RESUME_F24 sólo significa que esta
consulta ya no bloquea una continuación posteriormente autorizada. Reviewer,
Completion Gate y F25 NO ejecutados. F27/F28 NO iniciadas. Detenido.

Evidencia: evidence/f24-human-send-once-20261014/. Backup:
backups/f24-human-send-once-20261014/. El harness temporal está archivado como
single-send-harness.txt; el marcador exclusivo de ejecución se conserva.
