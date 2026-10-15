'use strict';
const assert=require('assert/strict'),fs=require('fs'),path=require('path'),crypto=require('crypto');
const {inspectComposer,selectActuator,sendPhysicalEnter}=require('../tools/chatgpt-send-actuator');
const {ConsultationLedger,hash}=require('../tools/chatgpt-ledger');
const {deliver,Budget,Trace}=require('../tools/chatgpt-delivery');
const {sendSinglePhysicalClick}=require('../tools/chatgpt-bridge');
const prompt='Prueba única: áéíóú ñ — € °',url='https://chatgpt.com/c/test-exact';
const directory=path.resolve(__dirname,'../sandbox/actuator-'+crypto.randomUUID()),ledger=new ConsultationLedger(directory),checks={};
// Minimal DOM fixture executes the production scope traversal, with native form
// association and unrelated global submit controls. No browser/network access.
function fixture(localCount,globalCount=0){
 const rect={x:1,y:1,width:20,height:20};
 const composer={id:'prompt-textarea',innerText:prompt,isContentEditable:true,tagName:'DIV',querySelectorAll:()=>[],getBoundingClientRect:()=>rect,contains:x=>x===composer};
 const buttons=Array.from({length:localCount},()=>({type:'submit',getAttribute:()=>null,getBoundingClientRect:()=>rect,contains:()=>true}));
 const scope={querySelectorAll:()=>buttons,contains:x=>x===composer};composer.closest=selector=>selector==='form,[role="form"]'?scope:null;composer.parentElement={closest:()=>null};
 global.location={href:url};global.getComputedStyle=()=>({visibility:'visible',display:'block'});
 global.document={activeElement:composer,querySelectorAll:selector=>selector==='[contenteditable="true"],textarea'?[composer]:[...buttons,...Array(globalCount).fill({})],querySelector:()=>null,elementFromPoint:()=>({})};
 return inspectComposer(prompt);
}
const record={delivery_state:'RESERVED',send_attempts:0,prompt_sha256:hash(prompt),conversation_url:url};
(async()=>{try{
 const one=fixture(1);assert.equal(selectActuator(record,one).method,'COMPOSER_SCOPED_SUBMIT');checks.A_local_submit='PASS';
 assert.equal(selectActuator(record,fixture(1,5)).method,'COMPOSER_SCOPED_SUBMIT');checks.B_global_buttons_ignored='PASS';
 assert.equal(selectActuator(record,fixture(0)).method,'COMPOSER_ENTER_KEY');checks.C_enter_without_submit='PASS';
 assert.equal(selectActuator(record,fixture(2)).method,'COMPOSER_ENTER_KEY');checks.D_ambiguous_local_enter='PASS';
 assert.throws(()=>selectActuator(record,{...one,composer:'wrong'}),/HASH/);checks.E_wrong_hash_deny='PASS';
 assert.throws(()=>selectActuator(record,{...one,url:'https://chatgpt.com/c/other'}),/CONVERSATION/);checks.F_wrong_conversation_deny='PASS';
 assert.throws(()=>selectActuator(record,{...one,isStreaming:true}),/STREAMING/);checks.G_streaming_deny='PASS';
 for(const prior of [{...record,delivery_state:'DELIVERY_INTENT',send_attempts:1},{...record,history:[{to:'DELIVERY_INTENT'}]}])assert.throws(()=>selectActuator(prior,fixture(0)),/PRIOR_INTENT/);
 assert.throws(()=>selectActuator(record,{...fixture(0),focused:false}),/FOCUS/);checks.H_prior_intent_no_fallback='PASS';
 for(const method of ['COMPOSER_SCOPED_SUBMIT','COMPOSER_ENTER_KEY']){
  const id=method;ledger.reserve(id,prompt);ledger.update(id,{user_turns_before:0,assistant_turns_before:0,conversation_url:url});
  ledger.update(id,{delivery_state:'PREPARED'});
  const calls=[];let t=0;const dispatch=async(_,name,params)=>{calls.push({name,params});throw Error('ambiguous transport');};
  await assert.rejects(deliver({ledger,id,baseline:{user:0,assistant:0},sendMethod:method,click:()=>method==='COMPOSER_SCOPED_SUBMIT'?sendSinglePhysicalClick(null,one.buttons[0],dispatch):sendPhysicalEnter(null,dispatch),probe:async()=>{throw Error('must not probe after transport rejection');},budget:new Budget(2,()=>t),trace:new Trace(path.join(directory,id+'.trace'),id)}),/ambiguous transport/);
  assert.equal(calls.length,1);assert.equal(ledger.read(id).send_method,method);assert.equal(ledger.read(id).send_attempts,1);assert.equal(ledger.read(id).physical_actions,1);
  assert.throws(()=>ledger.update(id,{send_method:method==='COMPOSER_ENTER_KEY'?'COMPOSER_SCOPED_SUBMIT':'COMPOSER_ENTER_KEY'}),/IMMUTABLE/);
  await assert.rejects(deliver({ledger,id,baseline:{user:0,assistant:0},sendMethod:method,click:async()=>calls.push('AGAIN'),budget:new Budget(2,()=>t),trace:new Trace(path.join(directory,id+'.trace'),id)}),/ALREADY_ATTEMPTED|REQUIRES_PREPARED/);assert.equal(calls.length,1);
  assert(calls.every(c=>c.name===(method==='COMPOSER_ENTER_KEY'?'Input.dispatchKeyEvent':'Input.dispatchMouseEvent')));
 }
 checks.I_click_never_enter='PASS';checks.J_enter_never_click='PASS';
 const events=[];await sendPhysicalEnter(null,async(_,name,params)=>events.push({name,params}));assert.deepEqual(events.map(e=>e.params.type),['keyDown','keyUp']);assert(events.every(e=>e.params.key==='Enter'));checks.enter_physical_pair='PASS';
 ledger.reserve('sent',prompt);ledger.update('sent',{user_turns_before:0,assistant_turns_before:0,conversation_url:url});ledger.update('sent',{delivery_state:'DELIVERY_INTENT',send_attempts:1});ledger.update('sent',{delivery_state:'SENT_CONFIRMED',message_confirmed:true,user_turns_after:1});assert.equal(ledger.result('sent').status,'ALREADY_SENT');checks.K_sent_retry='PASS';
 assert.equal(hash(Buffer.from(prompt,'utf8').toString('utf8')),hash(prompt));for(const u of ['http://chatgpt.com/','https://foo.chatgpt.com/','https://openai.com/'])assert.throws(()=>selectActuator(record,{...one,url:u}),/DOMAIN/);checks.L_utf8_domain_idempotency='PASS';
 console.log(JSON.stringify({status:'PASS',checks,real_sends:0},null,2));
}finally{fs.rmSync(directory,{recursive:true});}})().catch(e=>{console.error(e);process.exitCode=1;});
