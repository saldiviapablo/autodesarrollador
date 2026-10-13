# Path Guard canónico — intento 3 de F23

Causa: el guard antiguo inspeccionaba sólo el primer objeto existente. Si era
un archivo normal, no recorría sus padres junction y autorizaba después con
StartsWith(workspace). También aceptaba nombres hermanos con el mismo prefijo.

La resolución read-only central está en scripts/canonical_path.py. Recorre cada
componente, inspecciona lstat/reparse, sigue el destino real de junction/symlink,
resuelve también los padres de los destinos de enlaces y compara componentes
de la ruta física con la raíz canónica. Para un destino inexistente resuelve el
ancestro existente antes de añadir el sufijo donde se crearía. Los errores,
tags no resolubles, enlaces colgantes, ciclos y más de 32 saltos son DENY.
Rutas de dispositivo, UNC, drive-relative y ADS se rechazan por ambigüedad.

Test-WorkspacePathGuard conserva su interfaz y usa esa implementación, con
timeout de 20 segundos y DENY ante fallo del helper. READ y WRITE usan el mismo
criterio. Runner/Prepare importan ese resolver y mantienen sus reglas más
estrictas: traversal y cualquier reparse point DENY. Los adapters MCP y plugin
añaden la admisión central; sus implementaciones nativas e integridades aprobadas
permanecen intactas y sus restricciones adicionales siguen activas. El digest
de aprobación Runner incluye el resolver y los adapters/guard corregidos.

No se cambiaron security.yaml, RUN-CONTRACT schema, Inference Lock, Command Guard,
Secret Guard, hook ni hashes aprobados de MCP/plugin. Cero dependencias nuevas.

## Evidencia del fix

El caso original pasa de ALLOW histórico a DENY / PATH_BOUNDARY_VIOLATION, con
destino físico externo identificado, writes=0 y sentinel intacto. Historia en
evidence/phase-23-attempt-2/integral-security.json; nuevo resultado en
evidence/phase-23-attempt-3/integral-security.json.

A–J: PASS para READ y WRITE. A normal/I Unicode ALLOW; B archivo existente,
C futuro archivo y D directorio tras junction externa DENY; F junction anidada,
G traversal externo, H ruta externa y J variación de mayúsculas DENY. E permite
únicamente un destino físico interno conforme a 04-AUTONOMIA-Y-SEGURIDAD § de
resolución canónica y al comportamiento anterior de Path Guard. Prepare/Runner
y MCP conservan su DENY más estricto incluso para enlaces internos.

También PASS: prefijo hermano, destino normal inexistente, raíz DESTROY DENY,
ciclo real, dangling link, 33 enlaces, fallo de readlink inyectado y snapshots
sin cambios. MCP READ normal ALLOW/external DENY; plugin normal ALLOW/external
DENY e integridad SHA-256 PASS. Prepare boundary y A–H siguen PASS. F15 histórico:
5/5 PASS, comandos peligrosos 11/11 DENY, secretos y policy merge PASS.

La primera ejecución del harness A–J excedió el límite de longitud de comando
Windows al transportar todos los casos por EncodedCommand. Se corrigió el
harness usando un archivo JSON en su sandbox; no fue un fallo del guard. Sus
enlaces se retiraron en finally incluso en ese fallo.

TOCTOU residual: no se mantienen handles de objetos/rutas entre validar y operar.
La revalidación de Prepare y del adapter plugin reduce el intervalo; el servidor
MCP conserva su validación estricta justo antes del read. No se afirma aislamiento
de kernel frente a cambios concurrentes del namespace. El código que realice IO
debe revalidar inmediatamente antes cuando sea práctico.

Backup: backups/pathguard-fix-20261013-201419/manifest.json. Evidencia nueva:
evidence/phase-23-attempt-3/. historical-bindings.json liga byte por byte todos
los archivos de los intentos 1 y 2 y sus informes de parada.

El PASS de este fix no equivale a F23 integral PASS. F23 deberá ejecutar además
web, consulta real ChatGPT, agentes, tests/build, recovery y cleanup. F24 no
puede comenzar sin ese gate completo.
