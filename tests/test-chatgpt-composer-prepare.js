'use strict';
const assert=require('node:assert/strict'),vm=require('node:vm');
const {inspectComposer}=require('../tools/chatgpt-send-actuator');
const {prepareComposerText}=require('../tools/chatgpt-composer-prepare');
const {conversationBindings}=require('../tools/chatgpt-conversation');
const {composerBindings}=require('../tools/chatgpt-composer');
const prompt='Consulta UTF-8: áéíóú ñ — € °\nSegunda línea\n\nfin';
function fixture({count=1,dirty=false,streaming=false,focusFail=false,corrupt=false,hiddenAncestor=false}={}){
 let selected,insertions=0;const rect={x:0,y:0,width:400,height:30};
 const doc={activeElement:null};
 const node=(visible,text='')=>({isConnected:true,innerText:text,tagName:'DIV',isContentEditable:true,parentElement:null,style:{display:visible?'block':'none',visibility:'visible'},hidden:false,
   getAttribute:()=>null,hasAttribute:()=>false,getBoundingClientRect:()=>visible?rect:{...rect,width:0},getClientRects:()=>visible?[rect]:[],
   querySelectorAll:()=>[],contains(x){return x===this;},closest:()=>null,
   focus(){if(!focusFail)doc.activeElement=this;},dispatchEvent(){},});
 const hidden=node(false,'');const editors=Array.from({length:count},()=>({...node(true,dirty?'preexisting':''),id:'prompt-textarea'}));
 if(hiddenAncestor&&editors[0])editors[0].parentElement=node(false);
 doc.querySelectorAll=s=>s==='[contenteditable="true"],textarea'?[hidden,...editors]:[];
 doc.querySelector=s=>s==='.ProseMirror'?hidden:s.includes('stop')&&streaming?{}:null;
 doc.createRange=()=>({selectNodeContents(p){selected=p;}});
 doc.execCommand=(command,_,text)=>{assert.equal(command,'insertText');assert.equal(selected,doc.activeElement);selected.innerText=corrupt?'damaged':text;insertions++;return true;};
 const ctx=vm.createContext({document:doc,location:{href:'https://chatgpt.com/'},getComputedStyle:n=>n.style||{display:'block',visibility:'visible'},window:{getSelection:()=>({removeAllRanges(){},addRange(){}})},Event:class{}});
 const evaluate=s=>vm.runInContext(s,ctx);
 const inspect=()=>evaluate(`(()=>{${composerBindings()}return (${inspectComposer.toString()})();})()`);
 const prepare=()=>evaluate(`(()=>{${composerBindings()}return (${prepareComposerText.toString()})(${JSON.stringify(prompt)},${inspectComposer.toString()});})()`);
 const snapshot=()=>evaluate(`(()=>{${conversationBindings()}return readConversationSnapshot();})()`);
 return {doc,hidden,editors,inspect,prepare,snapshot,insertions:()=>insertions};
}
const checks={};
const old=fixture();assert.equal(old.doc.querySelector('.ProseMirror').innerText,'');
const result=old.prepare();assert.equal(result.domText,prompt.replace(/\n\n+/g,'\n'));assert.equal(old.hidden.innerText,'');assert.equal(old.editors[0].innerText,prompt);assert.equal(old.insertions(),1);checks.hidden_retained_legacy_reader_reproduced='PASS';checks.insert_and_read_same_active_editor_utf8='PASS';
assert.equal(old.snapshot().composer_empty,false);assert.throws(()=>old.prepare(),/PREEXISTING/);assert.equal(old.insertions(),1);checks.active_nonempty_hidden_empty_conservative='PASS';checks.no_duplicate_insertion='PASS';
for(const [name,opts,pattern] of [['multiple',{count:2},/NOT_UNIQUE/],['missing',{count:0},/NOT_UNIQUE/],['dirty',{dirty:true},/PREEXISTING/],['streaming',{streaming:true},/NOT_UNIQUE/],['focus',{focusFail:true},/FOCUS/],['ancestor',{hiddenAncestor:true},/NOT_UNIQUE/]]){
 const f=fixture(opts);assert.throws(f.prepare,pattern);assert.equal(f.insertions(),0);checks[name+'_deny_before_write']='PASS';
}
const wrong=fixture({corrupt:true});assert.throws(wrong.prepare,/ENCODING_MISMATCH/);assert.equal(wrong.insertions(),1);assert.equal(wrong.editors[0].innerText,'damaged');checks.corrupt_readback_no_unchecked_clear='PASS';
console.log(JSON.stringify({status:'PASS',checks,physical_sends:0,browser_access:false,ledger_access:false},null,2));
