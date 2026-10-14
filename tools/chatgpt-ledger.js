'use strict';
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const ROOT = path.resolve(__dirname, '..');
const hash = text => crypto.createHash('sha256').update(text, 'utf8').digest('hex');
function normalize(text) { return text.trim().replace(/\r\n/g, '\n').replace(/\n\n+/g, '\n'); }
// Human-only checks. Automatic reconciliation must never infer non-delivery.
function humanConversation(url) {
  try {
    const parsed = new URL(url);
    if (parsed.origin !== 'https://chatgpt.com' || parsed.username || parsed.password) return undefined;
    if (parsed.pathname === '/') return null; // New conversation, only with a 0/0 baseline.
    return /^\/c\/([A-Za-z0-9-]{1,120})\/?$/.exec(parsed.pathname)?.[1];
  } catch { return undefined; }
}
// Old history entries omit changed fields. Provenance must be audited separately
// and bound to the exact ledger in the explicit human receipt; this is only a
// consistency check and cannot authorize a retry on its own.
function humanHistoryConsistent(record) {
  if (![record.user_turns_before, record.assistant_turns_before].every(n => Number.isSafeInteger(n) && n >= 0) ||
      !Array.isArray(record.history)) return false;
  let state = 'RESERVED', attempts = 0, baselineWrite = false, intent = false;
  let previousTime = Date.parse(record.created_at);
  if (!Number.isFinite(previousTime)) return false;
  for (const event of record.history) {
    if (!event || event.from !== state || !Number.isFinite(Date.parse(event.at)) || Date.parse(event.at) < previousTime) return false;
    if (event.to === 'RESERVED' && !intent && event.send_attempts === 0) baselineWrite = true;
    else if (event.to === 'DELIVERY_INTENT' && baselineWrite && !intent && event.send_attempts === 1) intent = true;
    else if (!(event.to === 'UNKNOWN_DELIVERY' && intent && event.send_attempts === 1)) return false;
    state = event.to; attempts = event.send_attempts; previousTime = Date.parse(event.at);
  }
  return baselineWrite && intent && state === record.delivery_state && attempts === record.send_attempts;
}
function directoryChecked(directory) {
  const target = path.resolve(directory);
  const allowed = ['runtime', 'sandbox'].some(name => {
    const rel = path.relative(path.join(ROOT, name), target);
    return !rel.startsWith('..') && !path.isAbsolute(rel);
  });
  if (!allowed) throw new Error('LEDGER_PATH_DENIED');
  let current = target;
  while (current !== path.dirname(current)) {
    if (fs.existsSync(current) && fs.lstatSync(current).isSymbolicLink()) throw new Error('LEDGER_REPARSE_POINT_DENIED');
    current = path.dirname(current);
  }
  fs.mkdirSync(target, { recursive: true });
  return target;
}
class ConsultationLedger {
  constructor(directory = path.join(ROOT, 'runtime', 'chatgpt-consultations')) { this.directory = directoryChecked(directory); }
  file(id) {
    if (!/^[A-Za-z0-9_.-]{1,120}$/.test(id)) throw new Error('INVALID_CONSULTATION_ID');
    return path.join(this.directory, hash(id) + '.json');
  }
  read(id) {
    const filename = this.file(id);
    if (!fs.existsSync(filename)) return null;
    if (fs.lstatSync(filename).isSymbolicLink()) throw new Error('LEDGER_REPARSE_POINT_DENIED');
    try { return JSON.parse(fs.readFileSync(filename, 'utf8')); }
    catch { return { consultation_id: id, delivery_state: 'UNKNOWN_DELIVERY' }; }
  }
  reserve(id, prompt) {
    const filename = this.file(id);
    let fd;
    try { fd = fs.openSync(filename, 'wx', 0o600); }
    catch (error) { if (error.code === 'EEXIST') return false; throw error; }
    try {
      const record = { schema_version: '1.0', consultation_id: id, prompt_sha256: hash(normalize(prompt)), delivery_state: 'RESERVED', created_at: new Date().toISOString(), pid: process.pid, send_attempts: 0 };
      fs.writeFileSync(fd, JSON.stringify(record, null, 2)); fs.fsyncSync(fd);
    } finally { fs.closeSync(fd); }
    return true;
  }
  update(id, fields) {
    const record = this.read(id);
    if (!record) throw new Error('CONSULTATION_NOT_RESERVED');
    if (record.message_confirmed && (fields.message_confirmed === false ||
        ['UNKNOWN_DELIVERY','DELIVERY_INTENT','NOT_DELIVERED_CONFIRMED','RESERVED'].includes(fields.delivery_state))) throw new Error('SENT_IS_IRREVERSIBLE_NO_RESEND');
    const approvedRetry = fields.delivery_state === 'DELIVERY_INTENT' && record.delivery_state === 'NOT_DELIVERED_CONFIRMED' && record.human_retry_remaining === 1;
    if (approvedRetry && fields.send_attempts !== record.send_attempts + 1) throw new Error('RETRY_COUNTER_REQUIRED');
    if (fields.delivery_state === 'DELIVERY_INTENT' && record.send_attempts >= 1 && !approvedRetry) throw new Error('ALREADY_ATTEMPTED_NO_RESEND');
    if (fields.send_attempts > 1 && !(approvedRetry && fields.send_attempts === record.send_attempts + 1 && fields.send_attempts === 2)) throw new Error('SECOND_SEND_DENIED');
    if (Object.keys(fields).some(key => key.startsWith('human_'))) throw new Error('HUMAN_RECONCILIATION_METHOD_REQUIRED');
    if (approvedRetry) fields = { ...fields, human_retry_remaining: 0, human_retry_consumed: true };
    const next = { ...record, ...fields };
    if (next.delivery_state === 'SENT_CONFIRMED' && !(next.message_confirmed && next.send_attempts >= 1 &&
        Number.isInteger(next.user_turns_before) && next.user_turns_after === next.user_turns_before + 1)) throw new Error('SENT_PROOF_REQUIRED');
    if (['COMPLETED', 'COMPLETED_RECONCILED'].includes(next.delivery_state) &&
        !((next.send_attempts === 1 || (next.send_attempts === 2 && next.human_retry_consumed)) && next.message_confirmed && Number.isInteger(next.user_turns_before) &&
          next.user_turns_after === next.user_turns_before + 1 && Number.isInteger(next.assistant_turns_before) &&
          next.assistant_turns_after === next.assistant_turns_before + 1)) throw new Error('TURN_GATED_COMPLETION_DENIED');
    next.history = [...(record.history || []), { at: new Date().toISOString(), from: record.delivery_state, to: next.delivery_state, send_attempts: next.send_attempts }];
    this.#write(id, next);
  }
  #write(id, record) {
    const filename = this.file(id);
    const temporary = filename + '.' + process.pid + '.' + crypto.randomUUID() + '.tmp';
    const fd = fs.openSync(temporary, 'wx', 0o600);
    try { fs.writeFileSync(fd, JSON.stringify({ ...record, updated_at: new Date().toISOString() }, null, 2)); fs.fsyncSync(fd); }
    finally { fs.closeSync(fd); }
    fs.renameSync(temporary, filename);
  }
  confirmNotDelivered(id, receipt, observation, receiptHash) {
    const record = this.read(id);
    if (!record || record.message_confirmed || record.human_retry_consumed || record.human_retry_remaining || !['UNKNOWN_DELIVERY','DELIVERY_INTENT'].includes(record.delivery_state)) throw new Error('HUMAN_RECONCILIATION_STATE_DENIED');
    if (record.schema_version !== '1.0' || record.consultation_id !== id || !/^[a-f0-9]{64}$/.test(record.prompt_sha256 || '') ||
        record.send_attempts !== 1 || !humanHistoryConsistent(record) ||
        ['user_turns_after','assistant_turns_after','response_sha256','human_source','human_receipt_sha256'].some(key => Object.hasOwn(record, key))) throw new Error('HUMAN_LEDGER_INCONSISTENT');
    if (!receipt || receipt.source !== 'HUMAN_VISUAL_RECONCILIATION' || receipt.resolution !== 'DELIVERY_NOT_OCCURRED' ||
        receipt.consultation_id !== id || receipt.prompt_sha256 !== record.prompt_sha256 || receipt.authorized_additional_physical_attempts !== 1 ||
        receipt.baseline_user_turns !== record.user_turns_before || receipt.baseline_assistant_turns !== record.assistant_turns_before ||
        receipt.baseline_proven !== true || !/^[a-f0-9]{64}$/.test(receipt.baseline_proof_sha256 || '') ||
        receipt.baseline_proof_ledger_sha256 !== receipt.ledger_sha256 ||
        receipt.ledger_sha256 !== hash(fs.readFileSync(this.file(id), 'utf8')) || !/^[a-f0-9]{64}$/.test(receiptHash || '')) throw new Error('HUMAN_RECEIPT_INVALID');
    const conversationId = humanConversation(record.conversation_url);
    if (!observation || conversationId === undefined ||
        (conversationId === null && (record.user_turns_before !== 0 || record.assistant_turns_before !== 0)) ||
        receipt.conversation_id !== conversationId || humanConversation(receipt.conversation_url) !== conversationId ||
        humanConversation(observation.url) !== conversationId) throw new Error('HUMAN_CONVERSATION_MISMATCH');
    if (observation.user !== record.user_turns_before || observation.assistant !== record.assistant_turns_before ||
        observation.isStreaming !== false || typeof observation.composer !== 'string' ||
        Buffer.from(observation.composer, 'utf8').toString('utf8') !== observation.composer ||
        hash(normalize(observation.composer)) !== record.prompt_sha256 || observation.sendAvailable !== true) throw new Error('NOT_DELIVERED_OBSERVATION_MISMATCH');
    this.#write(id, { ...record, delivery_state: 'NOT_DELIVERED_CONFIRMED', human_retry_remaining: 1,
      human_receipt_sha256: receiptHash, human_source: receipt.source, human_conversation_id: conversationId,
      human_baseline_proof_sha256: receipt.baseline_proof_sha256,
      history: [...(record.history || []), { at:new Date().toISOString(), from:record.delivery_state, logical_previous:'UNKNOWN_DELIVERY', to:'NOT_DELIVERED_CONFIRMED', source:receipt.source, receipt_sha256:receiptHash, send_attempts:record.send_attempts }] });
  }
  result(id) {
    const record = this.read(id);
    if (!record) return { status: 'NOT_SEEN', consultation_id: id };
    const responseKnown = ['COMPLETED', 'COMPLETED_RECONCILED'].includes(record.delivery_state);
    const known = responseKnown || (!!record.message_confirmed && ['SENT','SENT_CONFIRMED','UNKNOWN_DELIVERY'].includes(record.delivery_state));
    const retrySafe = record.delivery_state === 'NOT_DELIVERED_CONFIRMED' && record.human_retry_remaining === 1;
    return { status: known ? 'ALREADY_SENT' : retrySafe ? 'RETRY_SAFE' : 'UNKNOWN_DELIVERY', consultation_id: id, no_resend: !retrySafe, deduplicated: true, previous_delivery_state: record.delivery_state, message_sent: !!record.message_confirmed, send_attempts: record.send_attempts, response_received: responseKnown, response_state: responseKnown ? 'CAPTURED' : known ? 'PENDING' : 'UNKNOWN', user_turns_before: record.user_turns_before, user_turns_after: record.user_turns_after, assistant_turns_before: record.assistant_turns_before, assistant_turns_after: record.assistant_turns_after };
  }
}
function acquireBrowserLease(directory = path.join(ROOT, 'runtime', 'chatgpt-consultations')) {
  directoryChecked(directory);
  const filename = path.join(directory, 'browser-lease.json');
  if (fs.existsSync(filename)) {
    if (fs.lstatSync(filename).isSymbolicLink()) throw new Error('LEDGER_REPARSE_POINT_DENIED');
    let old;
    try { old = JSON.parse(fs.readFileSync(filename, 'utf8')); } catch { throw new Error('BRIDGE_BUSY_UNKNOWN_OWNER'); }
    try { process.kill(old.pid, 0); throw new Error('BRIDGE_BUSY'); }
    catch (error) { if (error.code !== 'ESRCH') throw error; }
    fs.unlinkSync(filename);
  }
  const nonce = crypto.randomUUID();
  const fd = fs.openSync(filename, 'wx', 0o600);
  try { fs.writeFileSync(fd, JSON.stringify({ pid: process.pid, nonce })); fs.fsyncSync(fd); }
  finally { fs.closeSync(fd); }
  const release = () => {
    try { if (JSON.parse(fs.readFileSync(filename, 'utf8')).nonce === nonce) fs.unlinkSync(filename); } catch {}
  };
  process.once('exit', release);
  return release;
}
function reconcileObservation(record, observation) {
  const userMatch = record.prompt_sha256 === hash(normalize(observation.lastUserText || ''));
  const countsMatch = observation.user === record.user_turns_before + 1 && observation.assistant === record.assistant_turns_before + 1;
  return userMatch && countsMatch && !observation.isStreaming;
}
module.exports = { ConsultationLedger, acquireBrowserLease, hash, normalize, reconcileObservation };
