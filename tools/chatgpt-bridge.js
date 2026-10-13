#!/usr/bin/env node
// ==============================================================================
// tools/chatgpt-bridge.js — Cliente CDP para Consulta a ChatGPT (Perfil Dedicado)
// Proyecto: Desarrollador Autónomo
// Versión: 2.0 (Macrofase 6 — Fase 14: Hardening de Unicode / UTF-8)
// ==============================================================================

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const CDP_PORT = 9222;
const CDP_BASE = `http://127.0.0.1:${CDP_PORT}`;

const CANONICAL_UNICODE_STRING = `Prueba UTF-8:
áéíóú ÁÉÍÓÚ
ñ Ñ
¿Dónde está?
¡Funciona!
— € °`;

// Parse arguments
const args = process.argv.slice(2);
function getArg(flag, defaultValue = '') {
  const idx = args.indexOf(flag);
  return idx !== -1 && idx + 1 < args.length ? args[idx + 1] : defaultValue;
}
const hasFlag = (flag) => args.includes(flag);

const action = getArg('--action', 'check-session');
const targetUrl = getArg('--url', 'https://chatgpt.com');
const profileDir = getArg('--profile-dir', path.resolve(__dirname, '..', 'data', 'browser', 'HERMES-CHATGPT'));

let question = getArg('--question', '');
const questionB64 = getArg('--question-b64', '');
if (questionB64) {
  try { question = Buffer.from(questionB64, 'base64').toString('utf8'); } catch {}
}

let context = getArg('--context', '');
const contextB64 = getArg('--context-b64', '');
if (contextB64) {
  try { context = Buffer.from(contextB64, 'base64').toString('utf8'); } catch {}
}

const purpose = getArg('--purpose', 'Revisión técnica');
const consultationId = getArg('--consultation-id', `consult-${Date.now()}`);
const mockResponse = getArg('--mock-response', '');
const isRawPrompt = hasFlag('--raw-prompt');
const timeoutSec = parseInt(getArg('--timeout', '60'), 10);

// 1. Verificación Estricta de Domain Lock
function validateDomain(urlStr) {
  try {
    if (typeof urlStr !== 'string' || !urlStr.trim()) return false;
    const u = new URL(urlStr);
    return u.protocol === 'https:' && u.hostname === 'chatgpt.com' &&
      !u.username && !u.password;
  } catch {
    return false;
  }
}

// 2. Comprobar si Chrome CDP responde
async function isChromeRunning() {
  try {
    const res = await fetch(`${CDP_BASE}/json/version`, { signal: AbortSignal.timeout(1500) });
    return res.ok;
  } catch {
    return false;
  }
}

// 3. Iniciar Chrome con Perfil Dedicado si no está activo
async function launchDedicatedChrome() {
  if (!fs.existsSync(profileDir)) {
    fs.mkdirSync(profileDir, { recursive: true });
  }

  const chromeArgs = [
    `--user-data-dir=${profileDir}`,
    `--remote-debugging-port=${CDP_PORT}`,
    `--remote-debugging-address=127.0.0.1`,
    '--remote-allow-origins=*',
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-sync',
    '--disable-extensions',
    '--disable-background-networking',
    '--window-size=1280,960',
    targetUrl
  ];

  const proc = spawn(CHROME_PATH, chromeArgs, {
    detached: true,
    stdio: 'ignore'
  });
  proc.unref();

  // Esperar readiness de CDP
  const start = Date.now();
  while (Date.now() - start < 15000) {
    if (await isChromeRunning()) return true;
    await new Promise(r => setTimeout(r, 400));
  }
  return false;
}

// 4. Conectar WebSocket a CDP
function connectCdp(wsUrl) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);
    ws.onopen = () => resolve(ws);
    ws.onerror = (err) => reject(err);
  });
}

function sendCdpRaw(ws, method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = Math.floor(Math.random() * 1000000) + 1;
    const timeout = setTimeout(() => {
      ws.removeEventListener('message', handler);
      reject(new Error(`Timeout esperando respuesta CDP para ${method}`));
    }, 20000);

    const handler = (evt) => {
      try {
        const msg = JSON.parse(evt.data);
        if (msg.id === id) {
          clearTimeout(timeout);
          ws.removeEventListener('message', handler);
          if (msg.error) reject(new Error(msg.error.message || 'Error CDP'));
          else resolve(msg.result);
        }
      } catch {}
    };

    ws.addEventListener('message', handler);
    ws.send(JSON.stringify({ id, method, params }));
  });
}

