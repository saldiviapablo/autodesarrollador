# Corrección y verificación del preflight 7A

PHASE: PREFLIGHT_7A_CONTINUATION (antes de 7A.3)

STATUS: verificaciones funcionales, seguridad, metadata y cleanup PASS. La habilitación de continuidad exige también el commit correctivo local y Git limpio; esa comprobación se registra después del commit en el estado operativo.

## Cambios

- README y ROADMAP ahora indican 7A=IN_PROGRESS; 7A.1 y 7A.2=PASS; 7A.3–7A.10=PENDING. Macrofases 1–6 conservan PASS; 7B y 8 conservan PENDING.
- INSTALLATION-STATE incorpora el desglose canónico de macrofases/subfases. MANIFEST y la matriz de capacidades 08 ya eran coherentes; se verificaron sin alterar sus capacidades aprobadas.
- Domain-lock con parsing real: HTTPS y hostname exacto `chatgpt.com`. Se eliminaron `openai.com`, subdominios y la excepción de `about:blank` como URL autorizada. El wrapper y el iniciador comparten el parser de PowerShell.
- Cada operación sobre el DOM comprueba el origen en la misma llamada CDP, antes y después de la acción. El documento transitorio de arranque sólo puede ser observado por URL/readiness y nunca recibe acciones DOM.
- El resumen de Fase 5 es evidencia histórica fechada. Se añadió únicamente `HISTORICAL SNAPSHOT — current versions are defined by VERSIONS.lock` con una aclaración; el contenido original se preservó. No se certificaron retroactivamente las versiones contradictorias del snapshot.
- VERSIONS.lock, security.yaml, hook aprobado, Inference Lock, MCP, plugin y evidencias de 7A.1/7A.2 conservan su contenido y hashes aprobados.

## Pruebas

| Comprobación | Estado | Evidencia |
|---|---|---|
| Matriz Node: 13 casos; parser, guard DOM y CLI real para DENY | PASS | domain-node.json |
| Matriz PowerShell: 13 casos; parser, wrapper e iniciador | PASS | domain-powershell.json |
| Hook SHA-256 y auto-accept desactivado | PASS | hook-sha256.json |
| Sanitización del hook: dos secretos sintéticos redactados | PASS | secret-sanitization.json |
| MCP health real | PASS | mcp-health.json |
| MCP allowlist: da_echo ALLOW / da_forbidden_test DENY | PASS | mcp-allowlist.json |
| Plugin SHA-256: entrypoint y manifest instalados | PASS | plugin-sha256.json |
| Bridge: sesión real sobre HTTPS chatgpt.com exacto | PASS | chatgpt-real-session.json |
| Roundtrip UTF-8 real en composer, sin envío | PASS | chatgpt-utf8-roundtrip.json |
| Consulta REAL: envío y recepción del marcador único y Unicode | PASS | chatgpt-real-consultation.json |
| Cleanup: cero Chrome de prueba y MCP restantes | PASS | smoke-summary.json |
| Coherencia documental y estado de seis fuentes | PASS | metadata-versions.json |
| Versiones instaladas coincidentes con lock sin modificar | PASS | metadata-versions.json |
| Contenido original de Fase 5 conservado | PASS | metadata-versions.json |
| Evidencias históricas 7A.1 y 7A.2 sin cambios | PASS | metadata-versions.json |
| Componentes protegidos sin cambios, hashes aprobados válidos | PASS | metadata-versions.json |
| Inspección previa revisada para secretos | PASS | metadata-versions.json |
| Configuración Qwen conservada y dominio exacto | PASS | metadata-versions.json |

Los casos DENY incluyen HTTP, openai.com, www.openai.com, foo.chatgpt.com, chatgpt.com.evil.test, chatgpt.com@evil.test, URL inválida, about:blank y hostname con punto final. Las credenciales de la matriz son fixtures sintéticos. No se leyeron ni guardaron credenciales reales.

No se repitieron las suites completas de 7A.1 ni 7A.2. Ambas subfases continúan PASS. No se ejecutó idempotencia. Inferencias locales durante el preflight: 0.

## Auditoría de versiones

La comprobación real registró Python 3.14.4, Node 24.14.1, Qwen Code 0.25.1, llama.cpp 0.5.0-dev build 11368 / commit 1fb7ef3e3 y Hermes v0.21.6 / commit 818c13be1dc4fd28987e1e881a9408224afd4535. VERSIONS.lock sigue siendo la referencia vigente y permanece intacto.

## Incidencias y autocorrecciones

1. Windows PowerShell 5.1 interpretó inicialmente como ANSI el nuevo script con Unicode. Se guardó como UTF-8 con BOM; la ejecución posterior pasó.
2. Primera ejecución REAL: el guard bloqueó una evaluación durante la transición de carga del documento inicial. `attempt-1-smoke-summary.json` conserva ese FAIL y cleanup PASS. `session-after-load.json` confirma que la pestaña quedó en chatgpt.com exacto con sesión lista. Se añadió espera de readiness limitada a 15 segundos sin autorizar acciones fuera de dominio. El segundo smoke completo pasó.
3. La prueba de inmutabilidad comparó inicialmente el blob LF de Git contra checkout CRLF. Se corrigió la comparación de contenido textual y se mantuvo además SHA-256 binario contra los hashes aprobados de los componentes protegidos; ambos controles pasan.

## Backup, Git y continuidad

Backup previo: `backups/preflight-7a-20261013-012453/manifest.json`, con original, copia, hash y motivo. Sólo se modificaron archivos dentro del workspace. El perfil existente de ChatGPT se reutilizó sin manejar credenciales ni ampliar dominios.

La inspección previa `evidence/inspection-7a-20261013-011310/` se conserva como evidencia de los hallazgos iniciales. Sus conclusiones corresponden al estado anterior a esta corrección.

Rama: phase/7a2-mcp-plugins. Commit correctivo previsto: `fix: reconcile phase state and enforce chatgpt domain lock`. NO PUSH. Dependencias nuevas: ninguna.

NEXT PHASE: 7A.3 sólo después de verificar commit local y Git limpio. Macrofase 7A todavía IN_PROGRESS; READY FOR 7B=NO.
