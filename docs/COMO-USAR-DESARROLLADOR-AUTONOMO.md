# Cómo usar Desarrollador Autónomo

El mismo iniciador sirve para todos tus proyectos. No lo copies dentro de ellos.

1. **Buscá el iniciador** en `C:\Users\Pc\Documents\Proyectos Tech\Desarrollador autonomo\INICIAR-DESARROLLADOR-AUTONOMO.bat`.
2. **Abrilo con doble clic.** Se abre una ventana y el selector de carpetas de Windows.
3. **Elegí la carpeta de tu proyecto** y pulsá **Seleccionar carpeta**. Puede estar en otra carpeta o unidad local. Cancelar sale sin preparar un proyecto.
4. **Para un proyecto nuevo**, elegí una carpeta vacía o un repositorio Git propio. El sistema prepara su memoria y contrato dentro de esa carpeta. No elijas la carpeta de infraestructura.
5. **Pegá el objetivo** en el cuadro grande. Podés usar varios párrafos, tildes y otros caracteres. Explicá qué resultado necesitás y qué condiciones tiene que cumplir. No incluyas contraseñas ni claves.
6. **También podés abrir un brief** con **Abrir .md o .txt**. El archivo debe estar guardado como UTF-8. Podés revisar y editar el texto antes de continuar.
7. **Pulsá Continuar.** Hermes prepara un plan en modo de solo lectura. Todavía no trabaja el Worker. Aparecen el objetivo, las pruebas, los archivos permitidos, los límites y las políticas. Revisalos y elegí **Sí, iniciar este proyecto** o **No, cancelar**. Sólo después de aprobar se ejecuta Prepare: genera el contrato y verifica que coincide con lo revisado antes de iniciar el Runner. Hay una sola aprobación para ese plan concreto.
8. **Mirá el progreso** en la ventana: proyecto, ejecución, estado, tarea, último evento, tiempo, reinicios y salud del modelo. La planificación y la carga del modelo pueden tardar unos minutos.
9. **Para detener**, abrí `DETENER-DESARROLLADOR-AUTONOMO.bat` desde la misma carpeta de infraestructura. No hace falta escribir una ruta para una ejecución iniciada desde esta interfaz. Esperá el resultado final: el Runner guarda estado, checkpoint y reporte, cierra sus procesos y libera sus locks. Cerrar la ventana de progreso también solicita una parada segura.
10. **Para volver al mismo proyecto**, abrí el iniciador y elegí esa carpeta. Verás el último estado, tarea, checkpoint y pendientes. **Continuar proyecto** conserva el tiempo y los contadores del run; no renueva una ejecución vencida. **Nuevo objetivo** conserva la preparación anterior en `.autopilot-history/<run_id>/` y crea otra ejecución cuando el estado anterior permite hacerlo.
11. **Para cambiar de proyecto**, cerrá la ejecución actual y volvé a abrir el mismo iniciador. Elegí la otra carpeta. Cada proyecto tiene su propio Git, memoria, estado y reportes. La inferencia local sigue siendo de una sola ejecución por vez.
12. **Buscá los resultados** en `.autopilot/reports/` dentro del proyecto. La ventana final muestra esa ubicación y permanece abierta hasta que la cierres. El historial archivado conserva los reportes anteriores.

También podés iniciar con una ruta entre comillas:

```bat
INICIAR-DESARROLLADOR-AUTONOMO.bat "D:\Proyectos\Mi proyecto"
```

Esto evita el selector y abre directamente el proyecto indicado. Un estado **COMPLETED** significa que pasó el Completion Gate; una parada solicitada termina como **ABORTED**. Los errores y bloqueos quedan visibles en la ventana y no significan que el objetivo esté completado.

La interfaz usa PowerShell y la biblioteca gráfica que ya trae Python. No requiere una cuenta cloud, una instalación gráfica adicional ni cambios de Windows. No hace push ni despliegues.
