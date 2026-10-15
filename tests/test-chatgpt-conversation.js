'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const {createRequire} = require('node:module');
const {conversationBindings} = require('../tools/chatgpt-conversation');
const {freshReady, requestFreshChat} = require('../tools/chatgpt-fresh-chat');

const checks = {}, root = path.resolve(__dirname, '..');
const primary = role => `[data-message-author-role="${role}"]`;
const secondary = role => `article[data-turn="${role}"]`;
const fallback = role => role === 'user' ? '.bg-user-message' : '[class*="DilResponseRoot"]';
const rect = {top: 20, left: 10, width: 300, height: 40};
function element(text = '', options = {}) {
  const node = {
    isConnected: true, innerText: text, parentElement: null, tagName: 'DIV',
    style: {display: 'block', visibility: 'visible'}, attrs: {}, rects: [rect],
    getAttribute(name) { return this.attrs[name] ?? null; },
    hasAttribute(name) { return Object.hasOwn(this.attrs, name); },
    getClientRects() { return this.rects; },
    closest(selector) { return this.selectors?.includes(selector) ? this : this.parentElement?.closest(selector); },
    ...options
  };
  return node;
}
function page(families = {}) {
  const editor = element('', {tagName: 'TEXTAREA', value: '', getBoundingClientRect: () => rect,
    focus() { document.activeElement = this; }, contains(other) { return this === other; },
    querySelectorAll: () => [], dispatchEvent() { this.events = (this.events || 0) + 1; }});
  const document = {
    querySelectorAll: selector => selector === '[contenteditable="true"],textarea' ? [editor] : families[selector] || [],
    querySelector: selector => ['.ProseMirror', '#prompt-textarea', 'div[contenteditable="true"]'].includes(selector) ? editor : null,
    // Turn extraction must never depend on hit testing or viewport membership.
    elementFromPoint() { throw Error('TURN_HIT_TEST_FORBIDDEN'); }
  };
  class TextArea {}
  Object.defineProperty(TextArea.prototype, 'value', {set(value) { this.value = value; this.innerText = value; }});
  const context = vm.createContext({document, location: {href: 'https://chatgpt.com/'},
    getComputedStyle: node => node.style, HTMLTextAreaElement: TextArea, Event: class {}});
  const evaluate = expression => vm.runInContext(expression, context, {timeout: 1000});
  const snapshot = () => evaluate(`(() => {${conversationBindings()} return readConversationSnapshot();})()`);
  const turns = role => evaluate(`(() => {${conversationBindings()} return conversationTurns(${JSON.stringify(role)}).length;})()`);
  return {editor, snapshot, turns, evaluate};
}
function counts(fixture, users, assistants) {
  const s = fixture.snapshot(); assert.equal(s.user, users); assert.equal(s.assistant, assistants); return s;
}
const hidden = text => element(text, {rects: []});

// Compile the real bridge functions in an isolated test module. Only the CDP
// transport/profile probe are replaced; no browser, ledger, or input is touched.
function bridgeFor(fixture) {
  const filename = path.join(root, 'tools/chatgpt-bridge.js');
  const context = vm.createContext({require: createRequire(filename), module: {exports: {}}, __dirname: path.dirname(filename),
    process: {argv: ['node', filename], once() {}}, Buffer, URL, setTimeout, clearTimeout});
  vm.runInContext(fs.readFileSync(filename, 'utf8') + `
    verifyDedicatedProfile = () => ({profile_match: true});
    sendCdp = async (ws, method, params) => {
      if (method !== 'Runtime.evaluate') throw Error('NO_INPUT_ALLOWED');
      return {result: {value: __evaluate(params.expression)}};
    };
    module.exports.test = {readConversation, clearOwnedComposer};`, context, {timeout: 1000});
  context.__evaluate = fixture.evaluate;
  return context.module.exports.test;
}

