# Inventario Real de Soporte MCP en Hermes v0.21.6 (Subfase 7A.2)

- **Versión de Hermes**: `0.21.6` (`commit 818c13be1dc4fd28987e1e881a9408224afd4535`)
- **Perfil activo**: `desarrollador-autonomo`
- **Archivo de configuración del perfil**: `C:\Users\Pc\AppData\Local\hermes\profiles\desarrollador-autonomo\config.yaml`
- **SDK MCP instalado en runtime de Hermes**: `mcp 2.0.0` (`C:\Users\Pc\AppData\Local\hermes\tools\python-3.14.7+20260901-win32-x64\python.exe`, entorno gestionado en `C:\Users\Pc\AppData\Local\hermes\runtime`)
- **Intérprete del servidor MCP local de sandbox**: `C:\Python314\python.exe` (`scripts/mcp-sandbox-server.py`)

## 1. Comandos CLI Disponibles

Verificados mediante `hermes -p desarrollador-autonomo mcp --help`:

- `hermes -p desarrollador-autonomo mcp list`: Lista los servidores MCP configurados en el perfil y su estado.
- `hermes -p desarrollador-autonomo mcp test <server>`: Prueba la conexión al servidor MCP, realiza el handshake `initialize` y descubre las herramientas filtradas.
- `hermes -p desarrollador-autonomo mcp add`: Agrega un servidor MCP a `config.yaml`.
- `hermes -p desarrollador-autonomo mcp remove`: Elimina un servidor MCP de `config.yaml`.
- `hermes -p desarrollador-autonomo mcp configure`: Configura selectivamente las herramientas habilitadas (`tools.include` / `tools.exclude`).

## 2. Transportes Soportados (`tools/mcp_tool.py`)

1. **stdio (`StdioServerParameters`)**: Subproceso local definido mediante `command`, `args` y `env`. Hermes filtra automáticamente variables de entorno sensibles para que el subproceso sólo reciba un entorno seguro más lo declarado en `env`.
2. **Streamable HTTP (`streamable_http_client`)**: Servidor HTTP/HTTPS definido mediante `url` y `headers`.
3. **SSE (`sse_client`)**: Transporte legado Server-Sent Events (`transport: sse`).

## 3. Convención de Nombres y Filtrado Nativo de Herramientas (`tools/mcp_tool_registration.py`, `tools/mcp_tool_schema.py`)

- **Nombre registrado en el registry de Hermes**: `mcp__<servidor_sanitizado>__<herramienta_sanitizada>` (ej. `mcp__da_local_sandbox__da_echo`).
- **Allowlist nativa (`tools.include`)**: Lista blanca explícita de nombres de herramientas nativas del servidor MCP. Toma precedencia sobre `tools.exclude`. Cualquier herramienta expuesta por el servidor que NO figure en `tools.include` es omitida durante el registro (`skipping tool ... (filtered by config)`).
- **Superficie mínima de utilidades (`tools.resources: false`, `tools.prompts: false`)**: Deshabilita el registro automático de las 4 herramientas utilitarias (`list_resources`, `read_resource`, `list_prompts`, `get_prompt`).

## 4. Timeouts, Health Checks y Recuperación ante Fallos

- **Timeout por llamada (`timeout: 30`)**: Tiempo máximo en segundos para `session.call_tool()`.
- **Timeout de conexión inicial (`connect_timeout: 15`)**: Tiempo máximo en segundos para el handshake inicial y descubrimiento.
- **Detección de muerte de subproceso stdio (`_stdio_child_pids`)**: Si el proceso hijo muere o se cierra inesperadamente, las llamadas en vuelo fallan de forma estructurada sin colgar indefinidamente, y el cliente MCP marca la sesión para reconexión controlada.
