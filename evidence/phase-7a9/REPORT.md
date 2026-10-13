# 7A.9 — Gateway sandbox: PASS

Gateway inicial es unidireccional y no concede autoridad a mensajes externos.
gateway-notify.py deriva event/run_id/status de STATE y RUN-CONTRACT reales; no
acepta texto/comandos libres. Solo admite destino HTTP 127.0.0.1 con puerto
explícito para este sandbox; no sigue redirects. Usa el transporte aiohttp ya
instalado de Hermes, timeout 3s, ninguna credencial persistida ni inferencia.

El WebhookAdapter nativo v0.21.6 certifica HMAC de requests reales. El handler
de pruebas clasifica toda entrada como UNTRUSTED y nunca despacha agentes, incluso
si estuviera firmada. Mensaje sin firma: 401 DENY. Listener efímero loopback.
GATEWAY-001 y 002 PASS: mock recibe una única alerta RUN COMPLETED derivada de
estado de fixture completada; targets alternativos DENY; timeout y cleanup PASS.

El adapter nativo genérico recibe webhooks y entrega a plataformas registradas;
su send genérico no implementa POST hacia una URL arbitraria. Por eso la salida
mock usa el adapter HTTP determinista explícito, conservando autenticación nativa
en la prueba entrante. No se certifican Telegram/Discord/Slack sin credenciales.
Los futuros transportes externos deberán pasar sus gates antes de habilitarse.
No se inicia daemon persistente ni integración Runner de 7B. Dependencias nuevas: 0.
Evidencia: evidence/phase-7a9/. Próxima subfase: controlled canary update 7A.10.
