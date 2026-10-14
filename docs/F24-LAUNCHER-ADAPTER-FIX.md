# Adaptador F24 — 2026-10-14

Fix PASS. Casos A–H PASS; la F24 real aún no se certifica por estos tests.

Se verificó la evidencia histórica del intento 1: la expresión `/c` entrecomillada se escapaba nuevamente mediante `list2cmdline`, con exit 1 antes del Runner. El nuevo adaptador de tests pasa una línea nativa Windows a CreateProcess con `shell=False`; valida el ejecutable batch y cada argumento antes de construirla. cmd.exe usa `/d /v:off /s /c`, con un único entrecomillado de cada literal y de la expresión exterior. No se pasa el texto de prompts por este mecanismo.

Se permiten argumentos literales, Unicode, espacios y vacío. Se rechazan antes de crear proceso comillas dobles, metacaracteres de cmd, expansiones `%`/`!`, controles CR/LF/NUL y paréntesis. Ninguna entrada peligrosa se convierte en ejecución adicional. Esta restricción es del adaptador de tests, no cambia políticas del Runner.

Tests reales con batch ficticio: A ruta sin espacios; B ruta con espacios; C PROJECT_ROOT con espacios; D Unicode; E vacío entre otros argumentos; F entradas peligrosas denegadas sin ejecución; G exit code 37 preservado; H stdout/stderr UTF-8 íntegros. Cada llamada permitida incrementa el contador exactamente una vez. Para A se crearon archivos nuevos en un directorio temporal único fuera del workspace porque su raíz contiene espacios; ningún archivo existente se modificó y cleanup PASS. Evidencia: `evidence/f24-launcher-adapter-fix-20261014/adapter-A-H.json`.

El harness F24 usa este adaptador validado. Guarda evidencia nueva en `evidence/phase-24-attempt-2-20261014/`; conserva el intento 1 íntegro. Monitoreo continuo de RAM/pagefile/VRAM; ownership por PID y nacimiento; detención ante 3 muestras consecutivas bajo 150 MiB; finalización mediante APIs existentes. La consulta F23 completada no se repite. La consulta de F24 tendrá un ID propio, sin reenvío ciego ante entrega ambigua.

Launchers F19, Runner, hooks, Inference Lock, security.yaml y componentes protegidos no se modifican. No hay dependencias nuevas ni cambios en Windows. qwen36 / 127.0.0.1:8080 / ctx 65536 / parallel 1 se mantienen. F24 real, F25, 4H y F26 requieren sus propios gates; F27/F28 no se inician. NO PUSH.
