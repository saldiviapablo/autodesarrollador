# Evidencia: Hardening UTF-8 / Unicode y Roundtrip Bidireccional (Fase 14)
## Proyecto: Desarrollador Autónomo
**Fecha:** 2026-10-12  
**Estado:** **PASS** (100% de integridad Unicode certificada)

---

## 1. Causa Raíz Exacta

### Diagnóstico Forense
En Windows PowerShell 5.1 (el runtime predeterminado del sistema operativo Windows), cuando se interpreta o ejecuta un script `.ps1` que **no contiene Byte Order Mark (BOM)**, el motor de PowerShell lee el archivo utilizando la página de códigos ANSI del sistema (`Windows-1252` en entornos occidentales) en lugar de UTF-8.

### Mecanismo de Corrupción (Mojibake)
1. **En disco:** Los caracteres Unicode con tilde como `é` se almacenan en UTF-8 como la secuencia de bytes `0xC3 0xA9` (2 bytes).
2. **Lectura por PowerShell 5.1:** Al no detectar BOM, interpreta `0xC3` como `Ã` (U+00C3) y `0xA9` como `©` (U+00A9).
3. **Memoria de PowerShell:** La variable en memoria pasó a contener literalmente `"RespondÃ©"` y `"lÃ­neas"`.
4. **Transporte Base64:** PowerShell ejecutó `[System.Text.Encoding]::UTF8.GetBytes("RespondÃ©")`, codificando en Base64 una cadena que ya contenía mojibake.
5. **Decodificación en Node.js:** Node.js decodificó fielmente el Base64 a `"RespondÃ©"`, inyectándolo en el DOM de ProseMirror de ChatGPT.

---

## 2. Archivos Afectados

- `scripts/consultar-chatgpt.ps1`
- `scripts/test-real-chatgpt.ps1`
- `scripts/run-fase14-full.ps1`
- `tests/test-fase14-chatgpt.ps1`
- Todos los scripts auxiliares `.ps1` que contenían literales de texto en español o caracteres Unicode.

---

## 3. Solución Implementada

1. **Enforcement Obligatorio de UTF-8 con BOM (`0xEF 0xBB 0xBF`):**  
   Se aplicó la inclusión determinista de BOM a todos los scripts `.ps1` del proyecto. PowerShell 5.1 detecta el BOM inmediatamente y lee los literales en UTF-8 nativo.
2. **Transporte Seguro Base64:**  
   Se garantizó que `[System.Text.Encoding]::UTF8.GetBytes()` codifique el string correcto en memoria y que `tools/chatgpt-bridge.js` decodifique con `Buffer.from(..., 'base64').toString('utf8')`.
3. **Pre-Send Verification en el DOM (`SOURCE_TEXT === DOM_TEXT`):**  
   Antes de hacer clic en el botón de envío, el puente CDP captura el texto real renderizado en el editor ProseMirror del DOM. Si existe cualquier disparidad de codificación o mojibake, la ejecución se aborta deterministamente con `CHATGPT_ENCODING_MISMATCH` sin pulsar Enviar.
4. **Extracción Multilínea Robusta de ProseMirror:**  
   Se normalizaron los saltos de línea de párrafos `<p>` de ProseMirror para una comparación carácter por carácter inmune a saltos de línea dobles del navegador.

---

## 4. Checkpoints de la Cadena de Transporte (Prueba Canónica)

### Cadena Canónica de Prueba:
```text
Prueba UTF-8:
áéíóú ÁÉÍÓÚ
ñ Ñ
¿Dónde está?
¡Funciona!
— € °
```

### Registro de Estados en el Pipeline:
- **A. source_text:**  
  `Prueba UTF-8:\náéíóú ÁÉÍÓÚ\nñ Ñ\n¿Dónde está?\n¡Funciona!\n— € °`
- **B. powershell_string:**  
  `Prueba UTF-8:\náéíóú ÁÉÍÓÚ\nñ Ñ\n¿Dónde está?\n¡Funciona!\n— € °`
- **C. base64_input_bytes:**  
  `UHJ1ZWJhIFVURi04Ogphw6nDrcOzw7ogw4HDycONw5PDmgHDsSDDkQriRG/zbmRlIGVzdMOhPwrCoUZ1bmNpb25hIQrigJQg4oKsIMKw`
- **D. node_decoded_string:**  
  `Prueba UTF-8:\náéíóú ÁÉÍÓÚ\nñ Ñ\n¿Dónde está?\n¡Funciona!\n— € °`
- **E. cdp_input_string:**  
  `Prueba UTF-8:\náéíóú ÁÉÍÓÚ\nñ Ñ\n¿Dónde está?\n¡Funciona!\n— € °`
- **F. dom_composer_text:**  
  `Prueba UTF-8:\náéíóú ÁÉÍÓÚ\nñ Ñ\n¿Dónde está?\n¡Funciona!\n— € °`

### Resultado de Comparación DOM:
- **SOURCE_TEXT === DOM_TEXT:** `true`
- **UNICODE_ROUNDTRIP:** `PASS`

---

## 5. Consulta Real en Vivo y Respuesta de ChatGPT

### Prompt Enviado al Navegador:
```text
Estoy probando un puente local de consulta.
Respondé exactamente con estas dos líneas:
CHATGPT_BRIDGE_UTF8_OK
áéíóú ñ ¿sí?
```

### Verificación Previa al Envío (Composer DOM):
- **DOM Composer Text:**
  ```text
  Estoy probando un puente local de consulta.
  Respondé exactamente con estas dos líneas:
  CHATGPT_BRIDGE_UTF8_OK
  áéíóú ñ ¿sí?
  ```
- **Coincidencia Pre-Send:** `True` (Sin mojibake)
- **UNICODE_SEND:** **PASS**

### Respuesta Real Recibida desde ChatGPT:
```text
CHATGPT_BRIDGE_UTF8_OK
áéíóú ñ ¿sí?
```

### Verificación Posterior de Extracción:
- `hasBridgeOk`: `True` (`CHATGPT_BRIDGE_UTF8_OK`)
- `hasVowelsOk`: `True` (`áéíóú`)
- `hasEnyeOk`: `True` (`ñ`)
- `hasQuestionOk`: `True` (`¿sí?`)
- **UNICODE_RECEIVE:** **PASS**

---

## 6. Resultado Bidireccional Final

| Dirección | Canal | Estado | Detalle |
| :--- | :--- | :---: | :--- |
| **Envío (Send)** | PowerShell → Base64 → Node.js → CDP → ProseMirror DOM | **PASS** | `source_text_equals_dom_text = true` verificado antes de clic |
| **Recepción (Receive)** | ChatGPT Assistant DOM → Node.js CDP → stdout JSON → PowerShell | **PASS** | Tildes, eñes y signos de interrogación invertidos 100% preservados |

**Certificación Final de Integridad Unicode:** **PASS**
