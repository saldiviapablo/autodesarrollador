# Configuración de Custom Provider Local para Hermes Agent

**Proveedor:** `custom` (`local-qwen`)  
**Backend:** `llama-server.exe` (OpenAI-compatible HTTP API)  
**Endpoint:** `http://127.0.0.1:8080/v1`  
**Modelo:** `qwen36` (Qwen3.6-35B-A3B Q4_K_M)  
**Ventana de contexto:** `65536` tokens  

---

## 1. Principio de Autonomía y Privacidad

En cumplimiento estricto con `AGENTS.md` (Reglas 2, 10, 11, 12) y `04-AUTONOMIA-Y-SEGURIDAD.md`:

- **Cero dependencias cloud:** Hermes opera sin requerir conexión a internet para inferencia. No se conecta a Nous Portal, OpenRouter, OpenAI remoto, Anthropic, DeepSeek, Alibaba Cloud ni otros servicios externos.
- **Sin costos por API:** Toda la inferencia se resuelve localmente en la GPU/CPU del host.
- **Compatibilidad estándar:** Utiliza la API compatible con OpenAI `/v1/chat/completions` provista por `llama-server`.
- **Inference Lock:** Se respeta la directiva de `--parallel 1` (una única inferencia local simultánea en todo el sistema).

---

## 2. Esquema de Configuración en Hermes Agent

En Hermes Agent v0.21.6, la conexión a un servidor OpenAI local se realiza definiendo tanto el bloque `model` por defecto como la entrada en `custom_providers`:

```yaml
model:
  default: qwen36
  provider: custom
  base_url: http://127.0.0.1:8080/v1
custom_providers:
  - name: local-qwen
    base_url: http://127.0.0.1:8080/v1
    api_key: local-not-required
    api_mode: chat_completions
    context_length: 65536
    models:
      qwen36:
        context_length: 65536
_config_version: 50
```

### Parámetros Clave:

1. **`provider: custom`**: Indica a Hermes que debe consultar la lista de proveedores personalizados y no asumir rutas predeterminadas de vendors cloud.
2. **`base_url: http://127.0.0.1:8080/v1`**: Especifica la URL base local del servidor `llama.cpp`.
3. **`api_mode: chat_completions`**: Establece el transporte canónico a `/v1/chat/completions` con soporte para streaming y llamadas a herramientas (function calling).
4. **`context_length: 65536`**: Configura la ventana de contexto idéntica al parámetro `--ctx-size 65536` de `llama-server`.
5. **`api_key: local-not-required`**: Provee un token sintético no vacío para satisfacer clientes HTTP que requieren cabecera `Authorization: Bearer <key>`.

---

## 3. Verificación de Cero Fuga Externa

1. **Auditoría de Configuración:** `hermes -p desarrollador-autonomo config show` confirma que no hay API keys configuradas para ningún proveedor externo.
2. **Restricción de Red:** Todas las solicitudes HTTP del runtime del agente se dirigen a `127.0.0.1:8080`.
3. **Validación de `hermes config check`:** La verificación estática confirma que la configuración es sintáctica y semánticamente válida sin advertencias ni errores.
