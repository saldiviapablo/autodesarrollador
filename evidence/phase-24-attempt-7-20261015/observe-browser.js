'use strict';
// Read-only telemetry, never a gate or an input actuator.
const fs=require('fs'),path=require('path');
const R=path.resolve(__dirname,'../..'),E=path.join(R,'evidence/phase-24-attempt-7-20261015');
const {verifyDedicatedProfile,validateDomain,guardPageExpression}=require(path.join(R,'tools/chatgpt-bridge'));
const {conversationBindings}=require(path.join(R,'tools/chatgpt-conversation'));
const {inspectComposer}=require(path.join(R,'tools/chatgpt-send-actuator'));
const observations=[];let ws,seq=0,last;
(async()=>{
 const profile=verifyDedicatedProfile(),tabs=(await(await fetch('http://127.0.0.1:9222/json',{signal:AbortSignal.timeout(3000)})).json()).filter(t=>t.type==='page');
 if(tabs.length!==1||!validateDomain(tabs[0].url))throw Error('READONLY_OBSERVER_DOMAIN_DENIED');
 ws=new WebSocket(tabs[0].webSocketDebuggerUrl);
 await new Promise((resolve,reject)=>{const t=setTimeout(()=>reject(Error('CONNECT_TIMEOUT')),5000);ws.onopen=()=>{clearTimeout(t);resolve();};ws.onerror=()=>{clearTimeout(t);reject(Error('CONNECT_ERROR'));};});
 const expression=`(() => {${conversationBindings()} const t=readConversationSnapshot(),c=(${inspectComposer.toString()})();
  const raw=r=>{for(const s of ['[data-message-author-role="'+r+'"]','article[data-turn="'+r+'"]']){const a=document.querySelectorAll(s);if(a.length)return a.length;}const s=r==='user'?'.bg-user-message':'[class*="DilResponseRoot"]';return Array.from(document.querySelectorAll(s)).filter(e=>!e.parentElement?.closest(s)).length;};
  return {url:t.url,raw_user:raw('user'),raw_assistant:raw('assistant'),active_user:t.user,active_assistant:t.assistant,composer_empty:t.composer_empty&&c.composer==='',focused:c.focused,isStreaming:t.isStreaming};})()`;
 const deadline=Date.now()+2700e3;
 while(Date.now()<deadline&&!fs.existsSync(path.join(E,'SUMMARY.json'))){
  const value=await new Promise((resolve,reject)=>{
   const id=++seq,t=setTimeout(()=>{ws.removeEventListener('message',receive);reject(Error('READ_TIMEOUT'));},5000);
   const receive=e=>{const m=JSON.parse(e.data);if(m.id!==id)return;clearTimeout(t);ws.removeEventListener('message',receive);if(m.error||m.result?.exceptionDetails)reject(Error('READ_ERROR'));else resolve(m.result.result.value);};
   ws.addEventListener('message',receive);ws.send(JSON.stringify({id,method:'Runtime.evaluate',params:{expression:guardPageExpression(expression),returnByValue:true}}));
  });
  const now=Date.now(),serialized=JSON.stringify(value);
  // Keep heartbeat samples too, so the exact pre-send interval is auditable.
  if(serialized!==last||!observations.length||now-Date.parse(observations.at(-1).at)>1000){observations.push({at:new Date(now).toISOString(),...value});last=serialized;fs.writeFileSync(path.join(E,'browser-layout-observations.json'),JSON.stringify({profile,read_only:true,input_actions:0,observations},null,2));}
  await new Promise(resolve=>setTimeout(resolve,250));
 }
 console.log('BROWSER_READONLY_OBSERVATIONS '+observations.length);
})().catch(e=>{fs.writeFileSync(path.join(E,'browser-observer-error.txt'),e.message);console.error(e);process.exitCode=1;}).finally(()=>ws?.close());
