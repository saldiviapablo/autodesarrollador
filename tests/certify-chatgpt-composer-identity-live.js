'use strict';
// Read-only proof on the already completed A10 reply containing CodeMirror.
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const {verifyDedicatedProfile,validateDomain,guardPageExpression,readConversation}=require('../tools/chatgpt-bridge');
const {inspectComposer}=require('../tools/chatgpt-send-actuator');const {conversationBindings}=require('../tools/chatgpt-conversation');const {hash}=require('../tools/chatgpt-ledger');
const R=path.resolve(__dirname,'..'),E=path.resolve(process.env.F24_PREFLIGHT_E||''),id='f24-a10-9ef973fcd207446197d8ffd7e8b4b12d';
(async()=>{
 assert(!path.relative(path.join(R,'evidence'),E).startsWith('..'));
 const file=path.join(R,'runtime/chatgpt-consultations',hash(id)+'.json'),ledgerBefore=fs.readFileSync(file),record=JSON.parse(ledgerBefore);assert.equal(record.delivery_state,'COMPLETED');assert.equal(record.send_attempts,1);
 const profile=verifyDedicatedProfile(),tabs=(await(await fetch('http://127.0.0.1:9222/json')).json()).filter(t=>t.type==='page');assert.equal(tabs.length,1);assert(validateDomain(tabs[0].url));assert.equal(tabs[0].url,record.conversation_url);
 const ws=new WebSocket(tabs[0].webSocketDebuggerUrl);await new Promise((resolve,reject)=>{const t=setTimeout(()=>reject(Error('CONNECT_TIMEOUT')),5000);ws.onopen=()=>{clearTimeout(t);resolve();};});
 try{
  const expression=`(()=>{${conversationBindings()}return {snapshot:readConversationSnapshot(),actuator:(${inspectComposer.toString()})(),raw_editors:document.querySelectorAll('[contenteditable="true"],textarea').length,semantic_composers:chatGptComposers().length,code_editors:Array.from(document.querySelectorAll('.cm-content[contenteditable="true"]')).filter(isRenderedConversationTurn).map(e=>e.innerText)};})()`;
  const first=await new Promise((resolve,reject)=>{const t=setTimeout(()=>reject(Error('READ_TIMEOUT')),5000);ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id!==1)return;clearTimeout(t);m.error||m.result?.exceptionDetails?reject(Error('READ_FAILED')):resolve(m.result.result.value);};ws.send(JSON.stringify({id:1,method:'Runtime.evaluate',params:{expression:guardPageExpression(expression),returnByValue:true}}));});
  assert(first.code_editors.length>=1);assert(first.raw_editors>first.semantic_composers);assert.equal(first.semantic_composers,1);assert.equal(first.actuator.composer_matches,1);assert.equal(first.actuator.composer,'');assert.equal(first.snapshot.composer_empty,true);assert.equal(first.snapshot.user,1);assert.equal(first.snapshot.assistant,1);assert.equal(first.snapshot.isStreaming,false);assert.equal(hash(first.snapshot.lastAssistantText),record.response_sha256);
  const actual=await readConversation(ws);assert.equal(actual.composer_empty,true);assert.equal(actual.user,1);assert.equal(actual.assistant,1);assert.equal(hash(actual.lastAssistantText),record.response_sha256);assert(fs.readFileSync(file).equals(ledgerBefore));
  const proof={status:'PASS',at:new Date().toISOString(),profile,consultation_id:id,observation:first,productive_reader_composer_empty:true,response_sha256:record.response_sha256,ledger_byte_unchanged:true,physical_send_count:0,prompt_insertions:0,composer_deletions:0,focus_actions:0,ledger_reservations:0,delivery_intents:0,turn_delta:'0/0',attempt10_still:'HISTORICAL FAIL'};
  fs.writeFileSync(path.join(E,'LIVE-READONLY.json'),JSON.stringify(proof,null,2));console.log(JSON.stringify({status:'PASS',raw_editors:first.raw_editors,semantic_composers:first.semantic_composers,code_editors:first.code_editors.length,composer_empty:true,response_hash_match:true,input_actions:0,ledger_changes:0}));
 }finally{ws.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
