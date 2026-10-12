# Especificación del Proveedor Local — Qwen Code CLI
## Proyecto: Desarrollador Autónomo — Fase 5

**Proveedor de inferencia:** `llama-server.exe` (local)  
**Host:** `127.0.0.1`  
**Puerto:** `8080`  
**Base URL:** `http://127.0.0.1:8080/v1`  
**Modelo registrado:** `qwen36` (Qwen3.6-35B-A3B-Q4_K_M.gguf)  
**Protocolo:** `openai` (`/v1/chat/completions`)  
**Context Window:** `65536` tokens  

---

# 1. Configuración de Acceso y Credenciales

- **Tipo de autenticación CLI:** `--auth-type openai`
- **Variable de URL:** `OPENAI_BASE_URL=http://127.0.0.1:8080/v1`
- **Credencial sentinel:** `OPENAI_API_KEY=local-not-required`
  - *Aclaración de seguridad:* `local-not-required` es una cadena centinela obligatoria para satisfacer los requisitos del SDK de OpenAI cliente. No representa ninguna credencial real, token de autenticación ni secreto de producción.
- **Modelo:** `OPENAI_MODEL=qwen36` (o `-m qwen36`).

---

# 2. Exclusión de Endpoints Externos y Servicios Cloud

- **Sin APIs de pago:** Se prohíbe el uso de DashScope, OpenAI remoto o OpenRouter.
- **Sin Qwen OAuth:** No se inicia sesión web ni autenticación por navegador en Alibaba Cloud.
- **Sin Responses API:** Se utiliza el endpoint estándar validado `/v1/chat/completions`.
- **Aislamiento de configuración:** No se persiste configuración en perfiles globales del sistema; se inyectan variables de entorno exclusivamente al proceso del worker mediante el wrapper `scripts/invoke-qwen-code.ps1`.
