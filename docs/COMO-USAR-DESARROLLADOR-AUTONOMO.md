# Cómo usar Desarrollador Autónomo

El mismo iniciador sirve para todos tus proyectos. No lo copies dentro de ellos.

## PARA USARLO HACÉ ESTO

1. **Abrí con doble clic** `C:\Users\Pc\Documents\Proyectos Tech\Desarrollador autonomo\INICIAR-DESARROLLADOR-AUTONOMO.bat`.
2. **Elegí la carpeta del proyecto** y pulsá **Seleccionar carpeta**. Para empezar algo nuevo, usá una carpeta vacía o un repositorio propio. Cancelar sale sin preparar nada.
3. **Escribí qué querés conseguir** y pulsá **Continuar**. Podés escribir varios párrafos o usar **Abrir .md o .txt** para cargar un archivo UTF-8. Indicá también qué condiciones debe cumplir el resultado; no incluyas contraseñas ni claves.
4. **Revisá el plan que prepara Hermes** y, si estás de acuerdo, pulsá **Sí, iniciar este proyecto**. Hay una sola aprobación. El proyecto empieza a prepararse y el Worker queda autorizado sólo después de ese paso.
5. **Seguí el avance en la ventana y esperá el resultado.** La ventana final muestra dónde están los reportes y queda abierta hasta que pulses **Cerrar**. La planificación y la carga del modelo pueden tardar unos minutos.

**Para detener:** abrí `DETENER-DESARROLLADOR-AUTONOMO.bat` desde la misma carpeta del iniciador y esperá el resultado final. También podés cerrar la ventana de progreso para solicitar una parada segura. Se guardan el estado, el checkpoint y el reporte; se cierran los procesos propios y se liberan los locks.

**Para continuar un proyecto:** abrí el mismo iniciador, seleccioná su carpeta y elegí **Continuar proyecto**. Conserva el reloj y los contadores; no renueva una ejecución vencida. **Nuevo objetivo** archiva la preparación anterior en `.autopilot-history/<run_id>/` y pide revisar otro plan cuando el estado anterior lo permite.

**Para cambiar de proyecto:** terminá o detené la ejecución actual, cerrá la ventana y volvé a abrir el mismo iniciador. Elegí la otra carpeta. Cada proyecto conserva su propio Git, memoria, estado, historial y reportes; la inferencia local sigue serializada.

Los reportes quedan en `.autopilot/reports/` dentro de la carpeta elegida. Hermes prepara el plan en modo de solo lectura. Después de aprobar, Prepare genera el contrato y comprueba que coincide con el alcance revisado antes de iniciar el Runner.

También podés iniciar con una ruta entre comillas:

```bat
INICIAR-DESARROLLADOR-AUTONOMO.bat "D:\Proyectos\Mi proyecto"
```

Esto evita el selector y abre directamente el proyecto indicado. Un estado **COMPLETED** significa que pasó el Completion Gate; una parada solicitada termina como **ABORTED**. Los errores y bloqueos quedan visibles en la ventana y no significan que el objetivo esté completado.

La interfaz usa PowerShell y la biblioteca gráfica que ya trae Python. No requiere una cuenta cloud, una instalación gráfica adicional ni cambios de Windows. No hace push ni despliegues.

Los objetivos largos se conservan completos como fuente privada en `runtime/project-launcher/planner-sources/` de la infraestructura. Hermes genera un plan compacto, sin volver a escribir todo el brief. Después de aprobar también queda una copia exacta en `.autopilot/evidence/ONBOARDING-OBJECTIVE.md` del proyecto. El plan muestra el resumen, pruebas y políticas antes de autorizar al Worker.

Si tenías abierta una ventana con el bloqueo anterior, cerrala y abrí nuevamente el iniciador para cargar la versión corregida. Podés volver a elegir la carpeta y cargar el mismo brief; no se inicia el Worker sin revisar y aprobar el nuevo plan. Cuando el plan pide investigación debe identificar una URL pública HTTPS concreta; si hay varias fuentes posibles y no puede resolverlas, se bloquea para que el plan pueda corregirse antes de aprobar.
