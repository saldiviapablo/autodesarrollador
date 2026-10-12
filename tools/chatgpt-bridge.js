#!/usr/bin/env node
// ==============================================================================
// tools/chatgpt-bridge.js — Cliente CDP para Consulta a ChatGPT (Perfil Dedicado)
// Proyecto: Desarrollador Autónomo
// Versión: 2.0 (Macrofase 6 — Fase 14: Chrome Dedicado + ChatGPT)
// ==============================================================================

const fs = require('fs');
const path = require('path');
const { spawn, execSync } = require('child_process');

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const CDP_PORT = 9222;
const CDP_BASE = `http://127.0.0.1:${CDP_PORT}`;
const ALLOWED_DOMAINS = ['chatgpt.com', 'openai.com'];

// Parse arguments
const args = process.argv.slice(2);
function getArg(flag, defaultValue = '') {
  const idx = args.indexOf(flag);
  return idx !== -1 && idx + 1 < args.length ? args[idx + 1] : defaultValue;
}
const hasFlag = (flag) => args.includes(flag);

const action = getArg('--action', 'check-session');
const targetUrl = getArg('--url', 'https://chatgpt.com');
const profileDir = getArg('--profile-dir', path.resolve(__dirname, '..', 'runtime', 'chrome', 'HERMES-CHATGPT'));
const question = getArg('--question', '');
const context = getArg('--context', '');
const purpose = getArg('--purpose', 'Revisión técnica');
const consultationId = getArg('--consultation-id', `consult-${Date.now()}`);
const mockResponse = getArg('--mock-response', '');
const timeoutSec = parseInt(getArg('--timeout', '40'), 10);

// 1. Verificación Estricta de Domain Lock
function validateDomain(urlStr) {
  try {
    if (!urlStr || urlStr === 'about:blank') return true;
    const u = new URL(urlStr);
    const host = u.hostname.toLowerCase();
    const isAllowed = ALLOWED_DOMAINS.some(d => host === d || host.endsWith('.' + d));
    return isAllowed;
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
    '--window-size=1200,900',
    targetUrl
  ];

  const proc = spawn(CHROME_PATH, chromeArgs, {
    detached: true,
    stdio: 'ignore'
  });
  proc.unref();

  // Esperar readiness de CDP
  const start = Date.now();
  while (Date.now() - start < 10000) {
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

function sendCdp(ws, method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = Math.floor(Math.random() * 1000000) + 1;
    const timeout = setTimeout(() => {
      ws.removeEventListener('message', handler);
      reject(new Error(`Timeout esperando respuesta CDP para ${method}`));
    }, 15000);

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
    // Cerrar pestaña si violó dominio
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

  // Manejo de Mock Response para tests deterministas y sin login
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

  // Si la acción es solo cerrar el navegador
  if (action === 'close-browser') {
    try {
      execSync('taskkill /F /IM chrome.exe 2>nul');
    } catch {}
    console.log(JSON.stringify({ status: "SUCCESS", message: "Navegador cerrado." }, null, 2));
    process.exit(0);
  }

  // Conectar WebSocket
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
    // Evaluar estado de sesión en chatgpt.com
    const evalResult = await sendCdp(ws, 'Runtime.evaluate', {
      expression: `(() => {
        const url = window.location.href;
        const bodyText = document.body ? document.body.innerText : '';
        const hasPromptBox = !!document.querySelector('#prompt-textarea') || !!document.querySelector('div[contenteditable="true"]');
        const hasLoginButton = !!document.querySelector('button[data-testid="login-button"]') || url.includes('/auth/login') || bodyText.includes('Log in');
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

      // Preparar consulta sanitizada
      const fullPrompt = `CONSULTA TÉCNICA (ROL CONSULTOR ARQUITECTÓNICO):
Propósito: ${purpose || 'Revisión técnica'}
Pregunta: ${question}
Contexto:
${context}

Por favor proporciona:
1. Causa probable
2. Dos estrategias alternativas
3. Riesgos técnicos asociados`;

      // Inyectar en prompt-textarea
      const injectRes = await sendCdp(ws, 'Runtime.evaluate', {
        expression: `(() => {
          const textarea = document.querySelector('#prompt-textarea') || document.querySelector('div[contenteditable="true"]');
          if (!textarea) return false;
          if (textarea.tagName === 'TEXTAREA') {
            textarea.value = ${JSON.stringify(fullPrompt)};
            textarea.dispatchEvent(new Event('input', { bubbles: true }));
          } else {
            textarea.innerText = ${JSON.stringify(fullPrompt)};
            textarea.dispatchEvent(new Event('input', { bubbles: true }));
          }
          const sendBtn = document.querySelector('button[data-testid="send-button"]') || document.querySelector('button[aria-label="Send prompt"]');
          if (sendBtn && !sendBtn.disabled) {
            sendBtn.click();
            return true;
          }
          return false;
        })()`,
        returnByValue: true
      });

      // Aguardar respuesta (extracción del último mensaje del asistente)
      // Esperar hasta timeoutSec segundos a que deje de streamear
      let finalResponse = "";
      const startTime = Date.now();
      while (Date.now() - startTime < timeoutSec * 1000) {
        await new Promise(r => setTimeout(r, 2000));
        const checkDone = await sendCdp(ws, 'Runtime.evaluate', {
          expression: `(() => {
            const articles = document.querySelectorAll('article[data-testid^="conversation-turn-"]');
            if (articles.length === 0) return { done: false, text: '' };
            const lastArticle = articles[articles.length - 1];
            const isStreaming = !!document.querySelector('.result-streaming');
            return { done: !isStreaming, text: lastArticle.innerText };
          })()`,
          returnByValue: true
        });

        const val = checkDone.result ? checkDone.result.value : null;
        if (val && val.done && val.text) {
          finalResponse = val.text;
          break;
        }
      }

      ws.close();

      if (!finalResponse) {
        console.log(JSON.stringify({
          status: "TIMEOUT",
          error: "Timeout esperando respuesta completa de ChatGPT.",
          consultation_id: consultationId,
          timestamp: new Date().toISOString()
        }, null, 2));
        process.exit(1);
      }

      console.log(JSON.stringify({
        status: "SUCCESS",
        response: finalResponse,
        consultation_id: consultationId,
        timestamp: new Date().toISOString()
      }, null, 2));
      process.exit(0);
    }
  } catch (err) {
    if (ws) ws.close();
    console.log(JSON.stringify({
      status: "ERROR",
      error: `Fallo durante interacción CDP: ${err.message}`,
      consultation_id: consultationId,
      timestamp: new Date().toISOString()
    }, null, 2));
    process.exit(1);
  }
}

main().catch(err => {
  console.log(JSON.stringify({
    status: "ERROR",
    error: err.message,
    timestamp: new Date().toISOString()
  }, null, 2));
  process.exit(1);
});
