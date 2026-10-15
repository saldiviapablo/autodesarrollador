'use strict';
// Read-only diagnostic of navigation controls. No ledger or UI mutations.
const fs=require('fs'),path=require('path');
const {validateDomain,guardPageExpression}=require('../tools/chatgpt-bridge');
(async()=>{
 const pages=(await(await fetch('http://127.0.0.1:9222/json')).json()).filter(p=>p.type==='page');if(pages.length!==1||!validateDomain(pages[0].url))throw Error('DOMAIN_OR_TABS_DENIED');
 const ws=new WebSocket(pages[0].webSocketDebuggerUrl);await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j;});
 const result=await new Promise((r,j)=>{const timer=setTimeout(()=>j(Error('READ_TIMEOUT')),5000);ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id===1){clearTimeout(timer);r(m.result);}};
 const expression=`(() => Array.from(document.querySelectorAll('button,a')).filter(e=>/^(Nuevo chat|New chat)$/i.test(e.getAttribute('aria-label')||e.innerText?.trim()||'')).map(e=>{const r=e.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2,h=document.elementFromPoint(x,y);let a=e;const ancestors=[];for(let i=0;i<5&&a;i++,a=a.parentElement)ancestors.push({tag:a.tagName,id:a.id,role:a.getAttribute('role'),'aria-label':a.getAttribute('aria-label')});return {text:e.innerText,aria:e.getAttribute('aria-label'),x,y,width:r.width,height:r.height,visibility:getComputedStyle(e).visibility,display:getComputedStyle(e).display,hit:!!h&&e.contains(h),ancestors};}))()`;
 ws.send(JSON.stringify({id:1,method:'Runtime.evaluate',params:{expression:guardPageExpression(expression),returnByValue:true}}));});ws.close();
 const e=process.env.F24_PREFLIGHT_E||path.resolve(__dirname,'../evidence/f24-admission-repair-20261014');fs.writeFileSync(path.join(e,'new-chat-controls.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});
