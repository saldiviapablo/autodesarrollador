# QWEN.md — Especificación de Conocimiento del Proyecto
<!-- 
  IMPORTANTE: Este archivo define el conocimiento técnico ESTABLE y permanente del proyecto.
  NO incluir aquí estado dinámico de ejecución (ciclo actual, errores temporales, tarea viva, próxima acción).
  El estado operativo en vivo reside exclusivamente en .autopilot/STATE.json y .autopilot/STATE.md.
-->

## 1. PROJECT
- **Nombre:** task-021-catalog
- **Propósito:** Validate a portable file catalog and report duplicates without filesystem access
- **Entorno de ejecución:** Windows 11 / Local

## 2. ARCHITECTURE
- **Patrón arquitectónico:** Modular Scripting / Clean Architecture
- **Separación de responsabilidades:**
  - Código fuente del proyecto gestionado vs Infraestructura externa.
  - El proyecto opera de forma autónoma guiado por contratos en `.autopilot/`.

## 3. STACK
- **Lenguajes:** Python, PowerShell
- **Frameworks / Runtimes:** Standard Library
- **Gestores de dependencias:** pip

## 4. CONVENTIONS
- Codificación en UTF-8 sin BOM.
- Rutas con compatibilidad para espacios y separadores de Windows.
- Nomenclatura descriptiva, funciones modulares y tipado explícito donde aplique.
- Comentarios concisos enfocados en el "por qué", no en el "qué".

## 5. COMMANDS
- **Instalación de dependencias:** `pip install -r requirements.txt`
- **Build / Compilación:** `echo 'No build required'`
- **Ejecución local / Smoke test:** `python main.py`

## 6. TESTING
- **Framework de pruebas:** `unittest / pytest`
- **Comando de pruebas unitarias:** ``
- **Criterio de éxito:** Todo commit debe resultar en ExitCode 0 en la suite de pruebas.

## 7. SECURITY
- No incluir secretos, tokens, contraseñas ni API keys en el código fuente ni en git.
- Mantener todas las escrituras y modificaciones estrictamente dentro de la raíz del proyecto.
- No ejecutar comandos destructivos fuera del workspace autorizado.

## 8. DO NOT
- NO modificar archivos fuera del directorio raíz del proyecto.
- NO realizar `git push` o interactuar con repositorios remotos sin autorización expresa.
- NO alterar la infraestructura del supervisor ni guardrails del sistema.
- NO borrar masivamente archivos ni directorios base.

## 9. VALIDATION
- La realidad del código y los tests prevalecen siempre sobre cualquier suposición del modelo.
- Antes de considerar una tarea completada, verificar que la suite de pruebas pase limpiamente.
