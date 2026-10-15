'use strict';
const assert=require('assert/strict'),fs=require('fs'),path=require('path'),crypto=require('crypto');
const {ConsultationLedger,hash}=require('../tools/chatgpt-ledger');
const {Budget,Trace,budgets,deliver,sentProof}=require('../tools/chatgpt-delivery');
const root=path.resolve(__dirname,'..'),directory=path.join(root,'sandbox','delivery-'+crypto.randomUUID());
const ledger=new ConsultationLedger(directory),checks={};
const prompt='Prueba UTF-8: áéíóú ñ ¿Dónde? — € °';
const url='https://chatgpt.com/c/deterministic-sandbox';
async function scenario(id,kind){
  let t=0,clicks=0;const clock=()=>t,budget=new Budget(4,clock),trace=new Trace(path.join(directory,id+'.trace.jsonl'),id,clock);
  ledger.reserve(id,prompt);ledger.update(id,{user_turns_before:2,assistant_turns_before:2,conversation_url:url});
  ledger.update(id,{delivery_state:'PREPARED'});
  const probe=async()=>({url,user:kind==='no-turn'?2:3,assistant:kind==='fast'||kind==='slow'&&t>=1500?3:2,lastUserText:prompt,lastAssistantText:'Respuesta ñ',isStreaming:kind==='pending',composer:kind==='no-turn'?prompt:''});
  const result=await deliver({ledger,id,baseline:{user:2,assistant:2},click:async()=>{clicks++;trace.emit('MOUSE_PRESSED_START');trace.emit('MOUSE_PRESSED_END');trace.emit('MOUSE_RELEASED_START');trace.emit('MOUSE_RELEASED_END');},probe,budget,trace,sleep:async ms=>{t+=ms;}});
  return {result,clicks,trace:fs.readFileSync(trace.filename,'utf8')};
}
(async()=>{try{
  const fast=await scenario('fast','fast');assert.equal(fast.result.status,'SUCCESS');assert(ledger.read('fast').history.some(e=>e.to==='SENT_CONFIRMED'));checks.fast_sent_confirmed='PASS';
  const slow=await scenario('slow','slow');assert.equal(slow.result.status,'SUCCESS');assert.equal(slow.clicks,1);checks.slow_response_no_second_send='PASS';
  const pending=await scenario('pending','pending');assert.equal(pending.result.status,'SENT_CONFIRMED');assert.equal(ledger.read('pending').delivery_state,'SENT_CONFIRMED');assert.equal(ledger.result('pending').status,'ALREADY_SENT');assert.equal(ledger.result('pending').response_state,'PENDING');
  assert.throws(()=>ledger.update('pending',{delivery_state:'UNKNOWN_DELIVERY'}),/SENT_IS_IRREVERSIBLE/);assert.throws(()=>ledger.update('pending',{delivery_state:'DELIVERY_INTENT',send_attempts:2}),/SENT_IS_IRREVERSIBLE/);assert.throws(()=>ledger.update('pending',{message_confirmed:false}),/SENT_IS_IRREVERSIBLE/);checks.response_timeout_irreversible_no_resend='PASS';
  const none=await scenario('none','no-turn');assert.equal(none.result.status,'UNKNOWN_DELIVERY');assert.equal(none.clicks,1);assert.equal(ledger.result('none').no_resend,true);checks.click_without_turn_unknown='PASS';
  const r=ledger.read('fast');assert(!sentProof(r,{url:'https://chatgpt.com/c/wrong',user:3,lastUserText:prompt}));assert(!sentProof(r,{url,user:3,lastUserText:'wrong'}));assert(!sentProof(r,{url,user:2,lastUserText:prompt,composer:''}));checks.identity_sha_and_turn_required='PASS';
  for(const sec of [1,2,45,60,300]){const b=budgets(sec);assert(b.parent_ms>b.internal_ms+b.cleanup_margin_ms);assert.equal(b.internal_ms,Object.values(b.stages).reduce((a,v)=>a+v,0));}checks.parent_budget_proven='PASS';
  const records=fast.trace.trim().split('\n').map(JSON.parse);assert(records.some(r=>r.event==='FIRST_POST_CLICK_PROBE'));assert(records.some(r=>r.event==='RESPONSE_CAPTURED'));assert(records.every((r,i)=>!i||r.mono_ms>=records[i-1].mono_ms));assert(!fast.trace.includes(prompt));checks.monotonic_trace_no_prompt='PASS';
  assert.equal(hash(Buffer.from(prompt,'utf8').toString('utf8')),hash(prompt));checks.utf8='PASS';
  console.log(JSON.stringify({status:'PASS',checks,browser_access:false,real_messages:0},null,2));
}finally{assert(directory.startsWith(path.join(root,'sandbox')+path.sep));fs.rmSync(directory,{recursive:true});}})().catch(e=>{console.error(e);process.exitCode=1;});
