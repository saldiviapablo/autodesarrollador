# Evidencia: EjecuciÃ³n con Timeout y TerminaciÃ³n de Ãrbol de Procesos

- **Comando Normal:** FinalizÃ³ en 0.23s con cÃ³digo 0.
- **Comando Colgado (Start-Sleep 60s):**
  - **Timeout Configurado:** 3 segundos
  - **DuraciÃ³n Observada:** 3.02s
  - **PID Registrado:** 29440
  - **AcciÃ³n Ejecutada:** 	askkill /PID 29440 /T /F (TerminaciÃ³n forzada de Ã¡rbol de procesos)
  - **ComprobaciÃ³n de HuÃ©rfanos:** Proceso 29440 ya no existe en el sistema operativo.
- **Resultado:** PASS
