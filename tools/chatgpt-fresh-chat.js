'use strict';
const {hash,normalize}=require('./chatgpt-ledger');
const {conversationId}=require('./chatgpt-delivery');
function findNewChatControl(){
 const visible=el=>{const r=el.getBoundingClientRect(),s=getComputedStyle(el);return r.width>0&&r.height>0&&s.visibility!=='hidden'&&s.display!=='none'&&!el.disabled;};
 const candidates=Array.from(document.querySelectorAll('button,a')).filter(visible).filter(el=>{const r=el.getBoundingClientRect(),hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return !!hit&&el.contains(hit);});
 const named=candidates.filter(el=>/^(Nuevo chat|New chat)$/i.test(el.getAttribute('aria-label')||''));
 const matched=named.length?named:candidates.filter(el=>/^(Nuevo chat|New chat)$/i.test(el.innerText?.trim()||''));
 return matched.map(el=>{const r=el.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2,hit=document.elementFromPoint(x,y);return {x,y,width:r.width,height:r.height,hit:!!hit&&el.contains(hit)};}).filter(b=>b.hit);
}
function emptyConversation(o){
 try{return conversationId(o.url)===null&&o.composer_found===true&&o.composer_matches===1&&o.editable===true&&typeof o.composer==='string'&&normalize(o.composer)===''&&o.user===0&&o.assistant===0&&o.isStreaming===false;}catch{return false;}
}
function freshReady(o){return emptyConversation(o)&&((o.buttons||[]).filter(b=>b.visible&&b.hit&&b.expectedSend).length===1||o.focused===true);}
async function requestFreshChat({inspect,findControl,clickNavigation,focusEmpty,sleep=ms=>new Promise(r=>setTimeout(r,ms)),trace}){
 const before=await inspect();conversationId(before.url);
 if(!before.composer_found||before.composer_matches!==1||before.isStreaming!==false)throw Error('FRESH_CHAT_INITIAL_STATE_DENIED');
 trace?.emit('REQUEST_FRESH_CHAT',{prompt_sha256:hash(normalize(before.composer||''))});
 const buttons=await findControl();
 if(buttons.length!==1)throw Error('NEW_CHAT_CONTROL_UNAVAILABLE_OR_AMBIGUOUS');
 await clickNavigation(buttons[0]); // Navigation action only, never the send actuator.
 let current;
 for(let i=0;i<12;i++){
  await sleep(250);current=await inspect();conversationId(current.url);
  if(emptyConversation(current)){
   if(!freshReady(current)){await focusEmpty();current=await inspect();}
   if(freshReady(current)){trace?.emit('FRESH_CHAT_READY',{user:0,assistant:0,composer_empty:true});return {status:'PASS',FRESH_CHAT_READY:true,prior_composer_sha256:hash(normalize(before.composer||'')),prior_draft_present:!!normalize(before.composer||''),url:current.url,user:0,assistant:0,composer_empty:true};}
  }
 }
 throw Error('FRESH_CHAT_NOT_EMPTY_OR_NOT_READY_NO_CLEAR');
}
module.exports={findNewChatControl,emptyConversation,freshReady,requestFreshChat};
