# Subfase 7A.3 — Document Extraction

PHASE: 7A.3. STATUS: pruebas funcionales, seguridad, fallo/timeout, cleanup y regression smoke PASS; commit local requerido antes de 7A.4.

CHANGES: adapter delgado de admisión por RUN-CONTRACT/scope sobre APIs nativas de Hermes. Configuración y versiones registradas; no se sustituyen Hermes, Qwen Code, Inference Lock ni guardrails. Nuevo documento operativo en docs/DOCUMENT-EXTRACTION.md.

TESTS:

- DOC-001: llamadas reales a `read_file_tool` para siete formatos (Markdown, JSON, YAML, DOCX, XLSX, PDF, RTF), todos PASS. firecrawl-anydoc 0.2.4 ya estaba instalado. No se instalaron pypdf, openpyxl ni dependencias opcionales.
- DOC-002: extracción gobernada de los siete formatos con texto estructurado, run_id y envelope UNTRUSTED PASS. Para formatos binarios se invoca el converter oficial `extract_document_bytes` que usa read_file; no se implementa un parser alternativo.
- DOC-003: macros camufladas, traversal, ruta externa, junction y contrato no autorizado: DENY. Documento con secretos: salida redactada. Orden maliciosa derivada del texto: hook existente bloquea antes de ejecución.
- DOC-004: corrupto y ausente devuelven ERROR; timeout real de 10 ms aborta el proceso nativo y verifica PID detenido en menos de 10 s. Son pruebas negativas PASS porque cumplen el resultado esperado.
- DOC-005: temporal de conversión vacío y junction de prueba eliminada sin recorrer el destino. Sin procesos de extracción o MCP huérfanos en la revisión final.
- Regression smoke anterior: hook SHA-256, sanitización, MCP health/allowlist, plugin SHA-256, domain-lock y cleanup PASS. El bridge no cambió respecto a f133bab, por lo que se conserva la evidencia de consulta REAL y UTF-8 PASS de ese commit sin repetir consultas innecesarias.

EVIDENCE: native-inventory.json, T-7A-DOC-002..005.json, phase-7a3-summary.json, regression-smoke.json. Estado/contrato/eventos de pruebas en sandbox/phase7a3-documents/.autopilot. Preflight de continuidad previo en commit f133bab.

DEPENDENCIES: cero nuevas. Se registran únicamente versiones de paquetes y Python que ya estaban en el entorno nativo Hermes.

AUTOCORRECTIONS: invocación inicial por `runpy` confundió archivo y módulo; se usó el Python del entorno ya instalado. El backend Windows de read_file usa procesos auxiliares; se eligió la API oficial de bytes para contenedores y se separó la lectura de texto de la fase de parser, manteniendo el bloqueo de procesos del parser. Se corrigió el encoding de stdout Unicode y el cleanup no interactivo de una junction, preservando los intentos fallidos en attempt-1-summary.json y attempt-2-cleanup-failure.json. La política global y los hashes aprobados existentes no cambiaron.

RISKS/LIMITS: sólo los siete formatos probados; PDF requiere capa de texto. No se certifica OCR, Office legacy ni PPTX. Ante extracción incompleta/error se falla de forma explícita. No se prueba aún un run autónomo completo ni se implementa el Runner de 7B.

NEXT PHASE: 7A.4, únicamente después del commit local y Git limpio. MACROFASE 7A sigue IN_PROGRESS; READY FOR 7B=NO.
