# Certificación del contador de turnos ChatGPT — 2026-10-15

Estado: **PASS**, limitado al extractor DOM y su regresión. F24 ATTEMPT 6 conserva su FAIL histórico. No se ejecutaron F24, ATTEMPT 7 ni F25.

El contador anterior seleccionaba la primera familia con nodos DOM, aunque fueran residuos sin layout, y `clearOwnedComposer()` duplicaba esa selección. Esto causó el falso baseline 1/1 en la raíz después de Nuevo chat. La evidencia original permanece en `evidence/phase-24-attempt-6-20261014/turn-visibility.json`.

`tools/chatgpt-conversation.js` centraliza `isRenderedConversationTurn()`, `conversationTurns()` y la lectura de cantidades/textos. Descarta elementos desconectados, atributos hidden/aria-hidden/inert en el elemento o sus ancestros, display:none, visibility:hidden/collapse y ausencia de ClientRects con área positiva. No exige pertenecer al viewport. Cada familia se filtra antes de decidir usarla; el fallback conserva la deduplicación exterior. Lectura y rollback inyectan las mismas funciones. Los predicados de recuperación, reconciliación, entrega, actuador y disponibilidad de Nuevo chat permanecen intactos.

El nuevo módulo se agrega a los listados de componentes que deben sellarse en aprobaciones futuras. No se alteraron hashes ni aprobaciones de runs anteriores. Backups registrados en `backups/chatgpt-turn-layout-20261015/MANIFEST.json`; sin dependencias nuevas.

Los casos A–J y comprobaciones adicionales pasan: residuos de ambas familias, fallback/deduplicación, turnos fuera de pantalla, atributos/estilos en elemento y ancestros, desconexión/área cero, textos UTF-8, lectura real del bridge y rollback con baseline 0/0 y 1/1. Un cambio real de baseline sigue bloqueando el rollback. La transición de `requestFreshChat()` se prueba con DOM simulado, sin navegar ni enviar. Las suites existentes transaction/pre-send, fresh-chat, delivery, send actuator, single physical click, domain lock, idempotency, human reconciliation y UTF-8 pasan.

La inspección real sólo leyó el Chrome dedicado PID 16576 y verificó su perfil persistente. URL `https://chatgpt.com/`, raw user/assistant 0/0, active 0/0, composer único, editable y vacío, sin streaming. Los residuos anteriores ya no estaban presentes; su reproducción queda cubierta por pruebas deterministas. La función real `readConversation()` coincide con el extractor inspeccionado.

Hay una distinción conservada: la raíz vacía satisface `emptyConversation()`, pero `freshReady()` además exige foco o control local disponible. La observación real carecía de ambos. No se cambió el foco para forzar ese guard. `FRESH_CHAT_READY_LIVE=false`; la transición a READY está certificada determinísticamente. `live-readonly-initial.json` conserva el primer diagnóstico, que falló por exigir READY en la observación sin foco; se corrigió la expectativa del certificado, sin cambiar el guard productivo. `live-readonly.json` separa explícitamente baseline real de readiness simulado.

Evidencia: `evidence/chatgpt-turn-layout-20261015/`, incluidos `conversation-deterministic.json`, `REGRESSION.json`, `live-readonly.json`, `INTEGRITY.json` y `CERTIFICATION.json`. Los ledgers históricos y las evidencias anteriores se verifican por SHA-256; no se instanciaron ledgers ni leases durante la inspección real. Cero clicks, escritura de composer, borrado o envíos reales. Chrome permanece abierto.

Reproducción determinista con directorio de evidencia nuevo y explícito:

```powershell
$env:F24_PREFLIGHT_E = Join-Path $PWD 'evidence/<nuevo-certificado>'
New-Item -ItemType Directory -Path $env:F24_PREFLIGHT_E
C:/Python314/python.exe tests/certify-chatgpt-conversation.py
```

La inspección opcional read-only requiere ese certificado determinista PASS y el Chrome dedicado ya abierto: `node tests/inspect-chatgpt-turns-readonly.js`. No inicia el bridge principal ni modifica la página.
