# 7A.4 — Native Browser

PHASE: 7A.4. STATUS: funcional, seguridad, fallo/timeout, cleanup, integración real y smoke PASS; commit local requerido antes de 7A.5.

CHANGES: backend built-in de Hermes v0.21.6 (`browser.backend: off` desactiva el backend Browser Use CLI y selecciona los browser_* built-in); Chromium local/headless, dominios exactos, contexto nuevo sin perfil/cookies personales, política de acciones default DENY. Se usa agent-browser 0.26.0 ya instalado. Navegación/snapshot/get y launch/close permitidos; evaluación, uploads, downloads, estado y otras acciones DENY.

La documentación [oficial de seguridad](https://agent-browser.dev/security) se contrastó con pruebas en la versión instalada: el backend rechazó example.com y la evaluación. Las restricciones de red del navegador no se presentan como un firewall del sistema operativo; no se habilita un provider cloud ni se certifican perfiles adjuntos. El bridge de ChatGPT conserva su perfil/domain-lock separado.

TESTS: T-7A-BROWSER-001 navegación real y snapshot de la documentación JSON de Python PASS; 002 wrapper y backend deniegan dominios/subdominios/HTTP/URLs inválidas y eval PASS; 003 cero procesos/temporales activos PASS; 004 timeout real con cierre de árbol PASS; 005 Hermes real usa browser_navigate y obtiene snapshot/resultado SUCCESS usando qwen36 local y el Inference Lock PASS. live-tool-result-validation.json valida el encabezado JSON real de success/URL. El formatter nativo stream_json.py limita cada output de tool a 5000 caracteres y puede truncar el snapshot; el snapshot completo se verifica por separado en 001. No se presenta la traza truncada como JSON completo.

GOVERNANCE: profile-governance.json verifica que modelo, hooks, auto-accept=false, MCP, plugins, memoria y skills existentes no cambiaron. El perfil externo de Hermes se modificó sólo para esta integración, con backup anterior y justificación registrados. Los parámetros 127.0.0.1:8080, qwen36, ctx 65536 y parallel 1 permanecen intactos. Los hashes aprobados del hook/MCP/plugin y security.yaml no se alteraron.

CLEANUP: el backend nativo devolvía sin dejar sesiones en memoria pero inicialmente dejó un auxiliar y temporales. Se recuperó únicamente el PID identificado por parentesco, tiempo de inicio y binario. Un Job Object Windows por worker, asignado antes de permitir spawn, garantiza la terminación de descendientes al finalizar/abortar. Se reutiliza este cierre en invoke-hermes sin alterar la serialización. El Python del store evita el redirector Windows del venv; usa las mismas dependencias ya instaladas. El padre limpia sólo su directorio PID y el ready-file. Dos temporales previos fueron archivados en backups/phase-7a4-20261013-023156/legacy-native-temps tras un rechazo de aprobación automática del borrado recursivo. No se borraron backups.

AUTOCORRECTIONS: selección explícita de backend built-in y Chromium existente; API pública browser_console para el test de evaluación; acción launch necesaria en la política restringida; UTF-8/PowerShell 5.1 en integración; supervisión de procesos y handshake de startup; propiedad cleanup_ok en respuestas DENY. Los intentos de inspección fallidos se conservan.

REGRESSION: hook, sanitización, MCP health/allowlist, plugin SHA-256, ChatGPT domain/UTF-8 (implementación sin cambios), cleanup y vinculación documental con contrato/estado PASS. No se repiten suites completas de 7A.1/7A.2. La inferencia de la prueba real se mantuvo serializada. El llama-server PID registrado pertenece al run global de Macrofase 7A y permanece activo para las siguientes llamadas; debe cerrarse al finalizar o bloquearse el run.

DEPENDENCIES: ninguna instalación nueva; únicamente se registran agent-browser/Chromium/Node/Python que ya estaban presentes. Job Object usa .NET/Win32 incluido en Windows. No drivers, Registry, firewall ni configuración global modificados. No push.

EVIDENCE: T-7A-BROWSER-001..005.json, native-probe.json, hermes-live-integration.json, live-tool-result-validation.json, profile-governance.json, regression-smoke.json, backup-manifest.json y registro de ownership de inferencia en runtime/macro7a-llama-owner.json.

NEXT PHASE: 7A.5 tras commit/Git limpio. Macrofase 7A sigue IN_PROGRESS; READY FOR 7B=NO.
