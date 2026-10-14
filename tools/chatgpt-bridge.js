#!/usr/bin/env node
// ==============================================================================
// tools/chatgpt-bridge.js — Cliente CDP para Consulta a ChatGPT (Perfil Dedicado)
// Proyecto: Desarrollador Autónomo
// Versión: 2.0 (Macrofase 6 — Fase 14: Hardening de Unicode / UTF-8)
// ==============================================================================

const fs = require('fs');
const path = require('path');
const { spawn, spawnSync } = require('child_process');
const { ConsultationLedger, acquireBrowserLease, hash, normalize, reconcileObservation } = require('./chatgpt-ledger');
const { Budget, Trace, budgets, deliver } = require('./chatgpt-delivery');
let activeLedger;
let activeBudget, activeTrace, activeSocket, deadlineTimer;
async function safeExit(code) {
  clearTimeout(deadlineTimer);
  // Give Node WebSocket close handles one turn on Windows before process teardown.
  await new Promise(resolve => setTimeout(resolve, 75));
  process.exit(code);
}
process.once('exit', () => {
  if (!activeLedger) return;
  try {
    const record = activeLedger.read(consultationId);
    if (record && !record.message_confirmed && !['COMPLETED', 'COMPLETED_RECONCILED'].includes(record.delivery_state)) activeLedger.update(consultationId, { delivery_state: 'UNKNOWN_DELIVERY' });
    activeTrace?.emit('CLEANUP',{pid:process.pid});
  } catch {}
});

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
const humanEvidencePath = getArg('--human-evidence', '');
const newConversation = hasFlag('--new-conversation');
function preparedPrompt() {
  if (isRawPrompt || !(context || (purpose && purpose !== 'Revisión técnica' && purpose !== 'test'))) return question;
  return `CONSULTA TÉCNICA (ROL CONSULTOR ARQUITECTÓNICO):
Propósito: ${purpose || 'Revisión técnica'}
Pregunta: ${question}
Contexto:
${context}

Por favor proporciona:
1. Causa probable
2. Dos estrategias alternativas
3. Riesgos técnicos asociados`;
}
async function readConversation(ws) {
  const result = await sendCdp(ws, 'Runtime.evaluate', {
    expression: `(() => {
      const role = name => {
        const messages = Array.from(document.querySelectorAll('[data-message-author-role="' + name + '"]'));
        if (messages.length) return messages;
        const articles = Array.from(document.querySelectorAll('article[data-turn="' + name + '"]'));
        if (articles.length) return articles;
        // The current ChatGPT UI mirrors DIL content in the approved top document.
        // Count each outer message once; never attach to the cross-origin renderer iframe.
        const selector = name === 'user' ? '.bg-user-message' : '[class*="DilResponseRoot"]';
        return Array.from(document.querySelectorAll(selector)).filter(el => !el.parentElement?.closest(selector));
      };
      const users = role('user'), assistants = role('assistant');
      return { user: users.length, assistant: assistants.length,
        composer_empty: (()=>{const p=document.querySelector('.ProseMirror')||document.querySelector('#prompt-textarea')||document.querySelector('div[contenteditable="true"]');return !!p&&!p.innerText?.trim();})(),
        lastUserText: users.length ? users[users.length - 1].innerText.trim().replace(/^(You said:|Tú dijiste:)\\s*/i, '') : '',
        lastAssistantText: assistants.length ? assistants[assistants.length - 1].innerText.trim().replace(/^(ChatGPT said:|ChatGPT dijo:)\\s*/i, '') : '',
        isStreaming: !!document.querySelector('button[data-testid*="stop"],button[aria-label*="Stop"],button[aria-label*="Detener"],.result-streaming'),
        url: location.href };
    })()`, returnByValue: true
  });
  return result.result ? result.result.value : {};
}

