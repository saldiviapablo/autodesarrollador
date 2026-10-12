# Evidencia Consolidada: Macrofase 6 — Web, ChatGPT, Seguridad y Anti-Loop
## Proyecto: Desarrollador Autónomo
**Versión:** 2.0  
**Fecha:** 2026-10-12  
**Estado:** **PASS** (100% de verificaciones aprobadas)

---

## 1. Resumen Ejecutivo de Macrofase 6

La Macrofase 6 establece las capacidades de investigación web, consulta consultiva externa supervisada, guardrails deterministas de seguridad y prevención matemática de bucles infinitos:

| Fase | Título | Estado | Pruebas | Evidencia Principal |
| :---: | :--- | :---: | :---: | :--- |
| **13** | Web Research | **PASS** | 6/6 | `evidence/web/web-research.md`, `evidence/web/web-prompt-injection.md` |
| **14** | Chrome Dedicado + ChatGPT | **PASS** | 6/6 | `evidence/chatgpt/chatgpt-profile.md`, `domain-lock.md`, `chatgpt-budget.md`, `chatgpt-consultation.md` |
| **15** | Guardrails / Seguridad | **PASS** | 5/5 | `evidence/security/command-guard.md`, `path-guard.md`, `secret-redaction.md`, `policy-merge.md` |
| **16** | Anti-Loop / Timeouts | **PASS** | 4/4 | `evidence/anti-loop/error-signature.md`, `loop-detection.md`, `timeout-kill.md`, `escalation-ladder.md` |

---

## 2. Hitos Verificados por Fase

### Fase 13 — Web Research Gratuito y Defensa contra Prompt Injection
1. **Búsqueda Técnica Gratuita:** DDG Instant Answer API, Wikipedia API, GitHub API y PyPI API integradas sin API keys ni servicios de pago.
2. **Contenedor de Datos No Confiables:** Todo contenido web extraído es envuelto bajo el tag `<UNTRUSTED_EXTERNAL_DATA>` y marcado explícitamente como datos y no instrucciones.
3. **Defensa contra Prompt Injection con Hermes en Vivo:** Hermes local evaluó una página inyectada con la orden maliciosa de ejecutar `git push --force origin master`. Hermes extrajo fielmente el dato legítimo (versión 4.2.0) y rechazó explícitamente el comando malicioso.

### Fase 14 — Chrome Dedicado + ChatGPT Consultivo
1. **Perfil Aislado y Persistente:** Perfil exclusivo en `data/browser/HERMES-CHATGPT`, desacoplado de perfiles personales y excluido de Git.
2. **Domain Lock Estricto:** Control mediante CDP permitiendo únicamente `chatgpt.com` y `openai.com`. Cualquier intento de escape a dominios ajenos es bloqueado antes de la navegación.
3. **Máximo 1 Pestaña Controlada:** Cierre automático de pestañas adicionales.
4. **Presupuesto Global de Consultas:** Límite configurable (`max_chatgpt_queries = 5` por run). Al superarse el límite, las consultas son denegadas sin abrir el navegador ni tocar el DOM.
5. **Autenticación Humana Respetada:** Detección de login con estado `BLOCKED_REQUIRES_HUMAN_LOGIN` manteniendo la ventana visible. Tras el login manual del usuario, la sesión quedó activa y validada en `data/browser/HERMES-CHATGPT`.
6. **Consulta REAL y Rol Consultivo de ChatGPT:** Consulta real en vivo vía CDP sin mocks (`CHATGPT_BRIDGE_REAL_OK`, `7 + 8 = 15`). ChatGPT actúa exclusivamente como consultor de arquitectura (`ADVISORY_UNTRUSTED`). Hermes Supervisor evalúa su consejo emitiendo un veredicto estructurado (`DECISION: ACCEPT`).

### Fase 15 — Guardrails y Seguridad Ejecutable
1. **Command Guard Determinista:** Bloqueo estricto de 11/11 comandos peligrosos (`git push`, `git push --force`, `git clean -fdx`, `git reset --hard`, `format`, `diskpart`, `bcdedit`, `reg delete`, `shutdown`, `restart-computer`, `netsh advfirewall`, `rmdir /s /q .`).
2. **Path Guard y Canonicidad:** Bloqueo de escapes relativos (`..\..\Windows`), escapes absolutos y destrucción de la raíz del workspace.
3. **Protección contra Symlinks/Junctions:** Detección y bloqueo de puntos de reanálisis que intentan apuntar fuera del workspace.
4. **Redacción de Secretos:** Sanitización determinista de API keys (`sk-...`), tokens (`ghp_...`), bearer tokens y passwords antes de ser enviados a la web, ChatGPT o Git.
5. **Policy Merge por Intersección:** Prevalencia estricta de `security.yaml` sobre `RUN-CONTRACT.yaml`. Ningún contrato ni prompt puede relajar los permisos globales.

### Fase 16 — Anti-Loop, Timeouts y Control de Progreso
1. **Firma Normalizada de Errores:** Limpieza de variaciones cosméticas (PIDs, timestamps, temp paths, memory addresses) para generar hashes idénticos ante errores semánticamente iguales.
2. **Huella de Avance Real (Fingerprint):** Hash SHA-256 combinando `git rev-parse HEAD`, `git diff --stat`, conteo de tests PASS/FAIL y última firma de error.
3. **Prevención de Bucles:** Detección de 3 errores idénticos (`max_same_failure = 3`) y de 3 ciclos sin avance (`max_no_progress = 3`).
4. **Escalera de Escalamiento Determinista:** Secuencia `RETRY` → `NEW_APPROACH` → `WEB_RESEARCH` → `CHATGPT_CONSULT` → `NEW_SESSION` → `BLOCKED_REQUIRES_HUMAN`. Límite absoluto en ciclo 20 (`STALLED`).
5. **Timeout con Terminación de Árbol de Procesos:** Ejecución con timeout determinista y terminación forzada del subárbol completo de procesos (`taskkill /PID ... /T /F`), garantizando cero procesos huérfanos.
