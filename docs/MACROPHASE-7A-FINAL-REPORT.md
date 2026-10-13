# Informe final — Macrofase 7A

MACROFASE 7A = PASS. READY FOR 7B YES. 7B y 8 permanecen PENDING; no se iniciaron.

| Gate | Estado | Evidencia |
|---|---|---|
| 7A.1 Memoria + Skills | PASS | evidence/phase-7a1/ (conservada; suite no repetida) |
| 7A.2 MCP + Plugins | PASS | evidence/phase-7a2/ (conservada; suite no repetida) |
| 7A.3 Document Extraction | PASS | evidence/phase-7a3/ |
| 7A.4 Native Browser | PASS | evidence/phase-7a4/ |
| 7A.5 Bot Mode + Subagents | PASS | evidence/phase-7a5/ |
| 7A.6 Git Worktrees | PASS | evidence/phase-7a6/ |
| 7A.7 Cron + No-Agent Jobs | PASS | evidence/phase-7a7/ |
| 7A.8 Web Dashboard | PASS | evidence/phase-7a8/ |
| 7A.9 Gateway sandbox | PASS | evidence/phase-7a9/ |
| 7A.10 Controlled Auto-update | PASS | evidence/phase-7a10/ |
| ChatGPT Idempotency | PASS | evidence/chatgpt-idempotency/ |
| Regression global | PASS | evidence/regression-7a-final/FINAL-GATE.json |

## Pruebas y control de seguridad

38 pruebas obligatorias de las diez subfases auditadas contra evidencias reales,
67 comprobaciones de integridad actuales y 11 gates ejecutables globales PASS.
Configuración central, security guard (11 comandos destructivos DENY, path,
junction, secret redaction, policy intersection), lock (exclusión, crash, timeout,
metadata), domain lock Node/PowerShell, smoke MCP/plugin/hook, extracción/browser,
roles/worktree, cron/dashboard, esquema de STATE y recovery/delegation PASS.
Recuperación real desde STATE.previous tras corrupción confinada al sandbox:
checkpoint SHA-256 válido, RECOVERED y RUNNING. Qwen Code real corrigió suma;
test fixture no modificado y comprobación independiente de la función PASS.
No se repitieron suites completas de subfases aprobadas; se conservaron sus pruebas
y se ejecutaron regresiones acotadas y controles de integridad actuales.

7A.10 usó snapshot completo del árbol Hermes congelado, archivo SHA-256 y copias
protegidas verificadas. Smoke PASS precedió promoción de marcador SIMULADO; se
inyectó regresión real en el path guard del candidato, smoke FAIL esperado y
rollback automático PASS. Candidato archivado y marcador retirado. Cero updates
productivos; Hermes v0.21.6/818c13be1dc4fd28987e1e881a9408224afd4535 intacto.

Idempotencia real: consulta SUCCESS, retry ALREADY_SENT sin Send; deadline 1s
UNKNOWN_DELIVERY, retry UNKNOWN sin Send, reconcile ALREADY_SENT. Ambos casos:
user +1, assistant +1, UTF-8/domain PASS. Reserva cross-process fsync: 8 callers,
1 reserva. Cuota de STATE serializada: 4 callers mock, max2, 2 grant/2 DENY; cero
red. Esquema opcional limitado a enteros 0–5 y propiedades cerradas; todas las
restricciones anteriores y RUN-CONTRACT preservados. Estado inválido DENY.

## Cleanup, hashes y versiones

Llama-server propio PID 27484 identificado por ruta/start time/argumentos, health
OK y alias qwen36 antes de detenerlo. Cero auxiliares observados, puertos
8080/9119/9222 cerrados, mutex libre y RELEASED, lease/temp/ready files ausentes.
Cero procesos desconocidos terminados. Checkpoints inmutables conservados.
Modelo completo 20.419.565.568 bytes verificado contra SHA-256 aprobado
671e47e0ec53c665d048b98c3ecbfd5236b5ca9c3e02ed19fc8f81f7b85140c7.
Hooks, MCP, plugin/manifest, módulos nativos y guardrails íntegros. Parámetros
qwen36, 127.0.0.1:8080, ctx65536, parallel1 preservados; inferencia serializada.
Versiones reales: llama.cpp build11368/1fb7ef3e3, Node24.14.1, Python principal3.14.4,
Python Hermes3.14.7, Qwen Code0.25.1, Hermes0.21.6. VERSIONS.lock canónico.
Dependencias nuevas: ninguna. Instalaciones/actualizaciones: ninguna.

## Problemas encontrados y corregidos

Preflight: estados documentales incoherentes y domain lock permisivo; corregidos
sin reescribir snapshots históricos. Extracción: API/contexto nativo, UTF-8 y
cleanup de parser. Browser: backend built-in, Chromium y policy explícitos,
Job Object y handshake; temporales anteriores archivados recuperablemente.
Roles: Supervisor con tools violaba separación; perfil sin tools y Qwen worker
principal, hijo síncrono, metadatos de timeline originales conservados.
Worktree: esquema real del contrato, gate ligado a commit/diff, backup dirty.
Cron: API devuelve job_id; job parcial retirado por ID verificado.
Dashboard: bootstrap nativo, orden de catch-all, selector default y espera del
hijo antes de declarar cleanup. Idempotencia: cambio de wrappers de la UI real
de ChatGPT, cierre WebSocket Windows, acción close-browser, campo quota ausente
del esquema y su persistencia serializada. Primer envío ambiguo reconciliado sin
reenviarlo. Intentos fallidos se conservan como historia; no son gates vigentes.
Un fallo de quoting del harness independiente se corrigió sin modificar el worker.

## Límites del alcance aprobado

Documentos con OCR/scans no certificados; roles auxiliares context-only sin tools;
hijos finitos síncronos; worktrees y cron certificados en sandbox; scheduler
persistente/Runner quedan para7B. Dashboard administrativo nativo aislado,
mutaciones/terminal/updates bloqueados durante el contrato. Gateway certificado
hacia mock local: plataformas externas requieren sus credenciales y gates.
Auto-update certificado como simulación, sin promoción live. No se declara SYSTEM
PASS ni E2E prolongado: corresponden a fases futuras. Picos RAM/VRAM de la sesión
completa no registrados; no se inventan métricas.

## Git y archivos

Rama: phase/7a2-mcp-plugins. NO PUSH. Commits de esta continuación:
- f133bab fix: reconcile phase state and enforce chatgpt domain lock
- 5af0156 feat: add governed native document extraction
- c2088c9 feat: add governed native browser with guaranteed cleanup
- 255a557 feat: add serialized hermes roles and governed native subagents
- 8b2b175 feat: add isolated git worktrees with reviewed integration gate
- 16c4181 feat: govern native cron and no-agent catalog jobs
- 43843bc feat: guard native dashboard administrative surface on loopback
- b8c7844 feat: add outbound gateway sandbox and native inbound authentication gate
- 597431b feat: add simulated canary update with verified automatic rollback
- 7218916 feat: make chatgpt bridge idempotent with unknown-delivery reconciliation

El cierre de regresión/documentación se guarda en un commit local adicional.
Git status limpio se verifica después del commit; su SHA y auditoría final quedan
en .autopilot/reports/FINAL-GIT-AUDIT.json del sandbox macro7a-regression.
La lista completa de archivos se guarda en evidence/regression-7a-final/modified-files.json.
Backups bajo backups/ por etapa; evidencias históricas y negativas preservadas.