function guardPageExpression(expression) {
  // Check in the same renderer operation as the DOM action, including redirects.
  return `(() => {
    const pageUrl = new URL(window.location.href);
    if (pageUrl.protocol !== 'https:' || pageUrl.hostname !== 'chatgpt.com' ||
        pageUrl.username || pageUrl.password) throw new Error('DOMAIN_BLOCKED');
    const result = (${expression});
    const afterUrl = new URL(window.location.href);
    if (afterUrl.protocol !== 'https:' || afterUrl.hostname !== 'chatgpt.com' ||
        afterUrl.username || afterUrl.password) throw new Error('DOMAIN_BLOCKED');
    return result;
  })()`;
}

async function sendCdp(ws, method, params = {}) {
  const guarded = method === 'Runtime.evaluate'
    ? { ...params, expression: guardPageExpression(params.expression) }
    : params;
  const result = await sendCdpRaw(ws, method, guarded);
  if (result.exceptionDetails) {
    throw new Error(result.exceptionDetails.exception?.description ||
      result.exceptionDetails.text || 'CDP evaluation failed');
  }
  return result;
}

// 5. Enforzar 1 sola pestaña y Domain Lock
async function enforceSingleTabAndDomainLock() {
  const tabsRes = await fetch(`${CDP_BASE}/json`);
  const tabs = await tabsRes.json();
  const pages = tabs.filter(t => t.type === 'page');

  if (pages.length === 0) {
    throw new Error('No hay páginas abiertas en Chrome.');
  }

  // Cerrar pestañas extra (Regla: Máximo 1 pestaña controlada)
  for (let i = 1; i < pages.length; i++) {
    try {
      await fetch(`${CDP_BASE}/json/close/${pages[i].id}`);
    } catch {}
  }

  const activeTab = pages[0];
  // Validar Domain Lock
  if (!validateDomain(activeTab.url)) {
    try { await fetch(`${CDP_BASE}/json/close/${activeTab.id}`); } catch {}
    return {
      success: false,
      blocked: true,
      reason: `DOMAIN_BLOCKED: La pestaña navegó a dominio no autorizado: ${activeTab.url}`
    };
  }

  return {
    success: true,
    tab: activeTab
  };
}

