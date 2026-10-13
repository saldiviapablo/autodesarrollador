# 7A.6 — Git Worktrees: PASS

El adapter `scripts/governed-worktree.py` usa Git CLI nativo con deadlines de 30s.
Solo se certifica en proyectos sandbox con RUN-CONTRACT autorizado y git_commit_local.
No reemplaza el Completion Gate global pendiente de 7B: su gate local exige tests,
Reviewer ACCEPTED, commit y SHA-256 del diff exactos, padre sin cambios y fast-forward.
El registro de ownership vive en .autopilot/worktrees.json. Se rechazan traversal,
junctions, cleanup no registrado y cambios a contratos/security/runner/versiones.
El retiro --force conserva un ZIP de los archivos dirty antes de ejecutarse; no
elimina ramas que aún contienen commits. Ninguna integración al repo de infraestructura
está habilitada por este adapter. Un Supervisor confiable produce el gate local.

Pruebas reales: WT-001 compilación independiente en .autopilot-worktrees/task-001;
WT-002 merge sin gate DENY, Reviewer qwen36 serializado acepta y merge --ff-only;
WT-003 archivo untracked respaldado y worktree eliminado, registro/lista limpios.
Casos de seguridad externos/traversal/unowned: DENY. Smoke previo PASS. Sin deps nuevas.
Evidencia: evidence/phase-7a6/. Próxima subfase: 7A.7 tras commit local y Git limpio.
