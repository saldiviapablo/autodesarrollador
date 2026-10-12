# Evidencia: Consulta Consultiva a ChatGPT y EvaluaciÃ³n por Hermes Supervisor

- **Rol de ChatGPT:** CONSULTOR EXTERNO DE ALTO NIVEL (ADVISORY_UNTRUSTED)
- **Regla Violada si ejecutara comandos:** ChatGPT NUNCA programa directamente ni ejecuta comandos de shell.
- **Pregunta Planteada:** `Tenemos un dilema arquitectÃ³nico: en un sistema de procesamiento por lotes local, Â¿es mejor usar bloqueo por archivo (.lock) o Mutex del sistema operativo para evitar concurrencia?`

## Respuesta Consultiva de ChatGPT:
> 
Causa probable: Las colisiones de concurrencia en disco suelen derivar de carreras entre procesos al escribir archivos compartidos.
> Estrategias alternativas:
> 1. Usar System.Threading.Mutex con nombre (Named Mutex): Garantiza exclusiÃ³n mutua atÃ³mica a nivel de kernel de Windows, sin depender del estado del sistema de archivos.
> 2. Usar FileShare.None en System.IO.FileStream: Bloquea el descriptor a nivel de kernel durante la operaciÃ³n, liberÃ¡ndolo automÃ¡ticamente si el proceso muere.
> Riesgos asociados:
> - Named Mutex puede quedar 'abandoned' si el proceso cae abruptamente sin liberar, requiriendo captura de AbandonedMutexException.
> - Los locks basados en archivo temporal pueden quedar huÃ©rfanos tras cortes de energÃ­a.

## EvaluaciÃ³n y Veredicto de Hermes Supervisor:
> 
Hermes omitido en test unitario (SkipLlama activo).
