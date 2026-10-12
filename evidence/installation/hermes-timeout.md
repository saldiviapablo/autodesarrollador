# Evidencia: Control de Timeout y Recuperación en Hermes Agent

---

## 1. Prueba 7: Timeout Forzado

- **Duración observada:** 2.13s
- **Flag TimedOut:** True
- **ExitCode:** -1
- **Comportamiento:** El wrapper `scripts/invoke-hermes.ps1` detectó el vencimiento del presupuesto de tiempo, finalizó inmediatamente el subproceso `hermes.exe` y todos sus procesos hijos asociados sin colgar el sistema operativo ni dejar procesos huérfanos.
- **Resultado:** **PASS**

---

## 2. Prueba 8: Recuperación Post-Timeout

- **Prompt:** `Responde exactamente la frase: HERMES_RECOVERY_OK`
- **ExitCode:** 0
- **Duración:** 61.99s
- **Resultado:** **PASS**
- **Salida:** `HERMES_RECOVERY_OK`
- **Observación:** Hermes y el endpoint local reanudaron operaciones con total normalidad tras la terminación forzada del turno previo, demostrando resiliencia y ausencia de locks residuales que impidan nuevas inferencias.
