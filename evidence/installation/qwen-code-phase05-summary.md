# Resumen de Validación — Fase 5: Qwen Code CLI
## Proyecto: Desarrollador Autónomo
**Fecha de ejecución:** 2026-10-11  
**Estado general:** PASS (100% pruebas superadas exitosamente)  
**Entorno de ejecución:** Windows 11 Pro 24H2 | Node.js v24.14.1 | npm 11.11.0 | Python 3.14.0

---

## 1. Identificación del Componente y Worker
- **Paquete oficial:** `@qwen-code/qwen-code`
- **Versión instalada:** `0.25.1`
- **Ejecutable global:** `C:\Users\Pc\AppData\Roaming\npm\qwen.cmd`
- **Punto de entrada CLI:** `C:\Users\Pc\AppData\Roaming\npm\node_modules\@qwen-code\qwen-code\cli-entry.js`
- **Permisos de instalación:** Usuario estándar (sin elevación UAC ni modificaciones globales de sistema)
- **Aislamiento de Telemetría:** Desactivada explícitamente (`QWEN_TELEMETRY=false`)

---

## 2. Configuración del Proveedor y Modelo Local
- **Motor de inferencia:** `llama-server.exe` (llama.cpp b4653)
- **Modelo servido:** `Qwen3.6-35B-A3B-Q4_K_M.gguf` (19.46 GB, alias `qwen36`)
- **Endpoint local:** `http://127.0.0.1:8080/v1`
- **Tipo de autenticación configurada:** `--auth-type openai`
- **Credencial sentinel:** `local-not-required`
- **Context Window:** 65,536 tokens (`--ctx-size 65536`)
- **Concurrencia:** `--parallel 1` (cumplimiento estricto de la regla de inferencia única)
- **Modelos externos o APIs pagas:** Totalmente excluidos (0 llamadas a Alibaba Cloud, OpenAI remoto, DashScope u OpenRouter)

---

## 3. Resultados Detallados de la Suite de Pruebas (scripts/verify-qwen-code.ps1)

| # | Prueba / Capacidad | Parámetros Clave | Resultado | Métricas / Evidencia |
|---|-------------------|------------------|-----------|----------------------|
| - | **Llama Server Readiness** | `http://127.0.0.1:8080/health` | **PASS** | Listo en 3.61s (PID 30420) |
| - | **Llama Model Check** | `/v1/models` | **PASS** | Modelo activo: `qwen36` |
| 1 | **Inferencia Local Qwen** | `--approval-mode plan`, `-o json` | **PASS** | ExitCode=0, Duración=99.41s |
| 2 | **Headless Mode y Budgets** | `--max-wall-time 300s`, suma 17+25 | **PASS** | ExitCode=0, Respuesta contiene 42 (`qwen-code-headless.json`) |
| 3 | **Inspección en Sandbox** | `--approval-mode plan`, `sandbox/qwen-code-basic` | **PASS** | ExitCode=0, Detectó bug de resta en `calculator.py` sin modificar archivos (`qwen-code-read-test.json`) |
| 4 | **Autocorrección (FAIL $\rightarrow$ FIX $\rightarrow$ PASS)** | `--approval-mode yolo`, ejecución tests, edición | **PASS** | Tests antes fallaron (ExitCode 1), código editado con operador `+`, tests después pasaron (ExitCode 0) (`qwen-code-autofix.json`) |
| 5 | **Output Estructurado JSON** | `-o json`, validación schema | **PASS** | JSON parseable y válido en wrapper |
| 6 | **Timeout Controlado** | `--max-wall-time 2s`, timeout wrapper 4s | **PASS** | ExitCode=55, Abortado limpiamente en 3.42s sin procesos huérfanos (`qwen-code-timeout.md`) |
| 7 | **Continuidad de Sesión (Resume)** | `--session-id <uuid>`, `-r <uuid>` | **PASS** | Conservó clave `CLAVE_DE_SESION_PHASE05_987` entre ejecuciones desacopladas (`qwen-code-resume.md`) |

---

## 4. Ciclo de Vida y Limpieza (Cleanup)
- Proceso `llama-server.exe` (PID 30420) terminado de forma determinista mediante bloque `finally`.
- Socket `127.0.0.1:8080` liberado inmediatamente comprobado con `Get-NetTCPConnection -State Listen`.
- Procesos auxiliares de Node y scripts intermedios completamente cerrados.
- Working tree del sandbox restaurado y libre de residuos.