(async () => {
  const a = page({[primary('user')]: [hidden('old user')], [primary('assistant')]: [hidden('old assistant')]});
  const empty = counts(a, 0, 0); assert.equal(empty.lastUserText, ''); assert.equal(empty.lastAssistantText, '');
  checks.A_hidden_retained_zero_rects = 'PASS';

  const b = page({[primary('user')]: [element('You said: Actual ñ'), hidden('old later node')]});
  assert.equal(counts(b, 1, 0).lastUserText, 'Actual ñ'); checks.B_last_text_only_rendered = 'PASS';

  for (const role of ['user', 'assistant']) {
    const c2 = page({[primary(role)]: [hidden('old')], [secondary(role)]: [element('live article')]});
    assert.equal(c2.turns(role), 1);
    const outer = element('live fallback', {selectors: [fallback(role)]});
    const nested = element('nested duplicate', {parentElement: outer, selectors: [fallback(role)]});
    const c3 = page({[primary(role)]: [hidden('old')], [secondary(role)]: [hidden('old article')],
      [fallback(role)]: [outer, nested, hidden('hidden fallback')]});
    assert.equal(c3.turns(role), 1);
  }
  checks.C_filter_every_family_before_fallback_and_deduplicate = 'PASS';

  for (const top of [-2000, 20000]) {
    const d = page({[primary('user')]: [element('offscreen', {rects: [{...rect, top}]})]});
    counts(d, 1, 0);
  }
  checks.D_offscreen_rendered_turns_preserved = 'PASS';
  for (const [name, style] of [['E_display_none', {display: 'none', visibility: 'visible'}],
    ['F_visibility_hidden', {display: 'block', visibility: 'hidden'}],
    ['F_visibility_collapse', {display: 'block', visibility: 'collapse'}]]) {
    for (const ancestor of [false, true]) {
      const blocked = element('blocked', {style});
      const node = ancestor ? element('descendant', {parentElement: blocked}) : blocked;
      counts(page({[primary('user')]: [node]}), 0, 0);
    }
    checks[name] = 'PASS';
  }
  for (const [name, attrs] of [['G_aria_hidden', {'aria-hidden': 'true'}], ['H_hidden', {hidden: ''}], ['H_inert', {inert: ''}]]) {
    for (const ancestor of [false, true]) {
      const blocked = element('blocked', {attrs});
      const node = ancestor ? element('descendant', {parentElement: blocked}) : blocked;
      counts(page({[primary('user')]: [node]}), 0, 0);
    }
    checks[name] = 'PASS';
  }
  for (const options of [{isConnected: false}, {rects: [{width: 0, height: 40}]}, {rects: [{width: 40, height: 0}]}])
    counts(page({[primary('user')]: [element('invalid', options)]}), 0, 0);
  checks.detached_and_zero_area_excluded = 'PASS';
  counts(page({[primary('user')]: [element('multiple rects', {rects: [{width: 0, height: 0}, rect]})]}), 1, 0);
  checks.any_positive_area_rect_counts = 'PASS';

  for (const baseline of [0, 1]) {
    const i = page({[primary('user')]: [hidden('old')], [primary('assistant')]: [hidden('old')],
      [secondary('user')]: baseline ? [element('user')] : [], [secondary('assistant')]: baseline ? [element('assistant')] : []});
    i.editor.value = i.editor.innerText = 'Owned draft áéíóú ñ';
    const bridge = bridgeFor(i), observed = await bridge.readConversation(null);
    assert.equal(observed.user, baseline); assert.equal(observed.assistant, baseline);
    await bridge.clearOwnedComposer(null, {...observed, composer: i.editor.value}, {user_turns_before: baseline, assistant_turns_before: baseline});
    assert.equal(i.editor.value, ''); assert.equal(i.editor.events, 1);
  }
  const mismatch = page({[primary('user')]: [element('new turn')]});
  mismatch.editor.value = mismatch.editor.innerText = 'owned';
  await assert.rejects(bridgeFor(mismatch).clearOwnedComposer(null, {url: 'https://chatgpt.com/', composer: 'owned'},
    {user_turns_before: 0, assistant_turns_before: 0}), /ROLLBACK_BASELINE_CHANGED/);
  assert.equal(mismatch.editor.value, 'owned');
  checks.I_real_bridge_read_and_rollback_share_extractor = 'PASS';
  checks.I_real_baseline_change_still_denied = 'PASS';

  const j = page({[primary('user')]: [element('You said: Pregunta ñ')], [primary('assistant')]: [element('ChatGPT said: Respuesta á')]});
  const normal = counts(j, 1, 1); assert.equal(normal.lastUserText, 'Pregunta ñ'); assert.equal(normal.lastAssistantText, 'Respuesta á');
  const actual = await bridgeFor(j).readConversation(null);
  assert.equal(actual.lastUserText, normal.lastUserText); assert.equal(actual.lastAssistantText, normal.lastAssistantText);
  checks.J_normal_one_each_texts_unchanged = 'PASS';
  assert(freshReady({...empty, composer_found: true, composer_matches: 1, editable: true, composer: '', focused: true}));
  checks.FRESH_CHAT_READY_with_only_hidden_retained_turns = 'PASS';
  let focused = false, focuses = 0;
  const ready = await requestFreshChat({
    inspect: async () => ({...a.snapshot(), composer_found: true, composer_matches: 1, editable: true, composer: '', focused, buttons: []}),
    findControl: async () => {throw Error('EMPTY_ROOT_MUST_NOT_NAVIGATE');},
    clickNavigation: async () => {throw Error('EMPTY_ROOT_MUST_NOT_CLICK');},
    focusEmpty: async () => {focuses++; focused = true;}, sleep: async () => {}
  });
  assert.equal(ready.FRESH_CHAT_READY, true); assert.equal(focuses, 1);
  assert.equal(freshReady({...empty, composer_found: true, composer_matches: 1, editable: true, composer: '', focused: false, buttons: []}), false);
  checks.FRESH_CHAT_READY_production_transition_simulated_only = 'PASS';
  checks.FRESH_CHAT_focus_or_control_guard_unchanged = 'PASS';
  const result = {status: 'PASS', checks, browser_access: false, real_sends: 0, ledger_access: false};
  if (process.env.F24_PREFLIGHT_E) fs.writeFileSync(path.join(process.env.F24_PREFLIGHT_E, 'conversation-deterministic.json'), JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result, null, 2));
})().catch(error => {console.error(error); process.exitCode = 1;});
