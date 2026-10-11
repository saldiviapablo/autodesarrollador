# Evidencia de Validacion de llama.cpp + Qwen (Fase 3)

- **Fecha:** 2026-10-11T18:51:50-03:00
- **Resultado de la Fase 3:** **PASS**
- **Binario validado:** C:\AI\llama.cpp\llama-server.exe
- **Version de llama.cpp:** 0.5.0-dev (build 11368, commit 1fb7ef3e3, Clang 20.1.8)
- **Modelo:** C:\Users\Pc\.cache\huggingface\hub\models--ggml-org--Qwen3.6-35B-A3B-GGUF\snapshots\baec3ebee244827cda0f4557eafa8b28f7545fa6\Qwen3.6-35B-A3B-Q4_K_M.gguf
- **Blob real:** C:\Users\Pc\.cache\huggingface\hub\models--ggml-org--Qwen3.6-35B-A3B-GGUF\blobs\671e47e0ec53c665d048b98c3ecbfd5236b5ca9c3e02ed19fc8f81f7b85140c7 (19.02 GB)
- **Alias:** qwen36
- **Contexto configurado:** 65536 tokens
- **Contexto verificado en log:** CONFIRMADO (65536)
- **Parallel verificado en log:** CONFIRMADO (1)
- **Endpoint /health:** HTTP 200 (Ready)
- **Endpoint /v1/models:** Alias 'qwen36' presente
- **Endpoint /v1/chat/completions:** PASS (Respuesta en 4.88s: 'QWEN_LOCAL_OK')
- **Cleanup:** PASS (PID cerrado y puerto 8080 liberado)

## Metricas de Recursos
| Estado | RAM Usada (GB) | RAM Libre (GB) | VRAM Usada (MiB) | Llama Working Set (MB) |
|:---|:---:|:---:|:---:|:---:|
| Antes de iniciar | 9.81 | 21.86 | 852 | 0 |
| Modelo cargado | 14.05 | 17.62 | 4051 | 4288.41 |
| Tras inferencia | 23.02 | 8.65 | 4067 | 4288.41 |
| Tras cleanup | 9.82 | 21.85 | 852 | 0 |

## Stress Test Previo 60K
Se deja constancia documental de que las pruebas progresivas de contexto (8K, 16K, 32K, 48K y 60K tokens) fueron ejecutadas y validadas previamente con este mismo hardware, binario y modelo, alcanzando 22.39 GB de RAM usada (9.28 GB libres) y working set de llama de 13.69 GB, confirmando la estabilidad operacional a 64K sin necesidad de re-estresar innecesariamente el hardware.