async function main() {
  // Verificación inicial de Domain Lock para targetUrl
  if (!validateDomain(targetUrl)) {
    const out = {
      status: "DOMAIN_BLOCKED",
      error: `Intento de navegación a dominio no autorizado bloqueado: ${targetUrl}`,
      consultation_id: consultationId,
      timestamp: new Date().toISOString()
    };
    console.log(JSON.stringify(out, null, 2));
    process.exit(2);
  }

  // Manejo de Mock Response si explícitamente se solicita
  if (mockResponse) {
    const out = {
      status: "SUCCESS",
      response: mockResponse,
      consultation_id: consultationId,
      source: "chatgpt_consultant_mock",
      timestamp: new Date().toISOString()
    };
    console.log(JSON.stringify(out, null, 2));
    process.exit(0);
  }

  // Comprobar Chrome
  const running = await isChromeRunning();
  if (!running) {
    const launched = await launchDedicatedChrome();
    if (!launched) {
      console.log(JSON.stringify({
        status: "ERROR",
        error: "No se pudo iniciar Chrome con el perfil dedicado HERMES-CHATGPT.",
        consultation_id: consultationId,
        timestamp: new Date().toISOString()
      }, null, 2));
      process.exit(1);
    }
  }

  // Enforzar single tab y domain lock
  const tabCheck = await enforceSingleTabAndDomainLock();
  if (!tabCheck.success && tabCheck.blocked) {
    console.log(JSON.stringify({
      status: "DOMAIN_BLOCKED",
      error: tabCheck.reason,
      consultation_id: consultationId,
      timestamp: new Date().toISOString()
    }, null, 2));
    process.exit(2);
  }

  const activeTab = tabCheck.tab;

  // Si la acción es solo cerrar el navegador de forma controlada vía CDP
  if (action === 'close-browser') {
    try {
      const verRes = await fetch(`${CDP_BASE}/json/version`);
      const verData = await verRes.json();
      if (verData.webSocketDebuggerUrl) {
        const browserWs = await connectCdp(verData.webSocketDebuggerUrl);
        await sendCdp(browserWs, 'Browser.close');
        browserWs.close();
      }
    } catch {}
    console.log(JSON.stringify({ status: "SUCCESS", message: "Navegador cerrado limpiamente vía CDP Browser.close." }, null, 2));
    process.exit(0);
  }

  // Conectar WebSocket a la página activa
  let ws;
  try {
    ws = await connectCdp(activeTab.webSocketDebuggerUrl);
  } catch (err) {
    console.log(JSON.stringify({
      status: "ERROR",
      error: `Error conectando WebSocket CDP: ${err.message}`,
      consultation_id: consultationId,
      timestamp: new Date().toISOString()
    }, null, 2));
    process.exit(1);
  }

  try {
    // CDP may expose the intended tab before its initial about:blank document
    // has committed. Read only URL/readiness metadata; perform no DOM action
    // until the exact approved origin has loaded. Every DOM operation below
    // still checks the origin inside the same Runtime.evaluate call.
    const readinessStarted = Date.now();
    while (true) {
      const metadata = await sendCdpRaw(ws, 'Runtime.evaluate', {
        expression: '({ url: window.location.href, ready: document.readyState })',
        returnByValue: true,
      });
      const current = metadata.result?.value;
      if (current && validateDomain(current.url) && current.ready !== 'loading') break;
      if (current && current.url !== 'about:blank' && !validateDomain(current.url)) {
        throw new Error('DOMAIN_BLOCKED');
      }
      if (Date.now() - readinessStarted >= 15000) throw new Error('PAGE_READINESS_TIMEOUT');
      await new Promise(resolve => setTimeout(resolve, 250));
    }
    // Evaluar estado de sesión en chatgpt.com
    const evalResult = await sendCdp(ws, 'Runtime.evaluate', {
      expression: `(() => {
        const url = window.location.href;
        const bodyText = document.body ? document.body.innerText : '';
        const hasPromptBox = !!document.querySelector('.ProseMirror') ||
                             !!document.querySelector('#prompt-textarea') ||
                             !!document.querySelector('div[contenteditable="true"]');
        const hasLoginButton = !!document.querySelector('button[data-testid="login-button"]') ||
                               url.includes('/auth/login') ||
                               (bodyText.includes('Log in') && !hasPromptBox);
        return { url, hasPromptBox, hasLoginButton, title: document.title };
      })()`,
      returnByValue: true
    });

    const pageState = evalResult.result ? evalResult.result.value : {};

    // Acción check-session
    if (action === 'check-session') {
      if (pageState.hasLoginButton && !pageState.hasPromptBox) {
        console.log(JSON.stringify({
          status: "BLOCKED_REQUIRES_HUMAN_LOGIN",
          profile_dir: profileDir,
          url: pageState.url,
          message: "Se requiere iniciar sesión manualmente en ChatGPT una sola vez en el perfil HERMES-CHATGPT.",
          timestamp: new Date().toISOString()
        }, null, 2));
        try { ws.close(); } catch {}
        setTimeout(() => process.exit(3), 50);
        return;
      } else {
        console.log(JSON.stringify({
          status: "SUCCESS",
          profile_dir: profileDir,
          session_ready: pageState.hasPromptBox,
          url: pageState.url,
          timestamp: new Date().toISOString()
        }, null, 2));
        try { ws.close(); } catch {}
        setTimeout(() => process.exit(0), 50);
        return;
      }
    }

    // Acción unicode-roundtrip (Verificación determinista del DOM sin enviar prompt)
    if (action === 'unicode-roundtrip') {
      const testText = question || CANONICAL_UNICODE_STRING;

      const roundtripRes = await sendCdp(ws, 'Runtime.evaluate', {
        expression: `(() => {
          const prose = document.querySelector('.ProseMirror') ||
                        document.querySelector('#prompt-textarea') ||
                        document.querySelector('div[contenteditable="true"]');
          if (!prose) return { success: false, reason: 'Composer not found' };

          prose.focus();
          document.execCommand('selectAll', false, null);
          document.execCommand('insertText', false, ${JSON.stringify(testText)});
          prose.dispatchEvent(new Event('input', { bubbles: true }));

          const rawInnerText = (prose.innerText || '').trim();
          const pElements = Array.from(prose.querySelectorAll('p'));
          const domText = pElements.length > 0
            ? pElements.map(p => p.innerText).join('\\n').trim()
            : rawInnerText.replace(/\\r\\n/g, '\\n').replace(/\\n\\n+/g, '\\n').trim();

          // Limpiar composer inmediatamente
          document.execCommand('selectAll', false, null);
          document.execCommand('delete', false, null);
          prose.dispatchEvent(new Event('input', { bubbles: true }));

          return { success: true, domText, rawInnerText };
        })()`,
        returnByValue: true
      });

      const rtVal = roundtripRes.result ? roundtripRes.result.value : {};
      if (!rtVal.success) {
        console.log(JSON.stringify({
          status: "ERROR",
          error: `Fallo durante roundtrip en composer: ${rtVal.reason || 'Desconocido'}`,
          timestamp: new Date().toISOString()
        }, null, 2));
        ws.close();
        process.exit(1);
      }

      const normSource = testText.trim().replace(/\r\n/g, '\n').replace(/\n\n+/g, '\n');
      const normDom = (rtVal.domText || '').trim().replace(/\r\n/g, '\n').replace(/\n\n+/g, '\n');
      const match = (normSource === normDom);

      const out = {
        status: match ? "SUCCESS" : "CHATGPT_ENCODING_MISMATCH",
        unicode_roundtrip: match ? "PASS" : "FAIL",
        source_text: normSource,
        dom_text: normDom,
        source_text_equals_dom_text: match,
        checkpoints: {
          source_text: normSource,
          node_decoded_string: testText,
          cdp_input_string: testText,
          dom_composer_text: normDom
        },
        timestamp: new Date().toISOString()
      };

      console.log(JSON.stringify(out, null, 2));
      try { ws.close(); } catch {}
      process.exit(match ? 0 : 1);
    }

    // Acción consult
    if (action === 'consult') {
      if (pageState.hasLoginButton && !pageState.hasPromptBox) {
        console.log(JSON.stringify({
          status: "BLOCKED_REQUIRES_HUMAN_LOGIN",
          error: "No existe sesión activa en ChatGPT. El usuario debe iniciar sesión manualmente una sola vez.",
          consultation_id: consultationId,
          timestamp: new Date().toISOString()
        }, null, 2));
        ws.close();
        process.exit(3);
      }

      // Preparar prompt final
      let fullPrompt = question;
      if (!isRawPrompt && (context || (purpose && purpose !== 'Revisión técnica' && purpose !== 'test'))) {
        fullPrompt = `CONSULTA TÉCNICA (ROL CONSULTOR ARQUITECTÓNICO):
Propósito: ${purpose || 'Revisión técnica'}
Pregunta: ${question}
Contexto:
${context}

Por favor proporciona:
1. Causa probable
2. Dos estrategias alternativas
3. Riesgos técnicos asociados`;
      }

      // 1. Contar turnos antes de enviar
      const countResBefore = await sendCdp(ws, 'Runtime.evaluate', {
        expression: `(() => {
          const articles = document.querySelectorAll('article[data-testid^="conversation-turn-"]');
          const userTurns = document.querySelectorAll('[data-message-author-role="user"]');
          return Math.max(articles.length, userTurns.length);
        })()`,
        returnByValue: true
      });
      const turnsBefore = countResBefore.result ? countResBefore.result.value : 0;

      // 2. Inyectar texto en composer
      const injectRes = await sendCdp(ws, 'Runtime.evaluate', {
        expression: `(() => {
          const prose = document.querySelector('.ProseMirror') ||
                        document.querySelector('#prompt-textarea') ||
                        document.querySelector('div[contenteditable="true"]');
          if (!prose) return { success: false, reason: 'Composer not found' };

          prose.focus();
          document.execCommand('selectAll', false, null);
          document.execCommand('insertText', false, ${JSON.stringify(fullPrompt)});
          prose.dispatchEvent(new Event('input', { bubbles: true }));

          const rawInnerText = (prose.innerText || '').trim();
          const pElements = Array.from(prose.querySelectorAll('p'));
          const domText = pElements.length > 0
            ? pElements.map(p => p.innerText).join('\\n').trim()
            : rawInnerText.replace(/\\r\\n/g, '\\n').replace(/\\n\\n+/g, '\\n').trim();

          return { success: true, domText, rawInnerText };
        })()`,
        returnByValue: true
      });

      const injectVal = injectRes.result ? injectRes.result.value : {};
      if (!injectVal.success) {
        console.log(JSON.stringify({
          status: "ERROR",
          error: `Fallo al inyectar mensaje: ${injectVal.reason || 'Desconocido'}`,
          consultation_id: consultationId,
          timestamp: new Date().toISOString()
        }, null, 2));
        ws.close();
        process.exit(1);
      }

      // 3. Verificación Pre-Send Obligatoria: SOURCE_TEXT === DOM_TEXT
      const normSource = fullPrompt.trim().replace(/\r\n/g, '\n').replace(/\n\n+/g, '\n');
      const normDom = (injectVal.domText || '').trim().replace(/\r\n/g, '\n').replace(/\n\n+/g, '\n');
      const textMatches = (normSource === normDom);

      if (!textMatches) {
        // Limpiar composer y abortar envío
        await sendCdp(ws, 'Runtime.evaluate', {
          expression: `(() => {
            const prose = document.querySelector('.ProseMirror') || document.querySelector('#prompt-textarea') || document.querySelector('div[contenteditable="true"]');
            if (prose) {
              prose.focus();
              document.execCommand('selectAll', false, null);
              document.execCommand('delete', false, null);
              prose.dispatchEvent(new Event('input', { bubbles: true }));
            }
          })()`
        });

        console.log(JSON.stringify({
          status: "CHATGPT_ENCODING_MISMATCH",
          error: "El texto inyectado en el DOM no coincide carácter por carácter con el texto origen.",
          source_text: normSource,
          dom_text: normDom,
          source_text_equals_dom_text: false,
          consultation_id: consultationId,
          timestamp: new Date().toISOString()
        }, null, 2));
        ws.close();
        process.exit(1);
      }

      // 4. Si el texto coincide exactamente: Pulsar Enviar
      const sendClickRes = await sendCdp(ws, 'Runtime.evaluate', {
        expression: `(() => {
          const prose = document.querySelector('.ProseMirror') || document.querySelector('#prompt-textarea') || document.querySelector('div[contenteditable="true"]');
          const form = prose ? prose.closest('form') : null;
          const sendBtn = form ? (
            form.querySelector('button[type="submit"]') ||
            form.querySelector('button[aria-label="Enviar"]') ||
            form.querySelector('button[data-testid="send-button"]') ||
            form.querySelector('button[aria-label*="Send"]')
          ) : (
            document.querySelector('button[data-testid="send-button"]') ||
            document.querySelector('button[aria-label="Enviar"]') ||
            document.querySelector('button[aria-label*="Send"]')
          );

          if (sendBtn && !sendBtn.disabled) {
            sendBtn.click();
            return { success: true, method: 'button_click' };
          } else if (form) {
            form.requestSubmit();
            return { success: true, method: 'form_submit' };
          } else if (prose) {
            prose.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
            return { success: true, method: 'enter_key' };
          }
          return { success: false, reason: 'Send trigger failed' };
        })()`,
        returnByValue: true
      });

      // 5. Confirmar que el mensaje fue enviado (CHATGPT_MESSAGE_SENT = true)
      let messageSent = false;
      const sendStart = Date.now();
      while (Date.now() - sendStart < 12000) {
        await new Promise(r => setTimeout(r, 600));
        const checkTurn = await sendCdp(ws, 'Runtime.evaluate', {
          expression: `(() => {
            const articles = document.querySelectorAll('article[data-testid^="conversation-turn-"]');
            const userTurns = document.querySelectorAll('[data-message-author-role="user"]');
            const main = document.querySelector('main');
            const hasUserText = main ? (main.innerText.includes('Tú dijiste:') || main.innerText.includes('You said:')) : false;
            const isStreaming = !!document.querySelector('button[data-testid*="stop"]') ||
                                !!document.querySelector('button[aria-label*="Detener"]') ||
                                !!document.querySelector('button[aria-label*="Stop"]') ||
                                !!document.querySelector('.result-streaming');
            return {
              count: Math.max(articles.length, userTurns.length),
              hasUserText,
              isStreaming
            };
          })()`,
          returnByValue: true
        });

        const turnVal = checkTurn.result ? checkTurn.result.value : {};
        if (turnVal.count > turnsBefore || turnVal.hasUserText || turnVal.isStreaming) {
          messageSent = true;
          break;
        }
      }

      // 6. Aguardar respuesta del asistente (CHATGPT_RESPONSE_RECEIVED = true)
      let finalResponse = "";
      let lastText = "";
      let stableCount = 0;
      const genStart = Date.now();

      while (Date.now() - genStart < timeoutSec * 1000) {
        await new Promise(r => setTimeout(r, 1200));

        const checkRes = await sendCdp(ws, 'Runtime.evaluate', {
          expression: `(() => {
            const isStreaming = !!document.querySelector('button[data-testid*="stop"]') ||
                                !!document.querySelector('button[aria-label*="Detener"]') ||
                                !!document.querySelector('button[aria-label*="Stop"]') ||
                                !!document.querySelector('.result-streaming');

            // Estrategia 1: DilResponseRoot / PortalBoundary / agent-turn / markdown
            const dilRoots = Array.from(document.querySelectorAll('[class*="DilResponseRoot"], [class*="PortalBoundary"], [class*="agent-turn"], [class*="markdown"]'))
              .map(el => el.innerText.trim())
              .filter(t => t.length > 0 && !t.includes('Tú dijiste:') && !t.includes('You said:'));
            let text = dilRoots.length > 0 ? dilRoots[dilRoots.length - 1] : '';

            // Estrategia 2: split por 'ChatGPT dijo:' o 'ChatGPT said:'
            if (!text) {
              const main = document.querySelector('main');
              if (main) {
                const parts = main.innerText.split(/ChatGPT dijo:|ChatGPT said:/i);
                if (parts.length > 1) {
                  text = parts[parts.length - 1].split(/ChatGPT puede cometer|Última respuesta/i)[0].trim();
                }
              }
            }

            return { isStreaming, text: (text || '').trim() };
          })()`,
          returnByValue: true
        });

        const resVal = checkRes.result ? checkRes.result.value : null;
        if (resVal && resVal.text) {
          if (!resVal.isStreaming) {
            if (resVal.text === lastText) {
              stableCount++;
              if (stableCount >= 2) { // Estable por ~2.4s y sin indicador de streaming
                finalResponse = resVal.text;
                break;
              }
            } else {
              lastText = resVal.text;
              stableCount = 1;
            }
          } else {
            lastText = resVal.text;
            stableCount = 0;
          }
        }
      }

      ws.close();

      if (!finalResponse) {
        console.log(JSON.stringify({
          status: "TIMEOUT",
          error: `Timeout esperando respuesta completa tras ${timeoutSec}s`,
          message_sent: messageSent,
          consultation_id: consultationId,
          timestamp: new Date().toISOString()
        }, null, 2));
        process.exit(1);
      }

      const out = {
        status: "SUCCESS",
        response: finalResponse,
        consultation_id: consultationId,
        source: "chatgpt_web_real",
        message_sent: messageSent,
        response_received: true,
        source_text: normSource,
        dom_text: normDom,
        source_text_equals_dom_text: textMatches,
        url: pageState.url,
        timestamp: new Date().toISOString()
      };

      console.log(JSON.stringify(out, null, 2));
      process.exit(0);
    }
  } catch (err) {
    if (ws) {
      try { ws.close(); } catch {}
    }
    console.log(JSON.stringify({
      status: err.message.includes('DOMAIN_BLOCKED') ? "DOMAIN_BLOCKED" : "ERROR",
      error: `Fallo durante interacción CDP: ${err.message}`,
      consultation_id: consultationId,
      timestamp: new Date().toISOString()
    }, null, 2));
    process.exit(1);
  }
}

module.exports = { validateDomain, guardPageExpression };

if (require.main === module) main().catch(err => {
  console.log(JSON.stringify({
    status: err.message.includes('DOMAIN_BLOCKED') ? "DOMAIN_BLOCKED" : "ERROR",
    error: err.message,
    timestamp: new Date().toISOString()
  }, null, 2));
  process.exit(1);
});
