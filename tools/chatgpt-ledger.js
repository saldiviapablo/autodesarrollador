'use strict';
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const ROOT = path.resolve(__dirname, '..');
const hash = text => crypto.createHash('sha256').update(text, 'utf8').digest('hex');
function normalize(text) { return text.trim().replace(/\r\n/g, '\n').replace(/\n\n+/g, '\n'); }
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
    if (fields.delivery_state === 'DELIVERY_INTENT' && record.send_attempts >= 1) throw new Error('ALREADY_ATTEMPTED_NO_RESEND');
    if (fields.send_attempts > 1) throw new Error('SECOND_SEND_DENIED');
    const next = { ...record, ...fields };
    if (['COMPLETED', 'COMPLETED_RECONCILED'].includes(next.delivery_state) &&
        !(next.send_attempts === 1 && next.message_confirmed && Number.isInteger(next.user_turns_before) &&
          next.user_turns_after === next.user_turns_before + 1 && Number.isInteger(next.assistant_turns_before) &&
          next.assistant_turns_after === next.assistant_turns_before + 1)) throw new Error('TURN_GATED_COMPLETION_DENIED');
    const filename = this.file(id);
    const temporary = filename + '.' + process.pid + '.' + crypto.randomUUID() + '.tmp';
    const fd = fs.openSync(temporary, 'wx', 0o600);
    try { fs.writeFileSync(fd, JSON.stringify({ ...record, ...fields, updated_at: new Date().toISOString() }, null, 2)); fs.fsyncSync(fd); }
    finally { fs.closeSync(fd); }
    fs.renameSync(temporary, filename);
  }
  result(id) {
    const record = this.read(id);
    if (!record) return { status: 'NOT_SEEN', consultation_id: id };
    const known = ['COMPLETED', 'COMPLETED_RECONCILED'].includes(record.delivery_state);
    return { status: known ? 'ALREADY_SENT' : 'UNKNOWN_DELIVERY', consultation_id: id, no_resend: true, deduplicated: true, previous_delivery_state: record.delivery_state, message_sent: !!record.message_confirmed, send_attempts: record.send_attempts, response_received: known, user_turns_before: record.user_turns_before, user_turns_after: record.user_turns_after, assistant_turns_before: record.assistant_turns_before, assistant_turns_after: record.assistant_turns_after };
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
