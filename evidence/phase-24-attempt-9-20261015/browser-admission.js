'use strict';
const assert=require('assert/strict'),fs=require('fs'),path=require('path');
const R=path.resolve(__dirname,'../..'),E=path.join(R,'evidence/phase-24-attempt-9-20261015');
const {verifyDedicatedProfile,validateDomain,guardPageExpression}=require(path.join(R,'tools/chatgpt-bridge'));
const {conversationBindings}=require(path.join(R,'tools/chatgpt-conversation'));
const {inspectComposer}=require(path.join(R,'tools/chatgpt-send-actuator'));
(async()=>{
 const profile=verifyDedicatedProfile();
 const pages=(await(await fetch('http://127.0.0.1:9222/json',{signal:AbortSignal.timeout(3000)})).json()).filter(t=>t.type==='page');
 assert.equal(pages.length,1);assert(validateDomain(pages[0].url));
 const ws=new WebSocket(pages[0].webSocketDebuggerUrl);
 try{
  await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('CONNECT_TIMEOUT')),5000);ws.onopen=()=>{clearTimeout(timer);resolve();};ws.onerror=()=>{clearTimeout(timer);reject(Error('CONNECT_FAILED'));};});
  const observation=await new Promise((resolve,reject)=>{
   const timer=setTimeout(()=>reject(Error('READ_TIMEOUT')),5000);
   ws.onmessage=event=>{const m=JSON.parse(event.data);if(m.id!==1)return;clearTimeout(timer);if(m.error||m.result?.exceptionDetails)reject(Error('READ_FAILED'));else resolve(m.result.result.value);};
   const expression=`(() => {${conversationBindings()} const t=readConversationSnapshot(),c=(${inspectComposer.toString()})();
    const raw=r=>{for(const s of ['[data-message-author-role="'+r+'"]','article[data-turn="'+r+'"]']){const a=document.querySelectorAll(s);if(a.length)return a.length;}const s=r==='user'?'.bg-user-message':'[class*="DilResponseRoot"]';return Array.from(document.querySelectorAll(s)).filter(e=>!e.parentElement?.closest(s)).length;};
    return {url:t.url,raw_user:raw('user'),raw_assistant:raw('assistant'),active_user:t.user,active_assistant:t.assistant,composer_empty:t.composer_empty&&c.composer==='',composer_found:c.composer_found,composer_matches:c.composer_matches,focused:c.focused,isStreaming:t.isStreaming};})()`;
   ws.send(JSON.stringify({id:1,method:'Runtime.evaluate',params:{expression:guardPageExpression(expression),returnByValue:true}}));
  });
  assert(validateDomain(observation.url));
  fs.writeFileSync(path.join(E,'admission-browser.json'),JSON.stringify({status:'PASS',at:new Date().toISOString(),profile,pages:pages.length,observation,read_only:true},null,2));
  console.log(JSON.stringify({status:'PASS',profile_match:true,...observation}));
 }finally{ws.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
