# Evidencia: Ejecución con Timeout y Terminación de Árbol de Procesos

- **Comando Normal:** Finalizó en 0.24s con código 0.
- **Comando Colgado (Start-Sleep 60s):**
  - **Timeout Configurado:** 3 segundos
  - **Duración Observada:** 3.01s
  - **PID Registrado:** 28752
  - **Acción Ejecutada:** 	askkill /PID 28752 /T /F (Terminación forzada de árbol de procesos)
  - **Comprobación de Huérfanos:** Proceso 28752 ya no existe en el sistema operativo.
- **Resultado:** PASS
