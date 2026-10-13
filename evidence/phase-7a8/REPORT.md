# 7A.8 — Native Dashboard: PASS

invoke-native-dashboard.ps1 inicia el app FastAPI y SPA originales congelados de
Hermes en 127.0.0.1:9119 (puerto central configurable). Superficie administrativa
completa, tratada como tal: su adapter ASGI externo solo admite lecturas explícitas
y rechaza TODAS las mutaciones durante el contrato autorizado. WebSockets/terminal,
update, restart, OAuth callbacks, perfiles externos, archivos, catálogo y plugins
no aprobados también son DENY. No se modifica Hermes ni security.yaml.

La UI real mostró Config (qwen36/65536/hooks autoaccept false), MCP y Cron del
perfil default aislado. Save devolvió rechazo visible. El selector All profiles
es bloqueado; seleccionar default permite leer jobs. Paneles/catálogos bloqueados
no se certifican como operables. El Dashboard no habilita nuevas inferencias.
/api/da/state lee STATE.json real y el contrato se revalida en cada request.

El wrapper finito usa Job Object y handshake del PID hijo antes de bind/imports;
ambos procesos son owned y se esperan sus handles antes de declarar cleanup.
DASH-001/002/003 PASS: HTTP/UI reales; 10 ataques administrativos DENY; loopback
exclusivo, hashes/contrato intactos; terminación forzada y lectura de STATE sin UI.
Timeout 2s del wrapper con cleanup PASS. Runner no depende de este componente.
Correcciones: usar venv nativo para bootstrap; ruta STATE antes del catch-all SPA;
admitir únicamente selector default; esperar salida real del hijo tras kill.
Evidencia: evidence/phase-7a8/. FastAPI/uvicorn y SPA ya instalados; cero deps nuevas.
