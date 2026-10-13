# Cleanup del Runner

El Job Object kernel contiene modelo y descendientes propios. La clausura del
handle también actúa si el padre muere abruptamente. El watchdog es el único
auxiliar autorizado a sobrevivir al padre: verifica identidad PID/start time,
espera hasta cinco segundos por el cierre kernel, guarda fallo/checkpoint/reporte
y termina. No sobrescribe un run nuevo que haya adquirido el mutex.

El finally procesa cada paso por separado. Un error de STATE, checkpoint o
reporte no salta la liberación del mutex. Los errores de finalización convierten
el resultado en FAILED. Si el directorio del reporte está obstruido, escribe los
formatos humano y JSON en runtime/emergency-reports/ dentro de infraestructura.

Sólo retira LOCK.json del run/PID propios. No mata procesos por nombre ni
detiene modelos EXTERNAL. Verifica el mutex físico de inferencia al cerrar y
conserva un holder externo. Las flags de un padre muerto se archivan al solicitar
Recover; no se borra una flag perteneciente a un padre activo.

El reloj del contrato vive en runtime/run-clocks/, fuera del proyecto gestionado:
reanudar no reinicia el presupuesto global. Un cambio del Runner/configuración
invalida el digest aprobado y requiere un contrato revisado antes de START.

STOP ofrece la parada controlada. Ctrl+C que termine abruptamente el padre usa
el mismo cierre kernel y guardian que la prueba de crash; la prueba específica
de interacción con un teclado queda fuera del runtime NonInteractive.

Evidencia: evidence/phase-22/. Pruebas de timeout, bloqueo, STALLED, STOP,
crash/stale, recuperación desde disco, obstrucción de escrituras y adopción real.
