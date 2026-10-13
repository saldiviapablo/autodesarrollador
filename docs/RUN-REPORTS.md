# Reportes por run

El Runner escribe `.autopilot/reports/runner-result.json` y `FINAL.md`. Para
FAILED, STALLED, BLOCKED_REQUIRES_HUMAN y ABORTED añade el documento terminal
correspondiente. Ambos formatos usan el sanitizador recursivo existente.

Los datos proceden de STATE, eventos del run, resultados de tests y gate, Git y
contadores de reinicios. Las consultas no se inventan: web se cuenta mediante
eventos registrados y ChatGPT mediante su cuota en STATE. El reporte distingue
un gate no evaluado de uno rechazado. No declara completada una simulación.

Sin aprobación en modo unattended, el launcher guarda estado, checkpoint y
BLOCKED.md, sin arrancar inferencia ni esperar entrada. Un segundo launcher
no puede sobrescribir el estado de un run activo.

Evidencia de campos, cinco terminales y sanitización: evidence/phase-21/.
