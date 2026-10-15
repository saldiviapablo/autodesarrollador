'use strict';
// One no-send Unicode roundtrip through the productive bridge. Explicitly
// refuses a nonempty composer, wrong profile/domain, streaming, or nonzero turns.
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto'),{execFileSync}=require('child_process');
const R=path.resolve(__dirname,'..'),E=path.resolve(process.env.F24_PREFLIGHT_E||'');
const {verifyDedicatedProfile,validateDomain,guardPageExpression}=require('../tools/chatgpt-bridge');
const {inspectComposer}=require('../tools/chatgpt-send-actuator');
const {conversationBindings}=require('../tools/chatgpt-conversation');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
function ledgers(){return Object.fromEntries(fs.readdirSync(path.join(R,'runtime/chatgpt-consultations')).filter(n=>n.endsWith('.json')||n.endsWith('.jsonl')).map(n=>[n,hash(fs.readFileSync(path.join(R,'runtime/chatgpt-consultations',n)))]));}
(async()=>{
 assert(path.relative(path.join(R,'evidence'),E)&&!path.relative(path.join(R,'evidence'),E).startsWith('..'));
 const baseline=ledgers(),profile=verifyDedicatedProfile(),tabs=(await(await fetch('http://127.0.0.1:9222/json')).json()).filter(t=>t.type==='page');
 assert.equal(tabs.length,1);assert(validateDomain(tabs[0].url));assert.equal(tabs[0].url,'https://chatgpt.com/');
 const ws=new WebSocket(tabs[0].webSocketDebuggerUrl);await new Promise((resolve,reject)=>{const t=setTimeout(()=>reject(Error('CONNECT_TIMEOUT')),5000);ws.onopen=()=>{clearTimeout(t);resolve();};});
 let id=0;
 async function inspect(){return new Promise((resolve,reject)=>{const request=++id,t=setTimeout(()=>reject(Error('INSPECT_TIMEOUT')),5000);const on=e=>{const m=JSON.parse(e.data);if(m.id!==request)return;clearTimeout(t);ws.removeEventListener('message',on);m.error||m.result.exceptionDetails?reject(Error('INSPECT_FAILED')):resolve(m.result.result.value);};ws.addEventListener('message',on);ws.send(JSON.stringify({id:request,method:'Runtime.evaluate',params:{expression:guardPageExpression(`(()=>{${conversationBindings()}return {conversation:readConversationSnapshot(),composer:(${inspectComposer.toString()})(),editor_count:document.querySelectorAll('[contenteditable="true"],textarea').length};})()`),returnByValue:true}}));});}
 try{
  const before=await inspect();for(const o of [before]){assert.equal(o.conversation.user,0);assert.equal(o.conversation.assistant,0);assert.equal(o.conversation.isStreaming,false);assert.equal(o.composer.composer,'');assert.equal(o.composer.composer_matches,1);}
  const raw=execFileSync(process.execPath,[path.join(R,'tools/chatgpt-bridge.js'),'--action','unicode-roundtrip'],{encoding:'utf8',timeout:45000,windowsHide:true});
  fs.writeFileSync(path.join(E,'live-unicode-bridge.stdout.json'),raw);const rt=JSON.parse(raw);assert.equal(rt.status,'SUCCESS');assert.equal(rt.unicode_roundtrip,'PASS');assert.equal(rt.source_text_equals_dom_text,true);
  const after=await inspect();assert.equal(after.conversation.url,before.conversation.url);assert.equal(after.conversation.user,0);assert.equal(after.conversation.assistant,0);assert.equal(after.conversation.composer_empty,true);assert.equal(after.composer.composer,'');assert.equal(after.conversation.isStreaming,false);assert.deepEqual(ledgers(),baseline);
  const proof={status:'PASS',at:new Date().toISOString(),profile,before,after,production_prepare_and_readback:true,UTF8:'PASS',composer_restored_empty:true,ledger_files_unchanged:true,DELIVERY_INTENT:0,SEND_METHOD_SELECTED:0,PHYSICAL_SEND_ACTIONS:0,TURN_DELTA:'0/0'};
  fs.writeFileSync(path.join(E,'LIVE.json'),JSON.stringify(proof,null,2));console.log(JSON.stringify(proof));
 }finally{ws.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
