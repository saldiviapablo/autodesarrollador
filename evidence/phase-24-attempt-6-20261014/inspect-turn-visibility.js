'use strict';
const fs=require('fs'),path=require('path');
const {validateDomain,guardPageExpression}=require('../../tools/chatgpt-bridge');
(async()=>{
 const tabs=(await(await fetch('http://127.0.0.1:9222/json')).json()).filter(t=>t.type==='page');if(tabs.length!==1||!validateDomain(tabs[0].url))throw Error('DOMAIN_OR_TAB_COUNT_DENIED');
 const ws=new WebSocket(tabs[0].webSocketDebuggerUrl);await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j;});
 const result=await new Promise((r,j)=>{const timer=setTimeout(()=>j(Error('READ_TIMEOUT')),5000);ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id===1){clearTimeout(timer);r(m.result);}};
 const expression=`(() => {const role=name=>{let a=Array.from(document.querySelectorAll('[data-message-author-role="'+name+'"]'));if(a.length)return a;a=Array.from(document.querySelectorAll('article[data-turn="'+name+'"]'));if(a.length)return a;const s=name==='user'?'.bg-user-message':'[class*="DilResponseRoot"]';return Array.from(document.querySelectorAll(s)).filter(e=>!e.parentElement?.closest(s));};const shape=e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return {tag:e.tagName,width:r.width,height:r.height,display:s.display,visibility:s.visibility,aria_hidden_ancestor:!!e.closest('[aria-hidden="true"]'),rendered:!!e.getClientRects().length};};return {url:location.href,user:role('user').map(shape),assistant:role('assistant').map(shape),no_dom_mutation:true};})()`;
 ws.send(JSON.stringify({id:1,method:'Runtime.evaluate',params:{expression:guardPageExpression(expression),returnByValue:true}}));});ws.close();fs.writeFileSync(path.join(__dirname,'turn-visibility.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});
