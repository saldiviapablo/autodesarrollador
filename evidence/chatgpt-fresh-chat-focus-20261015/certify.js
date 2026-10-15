'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto'),{spawnSync}=require('node:child_process');
const ROOT=path.resolve(__dirname,'../..'),E=path.join(ROOT,'evidence/chatgpt-fresh-chat-focus-20261015');
const sha=data=>crypto.createHash('sha256').update(data).digest('hex');
const counters={prompt_insertions:0,ledger_reservations:0,delivery_intent:0,send_method_selected:0,physical_send_actions:0,focus_actions:0};
// Tripwires apply only to this certification process. No product files change.
const ledger=require(path.join(ROOT,'tools/chatgpt-ledger'));
ledger.ConsultationLedger.prototype.reserve=function(){counters.ledger_reservations++;throw Error('LEDGER_RESERVATION_FORBIDDEN');};
ledger.ConsultationLedger.prototype.update=function(id,patch){if(patch?.delivery_state==='DELIVERY_INTENT')counters.delivery_intent++;throw Error('LEDGER_WRITE_FORBIDDEN');};
const actuator=require(path.join(ROOT,'tools/chatgpt-send-actuator'));
actuator.selectActuator=function(){counters.send_method_selected++;throw Error('SEND_METHOD_FORBIDDEN');};
actuator.sendPhysicalEnter=async function(){counters.physical_send_actions++;throw Error('PHYSICAL_SEND_FORBIDDEN');};
const {validateDomain,guardPageExpression,verifyDedicatedProfile,readConversation}=require(path.join(ROOT,'tools/chatgpt-bridge'));
const {conversationBindings}=require(path.join(ROOT,'tools/chatgpt-conversation'));
const {emptyConversation,freshReady}=require(path.join(ROOT,'tools/chatgpt-fresh-chat'));
const sourceFiles=['tools/chatgpt-bridge.js','tools/chatgpt-conversation.js','tools/chatgpt-ledger.js','tools/chatgpt-delivery.js','tools/chatgpt-pre-send.js','tools/chatgpt-send-actuator.js','tools/chatgpt-fresh-chat.js'];
const sourceBefore=Object.fromEntries(sourceFiles.map(f=>[f,sha(fs.readFileSync(path.join(ROOT,f)))]));
function ledgerSnapshot(){const d=path.join(ROOT,'runtime/chatgpt-consultations');return Object.fromEntries(fs.readdirSync(d).sort().filter(f=>fs.statSync(path.join(d,f)).isFile()).map(f=>[f,sha(fs.readFileSync(path.join(d,f)))]));}
const git=(...args)=>{const r=spawnSync('git',args,{cwd:ROOT,encoding:'utf8',windowsHide:true});assert.equal(r.status,0);return r.stdout.trim();};
const pageRead=`(() => { ${conversationBindings()}
  const turns=readConversationSnapshot(),composer=(${actuator.inspectComposer.toString()})();
  const raw=role=>{for(const s of ['[data-message-author-role="'+role+'"]','article[data-turn="'+role+'"]']){const a=Array.from(document.querySelectorAll(s));if(a.length)return a.length;}const s=role==='user'?'.bg-user-message':'[class*="DilResponseRoot"]';return Array.from(document.querySelectorAll(s)).filter(e=>!e.parentElement?.closest(s)).length;};
  return {url:turns.url,user:turns.user,assistant:turns.assistant,raw_user:raw('user'),raw_assistant:raw('assistant'),
    isStreaming:turns.isStreaming,composer_found:composer.composer_found,composer_matches:composer.composer_matches,
    composer_empty:turns.composer_empty&&composer.composer==='',composer:composer.composer===''?'':null,
    editable:composer.editable,focused:composer.focused,buttons:composer.buttons};
})()`;
const baselineValid=o=>validateDomain(o.url)&&o.url==='https://chatgpt.com/'&&o.composer_empty===true&&emptyConversation(o);
let sequence=0,ws;const commands=[];
async function evaluate(expression,label){
 return new Promise((resolve,reject)=>{
  const id=++sequence,timer=setTimeout(()=>{ws.removeEventListener('message',receive);reject(Error('CDP_TIMEOUT_NO_RETRY'));},5000);
  function receive(event){const m=JSON.parse(event.data);if(m.id!==id)return;clearTimeout(timer);ws.removeEventListener('message',receive);if(m.error||m.result?.exceptionDetails)reject(Error(m.result?.exceptionDetails?.exception?.description||'CDP_FAILED'));else resolve(m.result.result.value);}
  ws.addEventListener('message',receive);commands.push({method:'Runtime.evaluate',label,expression_sha256:sha(expression)});
  ws.send(JSON.stringify({id,method:'Runtime.evaluate',params:{expression:guardPageExpression(expression),returnByValue:true}}));
 });
}
async function tabs(){const pages=(await(await fetch('http://127.0.0.1:9222/json',{signal:AbortSignal.timeout(3000)})).json()).filter(t=>t.type==='page');assert.equal(pages.length,1);assert(validateDomain(pages[0].url));assert.equal(pages[0].url,'https://chatgpt.com/');return pages;}
(async()=>{
 assert.equal(git('rev-parse','--short','HEAD'),'80dd12c');assert.equal(git('status','--porcelain=v1'),'');
 const profile=verifyDedicatedProfile(),beforeLedgers=ledgerSnapshot(),pages=await tabs();
 ws=new WebSocket(pages[0].webSocketDebuggerUrl);
 await new Promise((resolve,reject)=>{const t=setTimeout(()=>{ws.close();reject(Error('CONNECT_TIMEOUT'));},5000);ws.onopen=()=>{clearTimeout(t);resolve();};ws.onerror=()=>{clearTimeout(t);reject(Error('CONNECT_FAILED'));};});
 const nativeSend=ws.send.bind(ws);ws.send=data=>{const m=JSON.parse(data);if(m.method!=='Runtime.evaluate'){counters.physical_send_actions++;throw Error('NON_READ_CDP_FORBIDDEN');}return nativeSend(data);};
 try{
  const before=await evaluate(pageRead,'PRECHECK_READ');assert(baselineValid(before),'PRECHECK_FAILED_NO_ACTION');
  const actual=await readConversation(ws);assert.equal(actual.user,0);assert.equal(actual.assistant,0);assert.equal(actual.composer_empty,true);assert.equal(actual.url,before.url);
  assert.equal((await tabs())[0].id,pages[0].id);verifyDedicatedProfile();
  fs.mkdirSync(E,{recursive:false});fs.copyFileSync(__filename,path.join(E,'certify.js'));
  fs.writeFileSync(path.join(E,'PRECHECK.json'),JSON.stringify({at:new Date().toISOString(),profile,before,sourceBefore,ledger_files:beforeLedgers},null,2));
  // Reuse the exact production focus operation, with atomic baseline checks
  // immediately before it. This is the only browser mutation in this script.
  const bridgeSource=fs.readFileSync(path.join(ROOT,'tools/chatgpt-bridge.js'),'utf8');
  const match=bridgeSource.match(/focusEmpty:async\(\)=>\{await sendCdp\(ws,'Runtime.evaluate',\{expression:`([\s\S]*?)`,returnByValue:true\}\);\}/);
  assert(match,'PRODUCTION_FOCUS_NOT_FOUND');
  const focused=await evaluate(`(() => {
    const current=(${pageRead});
    if(location.href!=='https://chatgpt.com/'||current.composer_found!==true||current.composer_matches!==1||current.editable!==true||current.composer_empty!==true||current.isStreaming!==false||current.user!==0||current.assistant!==0)throw Error('ATOMIC_PRECHECK_FAILED_NO_FOCUS');
    const applied=(${match[1]});
    return {applied,before:current,after:(${pageRead})};
  })()`,'ONE_PRODUCTION_FOCUS');
  assert.equal(focused.applied,true);counters.focus_actions=1;
  const after=await evaluate(pageRead,'POSTCHECK_READ');assert(baselineValid(after));assert.equal(after.focused,true);assert.equal(freshReady(after),true);
  assert.equal(focused.after.focused,true);assert(baselineValid(focused.after));
  assert.equal((await tabs())[0].id,pages[0].id);verifyDedicatedProfile();
  assert.deepEqual(ledgerSnapshot(),beforeLedgers);
  for(const [file,expected]of Object.entries(sourceBefore))assert.equal(sha(fs.readFileSync(path.join(ROOT,file))),expected);
  assert.deepEqual(counters,{prompt_insertions:0,ledger_reservations:0,delivery_intent:0,send_method_selected:0,physical_send_actions:0,focus_actions:1});
  const result={status:'PASS',at:new Date().toISOString(),profile,before,immediate_focus_observation:focused,after,FRESH_CHAT_READY:freshReady(after),counters,
    turn_delta:{user:after.user-before.user,assistant:after.assistant-before.assistant},ledger_file_set_and_hashes_unchanged:true,production_source_hashes_unchanged:true,
    commands,regression:'PASS / no send, no text mutations, no ledger writes, no turn delta; certified source unchanged',F24_started:false,attempt7_created:false};
  fs.writeFileSync(path.join(E,'RESULT.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
 }finally{ws.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
