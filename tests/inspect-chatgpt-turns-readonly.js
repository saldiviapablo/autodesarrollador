'use strict';
// Read-only certification only: no bridge main(), ledger instance/lease, browser
// launch/navigation, input dispatch, focus, composer edits, or tab closure.
const assert = require('node:assert/strict'), fs = require('node:fs'), path = require('node:path');
const {validateDomain, guardPageExpression, verifyDedicatedProfile, readConversation} = require('../tools/chatgpt-bridge');
const {conversationBindings} = require('../tools/chatgpt-conversation');
const {inspectComposer} = require('../tools/chatgpt-send-actuator');
const {emptyConversation, freshReady} = require('../tools/chatgpt-fresh-chat');

async function evaluate(ws, expression) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {ws.removeEventListener('message', receive); reject(Error('READ_TIMEOUT'));}, 5000);
    function receive(event) {
      const message = JSON.parse(event.data);
      if (message.id !== 1) return;
      clearTimeout(timer); ws.removeEventListener('message', receive);
      if (message.error || message.result?.exceptionDetails) reject(Error('READ_EVALUATION_FAILED'));
      else resolve(message.result.result.value);
    }
    ws.addEventListener('message', receive);
    ws.send(JSON.stringify({id: 1, method: 'Runtime.evaluate', params: {expression: guardPageExpression(expression), returnByValue: true}}));
  });
}

(async () => {
  const directory = process.env.F24_PREFLIGHT_E;
  assert(directory, 'EXPLICIT_EVIDENCE_DIRECTORY_REQUIRED');
  assert.equal(JSON.parse(fs.readFileSync(path.join(directory, 'conversation-deterministic.json'), 'utf8')).status, 'PASS');
  const profile = verifyDedicatedProfile();
  const tabs = (await (await fetch('http://127.0.0.1:9222/json', {signal: AbortSignal.timeout(3000)})).json()).filter(t => t.type === 'page');
  assert.equal(tabs.length, 1); assert(validateDomain(tabs[0].url));
  let ws;
  try {
    ws = new WebSocket(tabs[0].webSocketDebuggerUrl);
    await new Promise((resolve, reject) => {
      const timer = setTimeout(() => {ws.close(); reject(Error('READ_CONNECT_TIMEOUT'));}, 5000);
      ws.onopen = () => {clearTimeout(timer); resolve();}; ws.onerror = () => {clearTimeout(timer); reject(Error('READ_CONNECT_FAILED'));};
    });
    const result = await evaluate(ws, `(() => {
      ${conversationBindings()}
      const snapshot = readConversationSnapshot();
      const composer = (${inspectComposer.toString()})();
      const raw = role => {
        for (const selector of ['[data-message-author-role="'+role+'"]', 'article[data-turn="'+role+'"]']) {
          const nodes = Array.from(document.querySelectorAll(selector)); if(nodes.length) return nodes.length;
        }
        const selector = role === 'user' ? '.bg-user-message' : '[class*="DilResponseRoot"]';
        return Array.from(document.querySelectorAll(selector)).filter(e => !e.parentElement?.closest(selector)).length;
      };
      return {url: snapshot.url, raw_user: raw('user'), raw_assistant: raw('assistant'),
        active_user: snapshot.user, active_assistant: snapshot.assistant,
        composer_empty: snapshot.composer_empty && composer.composer === '', isStreaming: snapshot.isStreaming,
        composer_found: composer.composer_found, composer_matches: composer.composer_matches,
        editable: composer.editable, focused: composer.focused, buttons: composer.buttons};
    })()`);
    // Also exercise the production bridge reader without entering bridge main().
    const actual = await readConversation(ws);
    assert.equal(actual.user, result.active_user); assert.equal(actual.assistant, result.active_assistant);
    assert.equal(actual.url, result.url); assert.equal(actual.composer_empty, result.composer_empty);
    const observation = {...result, user: result.active_user, assistant: result.active_assistant, composer: result.composer_empty ? '' : undefined};
    const emptyBaseline = emptyConversation(observation), ready = freshReady(observation);
    const proof = {at: new Date().toISOString(), status: emptyBaseline ? 'PASS' : 'FAIL', profile, ...result,
      production_reader_matches: true, FRESH_CHAT_EMPTY_BASELINE: emptyBaseline, FRESH_CHAT_READY_LIVE: ready,
      readiness_transition_certified_separately: 'conversation-deterministic.json',
      browser_input_actions: 0, ledger_access: false};
    fs.writeFileSync(path.join(directory, 'live-readonly.json'), JSON.stringify(proof, null, 2));
    console.log(JSON.stringify(proof, null, 2));
    assert(emptyBaseline, 'FRESH_CHAT_READONLY_BASELINE_NOT_EMPTY');
  } finally { if(ws) ws.close(); }
})().catch(error => {console.error(error); process.exitCode = 1;});
