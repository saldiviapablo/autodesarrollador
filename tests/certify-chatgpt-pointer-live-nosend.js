'use strict';
// Live transport/selection test only. Hard transport guard forbids every send
// primitive, including key events and mouse button presses/releases.
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const {verifyDedicatedProfile,validateDomain,guardPageExpression}=require('../tools/chatgpt-bridge');
const {inspectComposer,selectActuator,probePointerMove}=require('../tools/chatgpt-send-actuator');
const {prepareComposerText}=require('../tools/chatgpt-composer-prepare');
const {conversationBindings}=require('../tools/chatgpt-conversation');
const {acquireBrowserLease,hash,normalize}=require('../tools/chatgpt-ledger');
const R=path.resolve(__dirname,'..'),E=path.resolve(process.env.F24_PREFLIGHT_E||''),D=path.join(R,'runtime/chatgpt-consultations');
const text='Canario de preparación, NO ENVIAR. '+crypto.randomUUID()+'\nUnicode áéíóú ñ\nVerificación de foco y SHA\nCampo multilínea\nNo es una consulta.';
function ledgerHashes(){return Object.fromEntries(fs.readdirSync(D).filter(n=>/^[a-f0-9]{64}\.(json|trace\.jsonl|parent\.trace\.jsonl)$/.test(n)).map(n=>[n,hash(fs.readFileSync(path.join(D,n),'utf8'))]));}
(async()=>{
 assert(!path.relative(path.join(R,'evidence'),E).startsWith('..'));
 const profile=verifyDedicatedProfile(),tabs=(await(await fetch('http://127.0.0.1:9222/json')).json()).filter(t=>t.type==='page');assert.equal(tabs.length,1);assert(validateDomain(tabs[0].url));assert.equal(tabs[0].url,'https://chatgpt.com/');
 const beforeLedgers=ledgerHashes(),release=acquireBrowserLease();let ws,seq=0,inserted=false;const calls=[];
 try{
  ws=new WebSocket(tabs[0].webSocketDebuggerUrl);await new Promise((resolve,reject)=>{const t=setTimeout(()=>reject(Error('CONNECT_TIMEOUT')),5000);ws.onopen=()=>{clearTimeout(t);resolve();};});
  const dispatch=async(_,method,params={})=>{
   if(method==='Input.dispatchMouseEvent')assert(params.type==='mouseMoved'&&params.button==='none'&&params.buttons===0,'SEND_PRIMITIVE_DENIED');
   else assert(['Runtime.evaluate','Page.bringToFront'].includes(method),'SEND_PRIMITIVE_DENIED');
   calls.push({method,...(method==='Input.dispatchMouseEvent'?{type:params.type,button:params.button,buttons:params.buttons}:{})});
   return new Promise((resolve,reject)=>{const id=++seq,t=setTimeout(()=>{ws.removeEventListener('message',on);reject(Error('Timeout esperando respuesta CDP para '+method));},5000);const on=e=>{const m=JSON.parse(e.data);if(m.id!==id)return;clearTimeout(t);ws.removeEventListener('message',on);m.error||m.result?.exceptionDetails?reject(Error('CDP_EVALUATION_FAILED')):resolve(m.result);};ws.addEventListener('message',on);ws.send(JSON.stringify({id,method,params:method==='Runtime.evaluate'?{...params,expression:guardPageExpression(params.expression)}:params}));});
  };
  const evaluate=async expression=>(await dispatch(ws,'Runtime.evaluate',{expression,returnByValue:true})).result.value;
  const inspect=()=>evaluate(`(()=>{${conversationBindings()}return {...readConversationSnapshot(),...(${inspectComposer.toString()})()};})()`);
  const before=await inspect();assert.equal(before.user,0);assert.equal(before.assistant,0);assert.equal(before.composer,'');assert.equal(before.isStreaming,false);assert.equal(before.composer_matches,1);
  await dispatch(ws,'Page.bringToFront');await evaluate(`(${prepareComposerText.toString()})(${JSON.stringify(text)},${inspectComposer.toString()})`);inserted=true;
  await new Promise(r=>setTimeout(r,700));const prepared=await inspect();assert.equal(hash(normalize(prepared.composer)),hash(normalize(text)));assert.equal(prepared.user,0);assert.equal(prepared.assistant,0);
  const input={delivery_state:'PREPARED',send_attempts:0,prompt_sha256:hash(normalize(text)),conversation_url:prepared.url};
  const primary=selectActuator(input,prepared);const button=prepared.buttons.find(b=>b.visible&&b.width>0&&b.height>0);assert(button,'LIVE_POINTER_TARGET_NOT_PRESENT');
  const start=Date.now(),available=await probePointerMove(ws,button,dispatch),duration=Date.now()-start;
  const afterProbe=await inspect();assert.equal(afterProbe.user,0);assert.equal(afterProbe.assistant,0);assert.equal(afterProbe.url,before.url);assert.equal(afterProbe.focused,true);assert.equal(hash(normalize(afterProbe.composer)),input.prompt_sha256);
  const selected=selectActuator(input,afterProbe,{pointerAvailable:available});
  if(!available)assert.equal(selected.method,'COMPOSER_ENTER_KEY');
  // Clear only this unique test-owned text, with exact URL/counters/hash/focus.
  await evaluate(`(()=>{${conversationBindings()}const o=(${inspectComposer.toString()})(${JSON.stringify(text)});if(location.href!==${JSON.stringify(before.url)}||conversationTurns('user').length!==0||conversationTurns('assistant').length!==0||!o.composer_found||o.composer_matches!==1||!o.focused||o.isStreaming)throw Error('OWNED_TEST_CLEANUP_DENIED');const p=Array.from(document.querySelectorAll('[contenteditable="true"],textarea'))[o.composer_dom_index];if(p.tagName==='TEXTAREA')p.setSelectionRange(0,p.value.length);else{const r=document.createRange();r.selectNodeContents(p);const s=window.getSelection();s.removeAllRanges();s.addRange(r);}if(!document.execCommand('delete',false,null))throw Error('OWNED_TEST_DELETE_FAILED');p.dispatchEvent(new Event('input',{bubbles:true}));return true;})()`);inserted=false;
  const after=await inspect();assert.equal(after.composer,'');assert.equal(after.user,0);assert.equal(after.assistant,0);assert.deepEqual(ledgerHashes(),beforeLedgers);
  const proof={status:'PASS',profile,before,prepared,primary_method:primary.method,pointer_acknowledged:available,pointer_probe_duration_ms:duration,selected_method_after_probe:selected.method,after,selection_is_component_test_input_not_reservation:true,ledger_files_unchanged:true,ledger_reservations:0,delivery_intents:0,physical_sends:0,turn_delta:'0/0',calls};
  fs.writeFileSync(path.join(E,'LIVE-POINTER-NOSEND.json'),JSON.stringify(proof,null,2));console.log(JSON.stringify({status:proof.status,primary:primary.method,pointer_acknowledged:available,selected:selected.method,physical_sends:0,ledger_reservations:0,composer_empty:true}));
 }finally{ws?.close();release();if(inserted)console.error('OWNED_CANARY_LEFT_FOR_SAFE_INSPECTION_NO_UNCHECKED_CLEAR');}
})().catch(e=>{console.error(e);process.exitCode=1;});