async function readPrepared(ws) {
  const result = await sendCdp(ws, 'Runtime.evaluate', { expression: `(() => {
    const prose = document.querySelector('.ProseMirror') || document.querySelector('#prompt-textarea') || document.querySelector('div[contenteditable="true"]');
    const paragraphs = prose ? Array.from(prose.querySelectorAll('p')) : [];
    const composer = paragraphs.length ? paragraphs.map(p => p.innerText).join('\\n').trim() : (prose?.innerText || '').trim().replace(/\\r\\n/g,'\\n').replace(/\\n\\n+/g,'\\n');
    const selectors = 'button[data-testid="send-button"],button[data-testid="composer-submit-button"],button[aria-label="Enviar"],button[aria-label*="Send"],button[type="submit"]';
    const buttons = Array.from(document.querySelectorAll(selectors)).map(button => {
      const r = button.getBoundingClientRect();
      const aria=button.getAttribute('aria-label')||'', testid=button.getAttribute('data-testid');
      const expectedSend=/Send|Enviar/i.test(aria)||['send-button','composer-submit-button'].includes(testid)||(button.type==='submit'&&prose&&button.form?.contains(prose));
      const x=r.x+r.width/2,y=r.y+r.height/2,hit=document.elementFromPoint(x,y);
      return { x,y,width:r.width,height:r.height,disabled:button.disabled,aria,testid,expectedSend,hit:!!hit&&button.contains(hit),visible:r.width>0&&r.height>0&&getComputedStyle(button).visibility!=='hidden' };
    });
    return {composer,buttons,sendAvailable:buttons.filter(b=>b.visible&&!b.disabled&&b.expectedSend).length===1,url:location.href};
  })()`, returnByValue:true });
  return result.result?.value || {};
}

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

function verifyDedicatedProfile() {
  const expected=path.resolve(__dirname,'..','data','browser','HERMES-CHATGPT');
  if(path.resolve(profileDir).toLowerCase()!==expected.toLowerCase()) throw new Error('PROFILE_MISMATCH');
  const script=`$ErrorActionPreference='Stop';$expected='${expected.replace(/'/g,"''")}';$listener=Get-NetTCPConnection -LocalPort 9222 -State Listen|Select-Object -First 1;$owner=Get-CimInstance Win32_Process -Filter ('ProcessId='+$listener.OwningProcess);if($owner.Name -ne 'chrome.exe'){throw 'PROFILE_MISMATCH'};$match=[regex]::Match($owner.CommandLine,'(?:"--user-data-dir=(?<a>[^"]+)"|--user-data-dir="(?<b>[^"]+)"|--user-data-dir=(?<c>\\S+))');$actual=(@('a','b','c')|ForEach-Object {$match.Groups[$_].Value}|Where-Object {$_})|Select-Object -First 1;if(-not $actual -or [IO.Path]::GetFullPath($actual) -ne $expected){throw 'PROFILE_MISMATCH'};@{profile_match=$true;pid=$owner.ProcessId;profile=$expected}|ConvertTo-Json -Compress`;
  const result=spawnSync('powershell.exe',['-NoProfile','-NonInteractive','-EncodedCommand',Buffer.from(script,'utf16le').toString('base64')],{encoding:'utf8',timeout:10000,windowsHide:true});
  if(result.status!==0 || !JSON.parse(result.stdout).profile_match) throw new Error('PROFILE_MISMATCH');
  return JSON.parse(result.stdout);
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
    const timer=setTimeout(()=>{try{ws.close();}catch{}reject(Error('CDP_CONNECT_TIMEOUT'));},activeBudget?activeBudget.remaining(5000):5000);
    ws.onopen = () => {clearTimeout(timer);resolve(ws);};
    ws.onerror = (err) => {clearTimeout(timer);reject(err);};
  });
}

