# Corrección de Prepare — intento 2 de F23

El intento 1 escribió ocho archivos a través de un PROJECT_ROOT junction antes
del rechazo de contract.inspect. El informe de parada y su evidencia FAIL se
preservan íntegros; historical-bindings.json registra sus SHA-256.

Antes: initializer → archivos/copias → admisión → DENY tardío.
Ahora: mutex de run → PREPARE_PRE_ADMISSION read-only → revalidación de inputs,
identidades de padres y destinos → initializer existente → plan/contrato draft
atómicos → inspect final. Prepare nunca autoriza Start.

contract.py comparte project_path/check_path/validate_plan entre Prepare e
inspect final. Se rechazan traversal, rutas relativas de proyecto, raíces
protegidas, UNC, cualquier reparse point (incluidos enlaces colgantes), conflictos
QWEN/.autopilot y planes inválidos antes de efectos en el proyecto. Se enumeran
también los directorios, STATE.previous y todos los temporales reales del flujo.
La política sigue en security.yaml, sin modificaciones. El workspace es el
proyecto seleccionado explícitamente; -WorkspaceRoot permite al llamador imponer
un ámbito adicional más estrecho y usa comparación canónica de componentes.

La revalidación se repite dentro del proceso Apply inmediatamente antes del
initializer. El Job Object existente contiene sus descendientes y los termina
si el proceso finaliza o vence el timeout de 90 segundos. La exclusión mutua
cubre también Prepare; no se adquiere Inference Lock porque no hay inferencia.

Si Apply falla no se devuelve éxito. El cleanup valida nuevamente las rutas,
retira sólo los destinos nuevos conocidos y usa unlink/rmdir sin borrado
recursivo; preserva entradas desconocidas y reporta cleanup incompleto si
impiden retirar un directorio. Los archivos preexistentes del proyecto se
preservan. Cambios de identidad durante cleanup se preservan y se reportan.

Existe TOCTOU residual: el initializer usa rutas normales, sin handles que
fijen el namespace durante todas las escrituras. Un actor externo que no respete
el mutex puede cambiar rutas después de la última validación o crear un archivo
con un nombre reservado durante Apply. El mutex excluye los runs cooperantes;
no equivale a un sandbox de kernel ni demuestra inmunidad frente a ese actor.
No se amplió la arquitectura para eliminar esa limitación.

## Validación ejecutada

- Hallazgo original: DENY / REPARSE_POINT_DENIED, exit 2, cero cambios,
  QWEN.md y .autopilot ausentes, sentinel intacto.
- PREPARE_ZERO_WRITE_ON_DENY: PASS, contador cero y snapshot independiente.
- A normal y H espacios/Unicode: Prepare PASS, contrato no autorizado y STATE
  INITIALIZED. B junction raíz, C junction padre, D destino junction,
  E traversal, F fuera del ámbito declarado y G symlink real: DENY / cero
  cambios. G pudo ejecutarse en este Windows.
- Plan inválido y conflicto preexistente: DENY / cero cambios.
- Cambio de junction entre admisión y Apply: DENY / cero cambios.
- Fallo inyectado en initializer: FAIL seguro, temporales retirados, datos del
  usuario preservados. Es fault injection de unidad, no un fallo real de disco.
- State Manager atómico sin modificar, mutex real y retiro de metadata de
  inicialización propia: PASS. Launcher no tiene acción Prepare: no aplica.
- Smoke de seguridad F15 con rutas absolutas: 5/5 PASS; comandos 11/11 DENY.
  La primera invocación relativa del harness falló por doble combinación de
  SandboxDir; ambas invocaciones quedan documentadas.
- Smoke de ciclo de vida backend probe: tests PASS, checkpoint y cleanup PASS;
  Completion Gate rechaza correctamente COMPLETED por falta de backend real y
  diff. La expectativa inicial errónea del harness se conserva como FAIL y se
  explica en runtime-smoke-classification.json. No hubo inferencia local.

Evidence: evidence/phase-23-attempt-2/. Backup previo:
backups/prepare-boundary-fix-20261013-193613/. Ninguna dependencia nueva, actualización
de Hermes, cambio de modelo, cambio de security.yaml ni push.

Este PASS corresponde a la corrección y sus smokes. F23 integral todavía requiere
su intento nuevo; F24–F26 están NOT_RUN hasta que F23 integral sea PASS.
