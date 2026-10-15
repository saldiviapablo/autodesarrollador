'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const {hash,normalize,hasIntent}=require('./chatgpt-ledger');
const {conversationId}=require('./chatgpt-delivery');
const LEGACY_ID='f24-a5-cfe02556f1f3490eb027139d8e5620ae';
const LEGACY_SHA='449d9d63fff353617d1d5f0f54ce75cf61186f1e8f2251586a8455a119ce056e';
function requireEmptyComposer(prose){if((prose.value??prose.innerText??'').trim())throw Error('UNICODE_ROUNDTRIP_COMPOSER_NOT_EMPTY');}
function traceSafe(rows,id){
 if(!Array.isArray(rows)||!rows.some(r=>r.event==='BRIDGE_START')||rows.some(r=>r.consultation_id!==id))return false;
 const allowed=/^(BRIDGE_START|FAILURE|CLEANUP|PREPARED|SEND_METHOD_SELECTED|REQUEST_FRESH_CHAT|FRESH_CHAT_READY|NEW_CHAT_NAVIGATION_START|NEW_CHAT_NAVIGATION_END|OWNED_DRAFT_ROLLBACK|PRE_SEND_INTERRUPTED)$/;
 return rows.every(r=>allowed.test(r.event)&&!r.method&&!r.type);
}
function baselineMatches(record,o){
 try{return o.profile_match===true&&o.composer_found===true&&o.composer_matches===1&&o.editable===true&&o.isStreaming===false&&Number.isSafeInteger(record.user_turns_before)&&record.user_turns_before>=0&&Number.isSafeInteger(record.assistant_turns_before)&&record.assistant_turns_before>=0&&o.user===record.user_turns_before&&o.assistant===record.assistant_turns_before&&conversationId(o.url)===conversationId(record.conversation_url);}catch{return false;}
}
function owned(record,o,rows,mode){
 if(!record||record.send_attempts!==0||record.message_confirmed||hasIntent(record)||!baselineMatches(record,o)||hash(normalize(o.composer||''))!==record.prompt_sha256||!traceSafe(rows,record.consultation_id))return false;
 if(record.schema_version==='1.0')return mode==='LEGACY_PRE_SEND_RECOVERY'&&record.consultation_id===LEGACY_ID&&record.prompt_sha256===LEGACY_SHA&&record.delivery_state==='UNKNOWN_DELIVERY';
 return record.schema_version==='2.0'&&['RESERVED','PREPARED','PRE_SEND_ABORTED','PRE_SEND_INTERRUPTED'].includes(record.delivery_state);
}
function traceRows(ledger,id){
 const p=ledger.file(id).replace(/\.json$/,'.trace.jsonl');
 if(!fs.existsSync(p)||fs.lstatSync(p).isSymbolicLink()||fs.statSync(p).size>2*1024*1024)throw Error('PRE_SEND_TRACE_UNAVAILABLE');
 return fs.readFileSync(p,'utf8').split('\n').filter(Boolean).map(JSON.parse);
}
function receiptWrite(ledger,receipt){
 const text=JSON.stringify(receipt,null,2),name='draft-recovery-'+crypto.randomUUID()+'.receipt.json';
 const p=path.join(ledger.directory,name),fd=fs.openSync(p,'wx',0o600);
 try{fs.writeSync(fd,text);fs.fsyncSync(fd);}finally{fs.closeSync(fd);}
 return {receipt_path:p,receipt_sha256:hash(text)};
}
async function recoverOwnedPreSendDraft({ledger,inspect,clearComposer,mode='OWNED_PRE_SEND_RECOVERY',id,sleep=ms=>new Promise(r=>setTimeout(r,ms))}){
 const before=await inspect();
 if(!normalize(before.composer||''))throw Error('RECOVERY_REQUIRES_NONEMPTY_COMPOSER');
 const matching=[];
 for(const name of fs.readdirSync(ledger.directory).filter(n=>/^[a-f0-9]{64}\.json$/.test(n))){
  const p=path.join(ledger.directory,name);if(fs.lstatSync(p).isSymbolicLink())throw Error('DRAFT_OWNER_REPARSE_DENIED');
  let r;try{r=JSON.parse(fs.readFileSync(p,'utf8'));}catch{continue;}
  if(r.prompt_sha256===hash(normalize(before.composer||''))){
   if(name!==hash(r.consultation_id)+'.json')throw Error('DRAFT_LEDGER_IDENTITY_DENIED');
   matching.push(r);
  }
 }
 if(matching.length===0)throw Error('DRAFT_UNKNOWN_OWNER');
 if(matching.length!==1)throw Error('DRAFT_OWNER_AMBIGUOUS');
 const record=matching[0],rows=traceRows(ledger,record.consultation_id);
 if(id&&record.consultation_id!==id)throw Error('PRE_SEND_ROLLBACK_UNSAFE');
 if(!owned(record,before,rows,mode))throw Error('PRE_SEND_ROLLBACK_UNSAFE');
 const ledgerBefore=hash(fs.readFileSync(ledger.file(record.consultation_id),'utf8'));
 // Reinspect immediately, including actual dedicated-profile verification.
 const immediate=await inspect();if(!owned(record,immediate,traceRows(ledger,record.consultation_id),mode))throw Error('PRE_SEND_ROLLBACK_UNSAFE');
 if(hash(fs.readFileSync(ledger.file(record.consultation_id),'utf8'))!==ledgerBefore)throw Error('PRE_SEND_LEDGER_CHANGED_NO_CLEAR');
 await clearComposer(immediate,record);
 const observations=[];
 for(let i=0;i<3;i++){
  if(i)await sleep(100);const o=await inspect();
  if(!baselineMatches(record,o)||typeof o.composer!=='string'||normalize(o.composer)!=='')throw Error('PRE_SEND_ROLLBACK_UNSAFE_AFTER_CLEAR');
  observations.push({user:o.user,assistant:o.assistant,composer_empty:true,streaming:false});
 }
 const receipt={status:'PASS',mode,consultation_id:record.consultation_id,prompt_sha256:record.prompt_sha256,conversation_id:conversationId(record.conversation_url),baseline_user:record.user_turns_before,baseline_assistant:record.assistant_turns_before,ledger_before_sha256:ledgerBefore,trace_sha256:hash(JSON.stringify(rows)),profile_verified:true,OWNED_DRAFT_ROLLBACK:'PASS',LEGACY_DRAFT_OWNER:mode==='LEGACY_PRE_SEND_RECOVERY'?'CONFIRMED':undefined,LEGACY_DRAFT_CLEARED:mode==='LEGACY_PRE_SEND_RECOVERY'?'PASS':undefined,observations,physical_sends:0,historical_ledger_modified:false};
 const saved=receiptWrite(ledger,receipt);
 if(record.schema_version==='2.0')ledger.update(record.consultation_id,{delivery_state:'PRE_SEND_ABORTED',draft_cleared:true,rollback_receipt_sha256:saved.receipt_sha256});
 else if(hash(fs.readFileSync(ledger.file(record.consultation_id),'utf8'))!==ledgerBefore)throw Error('HISTORICAL_LEDGER_CHANGED');
 return {...receipt,...saved};
}
module.exports={traceSafe,baselineMatches,owned,traceRows,recoverOwnedPreSendDraft,LEGACY_ID,requireEmptyComposer};
