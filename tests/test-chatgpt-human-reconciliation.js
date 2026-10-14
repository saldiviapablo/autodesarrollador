'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { spawnSync } = require('node:child_process');
const { ConsultationLedger, hash, normalize, reconcileObservation } = require('../tools/chatgpt-ledger');
const ROOT = path.resolve(__dirname, '..');
const directory = path.join(ROOT, 'sandbox', 'human-reconciliation-' + crypto.randomUUID());
const ledger = new ConsultationLedger(directory);
const evidenceDirectory = path.resolve(ROOT, process.env.CHATGPT_TEST_EVIDENCE_DIR || 'evidence/f24-human-baseline-reconciliation-20261014');
const prompt = 'Consulta UTF-8: áéíóú ñ ¿Dónde? — € °';
const conversationUrl = 'https://chatgpt.com/c/6acefadc-36b8-83e8-9172-7e3e9421dc21';
const conversationId = '6acefadc-36b8-83e8-9172-7e3e9421dc21';
const checks = {};
let sequence = 0;
function fixture(baseline = 1, newConversation = false) {
  const id = 'human-test-' + sequence++;
  ledger.reserve(id, prompt);
  const url = newConversation ? 'https://chatgpt.com/' : conversationUrl;
  ledger.update(id, { user_turns_before: baseline, assistant_turns_before: baseline, conversation_url: url });
  const baselineSnapshot = ledger.read(id);
  ledger.update(id, { delivery_state: 'DELIVERY_INTENT', send_attempts: 1 });
  const receipt = { source: 'HUMAN_VISUAL_RECONCILIATION', resolution: 'DELIVERY_NOT_OCCURRED', consultation_id: id,
    prompt_sha256: hash(normalize(prompt)), authorized_additional_physical_attempts: 1,
    baseline_user_turns: baseline, baseline_assistant_turns: baseline,
    conversation_url: url, conversation_id: newConversation ? null : conversationId,
    ledger_sha256: hash(fs.readFileSync(ledger.file(id), 'utf8')), baseline_proven: true,
    baseline_proof_sha256: hash(JSON.stringify(baselineSnapshot)) };
  receipt.baseline_proof_ledger_sha256 = receipt.ledger_sha256;
  return { id, receipt, observation: { user: baseline, assistant: baseline, composer: prompt,
    isStreaming: false, sendAvailable: true, url } };
}
function confirm(test) {
  ledger.confirmNotDelivered(test.id, test.receipt, test.observation, hash(JSON.stringify(test.receipt)));
}
function alterRecord(test, fields) {
  fs.writeFileSync(ledger.file(test.id), JSON.stringify({ ...ledger.read(test.id), ...fields }));
  test.receipt.ledger_sha256 = hash(fs.readFileSync(ledger.file(test.id), 'utf8'));
  test.receipt.baseline_proof_ledger_sha256 = test.receipt.ledger_sha256;
}
function deny(name, change) {
  const test = fixture();
  change(test);
  const before = fs.readFileSync(ledger.file(test.id));
  assert.throws(() => confirm(test), /HUMAN_|NOT_DELIVERED_/);
  assert.deepEqual(fs.readFileSync(ledger.file(test.id)), before, 'Denied reconciliation must not change ledger');
  assert.equal(ledger.result(test.id).status, 'UNKNOWN_DELIVERY');
  assert.equal(ledger.result(test.id).no_resend, true);
  assert.throws(() => ledger.update(test.id, { delivery_state: 'DELIVERY_INTENT', send_attempts: 2 }), /NO_RESEND/);
  checks[name] = 'DENY / PASS';
}
try {
  for (const [baseline, newConversation] of [[0, true], [1, false], [5, false]]) {
    const test = fixture(baseline, newConversation);
    const previousHistory = ledger.read(test.id).history;
    confirm(test);
    assert.equal(ledger.result(test.id).status, 'RETRY_SAFE');
    assert.equal(ledger.read(test.id).delivery_state, 'NOT_DELIVERED_CONFIRMED');
    assert.equal(ledger.read(test.id).send_attempts, 1);
    assert.deepEqual(ledger.read(test.id).history.slice(0, previousHistory.length), previousHistory);
    assert.equal(ledger.read(test.id).human_conversation_id, newConversation ? null : conversationId);
    checks['baseline_' + baseline + '_' + baseline] = 'ALLOW / PASS';
  }
  deny('current_2_1_vs_1_1', t => { t.observation.user = 2; });
  deny('current_2_2_vs_1_1', t => { t.observation.user = 2; t.observation.assistant = 2; });
  deny('composer_hash_mismatch', t => { t.observation.composer += ' changed'; });
  deny('conversation_id_mismatch', t => { t.observation.url = 'https://chatgpt.com/c/different'; });
  deny('receipt_conversation_id_mismatch', t => { t.receipt.conversation_id = 'different'; });
  deny('receipt_conversation_url_mismatch', t => { t.receipt.conversation_url = 'https://chatgpt.com/c/different'; });
  deny('missing_human_confirmation', t => { t.receipt.source = 'AUTOMATIC_RECONCILIATION'; });
  deny('no_human_receipt', t => { t.receipt = null; });
  deny('retry_already_consumed', t => alterRecord(t, { human_retry_consumed: true }));
  deny('consultation_id_mismatch', t => { t.receipt.consultation_id = 'different'; });
  deny('ledger_id_mismatch', t => alterRecord(t, { consultation_id: 'different' }));
  deny('receipt_prompt_hash_mismatch', t => { t.receipt.prompt_sha256 = '0'.repeat(64); });
  deny('receipt_baseline_mismatch', t => { t.receipt.baseline_user_turns = 0; });
  deny('receipt_ledger_hash_mismatch', t => { t.receipt.ledger_sha256 = '0'.repeat(64); });
  deny('baseline_not_proven_by_human_audit', t => { delete t.receipt.baseline_proven; });
  deny('baseline_proof_hash_missing', t => { delete t.receipt.baseline_proof_sha256; });
  deny('baseline_proof_bound_to_different_ledger', t => { t.receipt.baseline_proof_ledger_sha256 = '0'.repeat(64); });
  deny('marker_alone_is_not_baseline_proof', t => {
    const record = ledger.read(t.id);
    // An arbitrary pre-intent update marker cannot replace a baseline audit.
    record.history[0].note = 'unrelated update';
    alterRecord(t, { history: record.history });
    t.receipt.baseline_proven = false;
  });
  const lateBaselineId = 'late-baseline';
  ledger.reserve(lateBaselineId, prompt);
  ledger.update(lateBaselineId, { note: 'unrelated pre-intent update' });
  ledger.update(lateBaselineId, { delivery_state: 'DELIVERY_INTENT', send_attempts: 1,
    user_turns_before: 1, assistant_turns_before: 1, conversation_url: conversationUrl });
  const lateBaseline = fixture();
  Object.assign(lateBaseline.receipt, { consultation_id: lateBaselineId,
    ledger_sha256: hash(fs.readFileSync(ledger.file(lateBaselineId), 'utf8')), baseline_proven: false });
  lateBaseline.receipt.baseline_proof_ledger_sha256 = lateBaseline.receipt.ledger_sha256;
  lateBaseline.id = lateBaselineId;
  assert.throws(() => confirm(lateBaseline), /HUMAN_RECEIPT_INVALID/);
  assert.equal(ledger.result(lateBaselineId).no_resend, true);
  checks.baseline_added_at_intent_without_pre_attempt_audit = 'DENY / PASS';
  deny('missing_baseline', t => alterRecord(t, { user_turns_before: undefined }));
  deny('invalid_baseline', t => alterRecord(t, { assistant_turns_before: -1 }));
  deny('missing_pre_intent_baseline_write', t => alterRecord(t, { history: ledger.read(t.id).history.slice(1) }));
  deny('out_of_order_history', t => {
    const history = ledger.read(t.id).history;
    history[0].at = '2099-01-01T00:00:00.000Z';
    alterRecord(t, { history });
  });
  deny('history_sent_evidence', t => {
    const history = ledger.read(t.id).history;
    history.push({ at: new Date().toISOString(), from: 'DELIVERY_INTENT', to: 'SENT', send_attempts: 1 });
    alterRecord(t, { history });
  });
  deny('response_evidence', t => alterRecord(t, { response_sha256: hash('response') }));
  deny('turn_after_evidence', t => alterRecord(t, { user_turns_after: 2 }));
  deny('message_confirmed_evidence', t => alterRecord(t, { message_confirmed: true }));
  deny('streaming', t => { t.observation.isStreaming = true; });
  deny('missing_streaming_state', t => { delete t.observation.isStreaming; });
  deny('send_button_unavailable', t => { t.observation.sendAvailable = false; });
  deny('invalid_utf8', t => { t.observation.composer += '\ud800'; });
  deny('http_domain', t => { t.observation.url = conversationUrl.replace('https:', 'http:'); });
  deny('subdomain', t => { t.observation.url = conversationUrl.replace('chatgpt.com', 'foo.chatgpt.com'); });
  deny('missing_conversation_id_in_existing_chat', t => { t.observation.url = 'https://chatgpt.com/'; });
  const retry = fixture();
  confirm(retry);
  assert.throws(() => confirm(retry), /STATE_DENIED/);
  assert.throws(() => ledger.update(retry.id, { delivery_state: 'DELIVERY_INTENT' }), /RETRY_COUNTER_REQUIRED/);
  let simulatedPhysicalRetries = 0;
  ledger.update(retry.id, { delivery_state: 'DELIVERY_INTENT', send_attempts: 2 });
  simulatedPhysicalRetries++;
  assert.equal(ledger.read(retry.id).human_retry_remaining, 0);
  assert.equal(ledger.read(retry.id).human_retry_consumed, true);
  assert.throws(() => ledger.update(retry.id, { delivery_state: 'DELIVERY_INTENT', send_attempts: 3 }), /NO_RESEND/);
  ledger.update(retry.id, { delivery_state: 'UNKNOWN_DELIVERY' });
  assert.throws(() => confirm(retry), /STATE_DENIED/);
  assert.equal(simulatedPhysicalRetries, 1);
  assert.equal(ledger.result(retry.id).no_resend, true);
  checks.second_physical_retry_denied = 'DENY / PASS (simulation only, no browser)';
  const automatic = fixture();
  assert.equal(reconcileObservation(ledger.read(automatic.id), { ...automatic.observation, lastUserText: prompt }), false);
  assert.equal(ledger.result(automatic.id).status, 'UNKNOWN_DELIVERY');
  assert.equal(reconcileObservation(ledger.read(automatic.id), { user: 2, assistant: 2, lastUserText: prompt, isStreaming: false }), true);
  checks.automatic_equal_baseline_still_unknown = 'PASS';
  const original = spawnSync('git', ['show', '4e8ba72:tools/chatgpt-ledger.js'], { cwd: ROOT, encoding: 'utf8', windowsHide: true });
  assert.equal(original.status, 0);
  const oldAutomatic = original.stdout.replace(/\r\n/g, '\n').match(/function reconcileObservation[\s\S]*?(?=\nmodule.exports)/)[0].trim();
  assert.equal(reconcileObservation.toString(), oldAutomatic);
  checks.automatic_function_unchanged = 'PASS';
  const bridgeBefore = JSON.parse(fs.readFileSync(path.join(evidenceDirectory, 'integrity-before.json'), 'utf8')).protected['tools/chatgpt-bridge.js'];
  assert.equal(hash(fs.readFileSync(path.join(ROOT, 'tools/chatgpt-bridge.js'), 'utf8')), bridgeBefore);
  checks.automatic_bridge_and_all_send_paths_unchanged = 'PASS';
  const result = { status: 'PASS', checks, physical_send_count: 0, browser_access: false };
  fs.mkdirSync(evidenceDirectory, { recursive: true });
  fs.writeFileSync(path.join(evidenceDirectory, 'human-deterministic.json'), JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result, null, 2));
} finally {
  for (const name of fs.readdirSync(directory)) fs.unlinkSync(path.join(directory, name));
  fs.rmdirSync(directory);
}