function sendCdpRaw(ws, method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = Math.floor(Math.random() * 1000000) + 1;
    const timeout = setTimeout(() => {
      ws.removeEventListener('message', handler);
      reject(new Error(`Timeout esperando respuesta CDP para ${method}`));
    }, activeBudget ? activeBudget.remaining(method==='Input.dispatchMouseEvent'?2000:5000) : 20000);

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

async function sendSinglePhysicalClick(ws, button, dispatch = sendCdp) {
  if (!button || !button.visible || button.disabled || !button.expectedSend ||
      !Number.isFinite(button.x) || !Number.isFinite(button.y)) {
    throw new Error('SEND_BUTTON_UNAVAILABLE_OR_AMBIGUOUS');
  }
  // One press/release pair only. A transport error is ambiguous: never fall back
  // to another click, submit, or Enter. The caller persists intent beforehand.
  activeTrace?.emit('MOUSE_PRESSED_START');
  await dispatch(ws, 'Input.dispatchMouseEvent', {type:'mousePressed',x:button.x,y:button.y,button:'left',buttons:1,pointerType:'mouse',clickCount:1});
  activeTrace?.emit('MOUSE_PRESSED_END');
  activeTrace?.emit('MOUSE_RELEASED_START');
  await dispatch(ws, 'Input.dispatchMouseEvent', {type:'mouseReleased',x:button.x,y:button.y,button:'left',buttons:0,pointerType:'mouse',clickCount:1});
  activeTrace?.emit('MOUSE_RELEASED_END');
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
  if(action==='budget'){console.log(JSON.stringify(budgets(timeoutSec)));return;}
  // Verificación inicial de Domain Lock para targetUrl
  if (!validateDomain(targetUrl)) {
    const out = {
      status: "DOMAIN_BLOCKED",
      error: `Intento de navegación a dominio no autorizado bloqueado: ${targetUrl}`,
      consultation_id: consultationId,
      timestamp: new Date().toISOString()
    };
    console.log(JSON.stringify(out, null, 2));
    await safeExit(2);
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
    await safeExit(0);
  }

  // Comprobar Chrome
  const ledger = new ConsultationLedger();
  if (action === 'consultation-status') {
    console.log(JSON.stringify(ledger.result(consultationId), null, 2));
    await safeExit(0);
  }
  const confirmedRetry = action === 'consult' && ledger.result(consultationId).status === 'RETRY_SAFE';
  if (action === 'consult' && ledger.read(consultationId) && !confirmedRetry) {
    console.log(JSON.stringify(ledger.result(consultationId), null, 2));
    await safeExit(0);
  }
  if (action === 'reconcile' && ledger.result(consultationId).response_received) {
    console.log(JSON.stringify({ ...ledger.result(consultationId), reconciled: true }, null, 2)); await safeExit(0);
  }
  acquireBrowserLease();
  if (action === 'consult') {
    if (!confirmedRetry && !ledger.reserve(consultationId, preparedPrompt())) {
      console.log(JSON.stringify(ledger.result(consultationId), null, 2)); await safeExit(0);
    }
    activeLedger = ledger;
    activeBudget = new Budget(timeoutSec);
    activeTrace = new Trace(ledger.file(consultationId).replace(/\.json$/,'.trace.jsonl'),consultationId);
    activeTrace.emit('BRIDGE_START',{pid:process.pid});
    deadlineTimer=setTimeout(async()=>{
      activeTrace.emit('TIMEOUT',{phase:'internal'});
      const confirmed=!!ledger.read(consultationId)?.message_confirmed;
      if(!confirmed)ledger.update(consultationId,{delivery_state:'UNKNOWN_DELIVERY'});
      try{activeSocket?.close();}catch{}
      console.log(JSON.stringify({status:confirmed?'SENT_CONFIRMED':'UNKNOWN_DELIVERY',response_state:'PENDING',no_resend:true,consultation_id:consultationId}));
      await safeExit(1);
    },activeBudget.spec.internal_ms);
  }
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
      await safeExit(1);
    }
  }
  if(['consult','reconcile-human','inspect-prepared'].includes(action)) verifyDedicatedProfile();

  // Enforzar single tab y domain lock
  const tabCheck = await enforceSingleTabAndDomainLock();
  if (!tabCheck.success && tabCheck.blocked) {
    console.log(JSON.stringify({
      status: "DOMAIN_BLOCKED",
      error: tabCheck.reason,
      consultation_id: consultationId,
      timestamp: new Date().toISOString()
    }, null, 2));
    await safeExit(2);
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
    await safeExit(0);
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
    await safeExit(1);
  }

  activeSocket=ws;
  if(newConversation && action==='consult' && !confirmedRetry){
    await sendCdp(ws,'Page.navigate',{url:'https://chatgpt.com/'});
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
      if (current && validateDomain(current.url) && current.ready !== 'loading' && (!newConversation || new URL(current.url).pathname==='/')) break;
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
        await safeExit(3);
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
        await safeExit(0);
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
        await safeExit(1);
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
      await safeExit(match ? 0 : 1);
    }

    if (action === 'inspect-prepared' || action === 'reconcile-human') {
      const record=ledger.read(consultationId);
      if(!record) throw new Error('CONSULTATION_NOT_RESERVED');
      const observation={...(await readConversation(ws)),...(await readPrepared(ws))};
      if(action==='reconcile-human') {
        const receiptText=fs.readFileSync(humanEvidencePath,'utf8');
        ledger.confirmNotDelivered(consultationId,JSON.parse(receiptText),observation,hash(receiptText));
      }
      console.log(JSON.stringify({ ...ledger.result(consultationId), observation:{user:observation.user,assistant:observation.assistant,isStreaming:observation.isStreaming,composer_sha256:hash(normalize(observation.composer||'')),expected_sha256:record.prompt_sha256,sendAvailable:observation.sendAvailable,buttons:observation.buttons,url:observation.url},physical_send_count:0 },null,2));
      ws.close();await safeExit(0);
    }
    if (action === 'reconcile') {
      const record = ledger.read(consultationId);
      if (!record) { console.log(JSON.stringify({ status: 'NOT_SEEN', consultation_id: consultationId, no_resend: true })); await safeExit(0); }
      const observation = await readConversation(ws);
      if (reconcileObservation(record, observation)) {
        ledger.update(consultationId, { delivery_state: 'COMPLETED_RECONCILED', message_confirmed: true,
          user_turns_after: observation.user, assistant_turns_after: observation.assistant, conversation_url: observation.url });
      }
      const reconciled = ledger.result(consultationId);
      console.log(JSON.stringify({ ...reconciled, reconciled: reconciled.status === 'ALREADY_SENT', no_resend: true, source: 'chatgpt_web_real' }, null, 2));
      ws.close(); await safeExit(0);
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
        await safeExit(3);
      }

      activeBudget.enter('prepare');
      const initialComposer=await readPrepared(ws);
      if(!confirmedRetry && normalize(initialComposer.composer||''))throw Error('PREEXISTING_COMPOSER_NO_SEND');
      // Preparar prompt final
      const fullPrompt = preparedPrompt();

      // 1. Contar turnos antes de enviar
      const countsBefore = await readConversation(ws);
      if(countsBefore.isStreaming)throw Error('STREAMING_BEFORE_SEND');
      if(confirmedRetry){
        const record=ledger.read(consultationId);
        if(countsBefore.user!==record.user_turns_before||countsBefore.assistant!==record.assistant_turns_before||countsBefore.isStreaming) throw new Error('RETRY_OBSERVATION_CHANGED_NO_SEND');
      }
      const turnsBefore = countsBefore.user;
      ledger.update(consultationId, { user_turns_before: countsBefore.user, assistant_turns_before: countsBefore.assistant, conversation_url: countsBefore.url });

      // 2. Inyectar texto en composer
      const injectRes = confirmedRetry ? { result:{value:{success:true,domText:(await readPrepared(ws)).composer}} } : await sendCdp(ws, 'Runtime.evaluate', {
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
        await safeExit(1);
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
          prompt_sha256: hash(normSource),
          dom_sha256: hash(normDom),
          source_text_equals_dom_text: false,
          consultation_id: consultationId,
          timestamp: new Date().toISOString()
        }, null, 2));
        ws.close();
        await safeExit(1);
      }

      // Stabilize the prepared, hit-testable composer before one physical click.
      await sendCdp(ws,'Page.bringToFront');
      let prepared;
      for(let stable=0;stable<2;stable++) {
        prepared=await readPrepared(ws);
        if(hash(normalize(prepared.composer||''))!==ledger.read(consultationId).prompt_sha256)throw Error('COMPOSER_CHANGED_NO_SEND');
        if(prepared.url!==countsBefore.url)throw Error('CONVERSATION_CHANGED_BEFORE_SEND');
        if(stable===0)await new Promise(r=>setTimeout(r,300));
      }
      const candidates=prepared.buttons?.filter(b=>b.visible&&!b.disabled&&b.expectedSend&&b.hit)||[];
      const physicalButton=candidates.length===1?candidates[0]:null;
      if(!physicalButton)throw Error('SEND_BUTTON_UNAVAILABLE_OR_AMBIGUOUS');
      const attemptCount=ledger.read(consultationId).send_attempts+1;
      const outcome=await deliver({ledger,id:consultationId,baseline:countsBefore,
        click:()=>sendSinglePhysicalClick(ws,physicalButton),
        probe:()=>readConversation(ws),
        budget:activeBudget,trace:activeTrace,newConversation});
      if(outcome.status!=='SUCCESS') {
        console.log(JSON.stringify({...outcome,consultation_id:consultationId,message_sent:!!ledger.read(consultationId).message_confirmed,response_received:false},null,2));
        ws.close();await safeExit(1);
      }
      const countsAfter=outcome.observation;
      const finalResponse=outcome.response;
      const messageSent=true;
      activeBudget.enter('finalize');
      const composerCleared=countsAfter.composer_empty===true;
      if(!composerCleared)throw Error('COMPOSER_NOT_CLEARED');
      ws.close();

      const out = {
        status: "SUCCESS",
        response: finalResponse,
        consultation_id: consultationId,
        source: "chatgpt_web_real",
        message_sent: messageSent,
        response_received: true,
        prompt_sha256: hash(normSource),
        dom_sha256: hash(normDom),
        source_text_equals_dom_text: textMatches,
        utf8_valid: Buffer.from(normSource,'utf8').toString('utf8')===normSource,
        url: pageState.url,
        user_turns_before: countsBefore.user, user_turns_after: countsAfter.user,
        assistant_turns_before: countsBefore.assistant, assistant_turns_after: countsAfter.assistant,
        no_resend: false, send_attempts: attemptCount,physical_send_count:1,composer_cleared:composerCleared,human_reconciled_retry:confirmedRetry,
        timestamp: new Date().toISOString()
      };

      console.log(JSON.stringify(out, null, 2));
      await safeExit(0);
    }
  } catch (err) {
    if (ws) {
      try { ws.close(); } catch {}
    }
    activeTrace?.emit('FAILURE',{reason:err.message.split(':')[0]});
    console.log(JSON.stringify({
      status: activeLedger?.read(consultationId)?.message_confirmed ? 'SENT_CONFIRMED' : err.message.includes('DOMAIN_BLOCKED') ? "DOMAIN_BLOCKED" : "ERROR",
      error: `Fallo durante interacción CDP: ${err.message}`,
      consultation_id: consultationId,
      timestamp: new Date().toISOString()
    }, null, 2));
    await safeExit(1);
  }
}

module.exports = { validateDomain, guardPageExpression, sendSinglePhysicalClick };

if (require.main === module) main().catch(async err => {
  console.log(JSON.stringify({
    status: err.message.includes('DOMAIN_BLOCKED') ? "DOMAIN_BLOCKED" : "ERROR",
    error: err.message,
    timestamp: new Date().toISOString()
  }, null, 2));
  await safeExit(1);
});
