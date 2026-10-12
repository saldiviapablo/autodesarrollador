# Evidencia: Endpoint Local y Contexto 64K de Hermes Agent

- **Perfil:** `desarrollador-autonomo`
- **Modelo configurado:** `qwen36`
- **Proveedor:** `custom` (OpenAI-compatible local)
- **Endpoint:** `http://127.0.0.1:8080/v1`
- **Ventana de contexto:** `65536` tokens
- **Inference Lock:** `--parallel 1` respetado
- **Salida de configuración verificada:** `qwen36 custom http://127.0.0.1:8080/v1 65536`
- **Diagnóstico prompt-size:**
  - System prompt total: 37,432 B (~9.3K tokens)
  - Tool schemas total (25 herramientas nativas): 44,289 B (~11K tokens)
  - Total prompt base en reposo: ~81.7 KB (~20.5K tokens)
  - Margen libre dentro de ventana de 64K (65,536 tokens): ~45,000 tokens para conversación, lectura de código y razonamiento.
- **Resultado:** **PASS**
