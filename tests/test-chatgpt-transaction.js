'use strict';
const assert=require('assert/strict'),fs=require('fs'),path=require('path'),crypto=require('crypto'),{spawnSync}=require('child_process');
const {ConsultationLedger,hash,interruptedState}=require('../tools/chatgpt-ledger');
const {recoverOwnedPreSendDraft,owned,requireEmptyComposer,LEGACY_ID}=require('../tools/chatgpt-pre-send');
const {requestFreshChat}=require('../tools/chatgpt-fresh-chat');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'sandbox/transaction-'+crypto.randomUUID()),checks={},prompt='Prueba propia áéíóú ñ',url='https://chatgpt.com/';let n=0;
function fixture(){
 const ledger=new ConsultationLedger(path.join(dir,String(n++))),id='transaction-'+n;
 ledger.reserve(id,prompt);ledger.update(id,{user_turns_before:0,assistant_turns_before:0,conversation_url:url});ledger.update(id,{delivery_state:'PREPARED'});
 const trace=ledger.file(id).replace(/\.json$/,'.trace.jsonl');fs.writeFileSync(trace,JSON.stringify({event:'BRIDGE_START',consultation_id:id})+'\n'+JSON.stringify({event:'PREPARED',consultation_id:id})+'\n');
 let composer=prompt,clears=0;const obs=()=>({profile_match:true,url,user:0,assistant:0,isStreaming:false,composer_found:true,composer_matches:1,editable:true,focused:true,composer});
 return {ledger,id,trace,obs,get clears(){return clears;},get composer(){return composer;},clear:async()=>{clears++;composer='';}};
}
async function recover(f,extra={}){return recoverOwnedPreSendDraft({ledger:f.ledger,inspect:async()=>f.obs(),clearComposer:f.clear,sleep:async()=>{},...extra});}
async function deny(label,alter){const f=fixture();alter(f);await assert.rejects(recover(f));assert.equal(f.clears,0);assert.equal(f.composer,prompt);checks[label]='DENY / PASS';}
(async()=>{try{
 const a=fixture();let clicked=0;assert((await requestFreshChat({inspect:async()=>({...a.obs(),composer:''}),findControl:async()=>{throw Error('no button search on empty root');},clickNavigation:async()=>clicked++,sleep:async()=>{}})).FRESH_CHAT_READY);assert.equal(clicked,0);checks.A_root_empty_no_click='PASS';
 const b=fixture();assert.equal((await recover(b)).OWNED_DRAFT_ROLLBACK,'PASS');assert.equal(b.composer,'');assert.equal(b.ledger.read(b.id).delivery_state,'PRE_SEND_ABORTED');assert.equal(b.ledger.result(b.id).status,'RETRY_SAFE');checks.B_owned_draft_clear='PASS';
 await deny('C_unknown_owner',f=>fs.unlinkSync(f.ledger.file(f.id)));
 await deny('D_two_owners',f=>{f.ledger.reserve('second',prompt);});
 await deny('E_baseline_changed',f=>{const old=f.obs;f.obs=()=>({...old(),user:1});});
 await deny('F_trace_intent',f=>fs.appendFileSync(f.trace,JSON.stringify({event:'DELIVERY_INTENT',consultation_id:f.id})+'\n'));
 for(const event of ['MOUSE_PRESSED_START','ENTER_KEYDOWN_START'])await deny('G_'+event,f=>fs.appendFileSync(f.trace,JSON.stringify({event,consultation_id:f.id})+'\n'));
 for(const label of ['H_actuator_failure','I_encoding_failure_after_prepared']){const f=fixture();try{throw Error(label);}catch{await recover(f);}assert.equal(f.ledger.read(f.id).delivery_state,'PRE_SEND_ABORTED');assert.equal(f.ledger.read(f.id).send_attempts,0);checks[label]='PASS';}
 const j=fixture();const code=`const {ConsultationLedger,interruptedState}=require(${JSON.stringify(path.join(root,'tools/chatgpt-ledger'))});const l=new ConsultationLedger(${JSON.stringify(j.ledger.directory)});process.once('exit',()=>l.update(${JSON.stringify(j.id)},{delivery_state:interruptedState(l.read(${JSON.stringify(j.id)}))}));`;
 assert.equal(spawnSync(process.execPath,['-e',code],{windowsHide:true}).status,0);assert.equal(j.ledger.read(j.id).delivery_state,'PRE_SEND_INTERRUPTED');assert.notEqual(j.ledger.result(j.id).status,'UNKNOWN_DELIVERY');checks.J_process_exit_pre_send='PASS';await recover(j);assert.equal(j.ledger.result(j.id).status,'RETRY_SAFE');checks.K_next_process_recovery='PASS';
 await deny('L_post_intent_never_clear',f=>{f.ledger.update(f.id,{delivery_state:'DELIVERY_INTENT',send_attempts:1});f.ledger.update(f.id,{delivery_state:interruptedState(f.ledger.read(f.id))});assert.equal(f.ledger.result(f.id).status,'UNKNOWN_DELIVERY');});
 const m=fixture();m.ledger.update(m.id,{delivery_state:'DELIVERY_INTENT',send_attempts:1});m.ledger.update(m.id,{delivery_state:'SENT_CONFIRMED',message_confirmed:true,user_turns_after:1,response_state:'PENDING'});assert.equal(interruptedState(m.ledger.read(m.id)),'SENT_CONFIRMED');assert.equal(m.ledger.result(m.id).status,'ALREADY_SENT');assert.throws(()=>m.ledger.update(m.id,{delivery_state:'UNKNOWN_DELIVERY'}));checks.M_sent_timeout_no_resend='PASS';
 const prose={innerText:'existing draft'};assert.throws(()=>requireEmptyComposer(prose),/COMPOSER_NOT_EMPTY/);assert.equal(prose.innerText,'existing draft');checks.N_unicode_guard='PASS';
 const o=fixture(),record=o.ledger.read(o.id),legacy={...record,schema_version:'1.0',consultation_id:LEGACY_ID,delivery_state:'UNKNOWN_DELIVERY'};
 assert(!owned(legacy,o.obs(),[{event:'BRIDGE_START',consultation_id:LEGACY_ID}],'OWNED_PRE_SEND_RECOVERY'));
 const actualLegacy=JSON.parse(fs.readFileSync(path.join(root,'runtime/chatgpt-consultations',hash(LEGACY_ID)+'.json'),'utf8'));assert(actualLegacy.send_attempts===0&&actualLegacy.schema_version==='1.0');assert.equal(actualLegacy.prompt_sha256,'449d9d63fff353617d1d5f0f54ce75cf61186f1e8f2251586a8455a119ce056e');
 const plan=JSON.parse(fs.readFileSync(path.join(root,'evidence/phase-24-attempt-5-20261014/native/RUN-PLAN.json'),'utf8').replace(/^\uFEFF/,''));
 const actualPrompt=`CONSULTA TÉCNICA (ROL CONSULTOR ARQUITECTÓNICO):\nPropósito: Revisión técnica y segunda opinión arquitectónica\nPregunta: ${plan.consultation.question}\nContexto:\n\n\nPor favor proporciona:\n1. Causa probable\n2. Dos estrategias alternativas\n3. Riesgos técnicos asociados`;
 assert.equal(hash(actualPrompt.trim().replace(/\n\n+/g,'\n')),actualLegacy.prompt_sha256);
 const legacyObs={...o.obs(),composer:actualPrompt};const legacyRows=[{event:'BRIDGE_START',consultation_id:LEGACY_ID},{event:'FAILURE',consultation_id:LEGACY_ID},{event:'CLEANUP',consultation_id:LEGACY_ID}];assert(owned(actualLegacy,legacyObs,legacyRows,'LEGACY_PRE_SEND_RECOVERY'));assert(!owned(actualLegacy,legacyObs,legacyRows,'OWNED_PRE_SEND_RECOVERY'));checks.O_legacy_requires_explicit_mode='PASS';
 const inv=fixture();assert.throws(()=>inv.ledger.update(inv.id,{delivery_state:'UNKNOWN_DELIVERY'}),/ZERO_ATTEMPTS/);for(const f of [b,j,m,inv]){const r=f.ledger.read(f.id);assert(r.delivery_state!=='UNKNOWN_DELIVERY'||r.send_attempts>=1||r.historical_legacy_record===true);}checks.NEW_RECORD_WITH_ZERO_SEND_ATTEMPTS_CANNOT_BECOME_UNKNOWN_DELIVERY='PASS';
 const forged=fixture();forged.ledger.update(forged.id,{delivery_state:'PRE_SEND_ABORTED',draft_cleared:true,rollback_receipt_sha256:'0'.repeat(64)});assert.notEqual(forged.ledger.result(forged.id).status,'RETRY_SAFE');checks.forged_rollback_receipt_no_retry='PASS';
 const result={status:'PASS',checks,real_sends:0};const e=process.env.F24_PREFLIGHT_E||path.join(root,'evidence/f24-transaction-cert-20261014');fs.writeFileSync(path.join(e,'transaction-deterministic.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
}finally{fs.rmSync(dir,{recursive:true});}})().catch(e=>{console.error(e);process.exitCode=1;});
