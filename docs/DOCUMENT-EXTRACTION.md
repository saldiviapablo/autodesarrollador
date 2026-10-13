# Extracción documental gobernada (7A.3)

La capacidad nativa de Hermes v0.21.6 se verificó realmente antes de implementar el adapter. Markdown, JSON y YAML usan `read_file_tool`; DOCX, XLSX, PDF con capa de texto y RTF usan `extract_document_bytes`, la misma API oficial que emplea `read_file` después de obtener los bytes. En Windows esto permite confinar el parser sin abrir un shell para leer el contenedor binario.

Uso desde el workspace:

```powershell
& './scripts/extract-document.ps1' -InputPath 'spec.docx' -ProjectPath './sandbox/phase7a3-documents'
```

El proyecto debe tener un RUN-CONTRACT válido y autorizado cuyo `project_root` coincida exactamente. Este adapter sólo admite proyectos dentro del workspace de infraestructura; la admisión de proyectos externos corresponderá al Runner de 7B. Las rutas relativas se resuelven respecto al proyecto y las junctions/escapes fuera de él se rechazan.

El resultado JSON conserva `run_id`, documento relativo, SHA-256, origen y texto estructurado dentro de `UNTRUSTED_DOCUMENT_DATA`. El contenido es dato consultivo: cualquier orden contenida en el documento sigue subordinada al hook y a security.yaml.

Configuración central: sección `document_extraction` de system.yaml. Se verifican los hashes de los dos módulos nativos y del hook aprobado. Los paquetes usados ya estaban instalados en el runtime Hermes; sus versiones se inventarían en VERSIONS.lock, sin instalación ni actualización.

El adapter rechaza macros/piezas ejecutables camufladas en DOCX/XLSX, XML con DTD/entidades, archivos/ZIPs excesivos, formatos no aprobados, errores y extracción incompleta. No ejecuta macros ni fórmulas. La red está bloqueada en el proceso y el parser no puede crear procesos; las lecturas de texto plano pueden usar el backend nativo de archivos, separado de la fase de conversión documental.

El padre impone un timeout máximo de 30 segundos y elimina únicamente su árbol de procesos. El temporal se crea bajo `.autopilot/temp`, se elimina al salir y no se usa el directorio temporal global. La salida se transmite en UTF-8.

No se certifican OCR, PDFs escaneados, documentos cifrados ni Office legacy/PPTX. Estos casos no se convierten en PASS silenciosamente ni disparan instalaciones o servicios externos. No hay dependencias opcionales ni fallback instalado.

Verificación: `tests/test-phase-7a3.py`; inventario: `scripts/inspect-native-documents.py` en el Python nativo ya instalado; regresión acotada: `scripts/verify-capability-smoke.ps1`. Evidencia: `evidence/phase-7a3/`.
