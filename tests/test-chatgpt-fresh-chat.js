'use strict';
const assert=require('assert/strict'),fs=require('fs');
const {findNewChatControl,freshReady,requestFreshChat}=require('../tools/chatgpt-fresh-chat');
const empty={url:'https://chatgpt.com/',user:0,assistant:0,composer_found:true,composer_matches:1,editable:true,composer:'',isStreaming:false,buttons:[],focused:false};
(async()=>{
 const checks={};let clicks=0,focus=0,stage=0;
 const hit={};const offscreen={disabled:false,innerText:'',getAttribute:()=> 'Nuevo chat',getBoundingClientRect:()=>({x:0,y:2000,width:24,height:24}),contains:()=>false};
 const actual={disabled:false,innerText:'Nuevo chat',getAttribute:()=>null,getBoundingClientRect:()=>({x:10,y:10,width:24,height:24}),contains:v=>v===hit};
 global.getComputedStyle=()=>({visibility:'visible',display:'block'});global.document={querySelectorAll:()=>[offscreen,actual],elementFromPoint:(x,y)=>y<100?hit:null};assert.equal(findNewChatControl().length,1);assert.equal(findNewChatControl()[0].y,22);checks.offscreen_aria_cannot_mask_visible_navigation='PASS';
 const result=await requestFreshChat({inspect:async()=>stage?{...empty,focused:focus===1}:{...empty,composer:'HISTORICAL DRAFT'},findControl:async()=>[{x:1,y:1}],clickNavigation:async()=>{clicks++;stage=1;},focusEmpty:async()=>{focus++;},sleep:async()=>{}});
 assert.equal(result.FRESH_CHAT_READY,true);assert.equal(result.prior_draft_present,true);assert.equal(clicks,1);assert.equal(focus,1);checks.real_navigation_then_empty='PASS';
 for(const [name,observation] of Object.entries({retained_draft:{...empty,composer:'HISTORICAL DRAFT'},old_user:{...empty,user:1},old_assistant:{...empty,assistant:1},streaming:{...empty,isStreaming:true},old_conversation:{...empty,url:'https://chatgpt.com/c/old'},noneditable:{...empty,editable:false}})){
  let n=0;await assert.rejects(requestFreshChat({inspect:async()=>observation,findControl:async()=>[{x:1,y:1}],clickNavigation:async()=>{n++;},focusEmpty:async()=>{throw Error('must not focus invalid composer');},sleep:async()=>{}}),/FRESH_CHAT/);assert(n<=1);checks[name+'_deny_no_clear']='PASS';
 }
 assert.equal(freshReady({...empty,focused:true}),true);assert.equal(freshReady({...empty,url:'https://foo.chatgpt.com/',focused:true}),false);
 await assert.rejects(requestFreshChat({inspect:async()=>empty,findControl:async()=>[{},{}],clickNavigation:async()=>{throw Error('ambiguous must not click');},sleep:async()=>{}}),/UNAVAILABLE_OR_AMBIGUOUS/);checks.ambiguous_new_chat_no_click='PASS';
 const source=fs.readFileSync(require.resolve('../tools/chatgpt-bridge'),'utf8');assert(!source.includes("sendCdp(ws,'Page.navigate'"));assert(source.indexOf('freshChat=await openFreshChat(ws)')<source.indexOf('!ledger.reserve(consultationId,preparedPrompt())'));checks.fresh_before_reservation='PASS';
 console.log(JSON.stringify({status:'PASS',checks,messages_sent:0},null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});
