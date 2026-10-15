'use strict';
// Shared DOM identity. Message/code editors are never the input composer.
// Rendered offscreen nodes remain eligible; scope/uniqueness decide ownership.
function chatGptComposers() {
  const rendered=el=>{
    if(el.isConnected===false)return false;
    for(let n=el;n;n=n.parentElement){const s=getComputedStyle(n);if(n.hidden||n.inert||n.getAttribute?.('aria-hidden')==='true'||s.display==='none'||s.visibility==='hidden'||s.visibility==='collapse')return false;}
    const rects=el.getClientRects?Array.from(el.getClientRects()):[el.getBoundingClientRect()];
    return rects.some(r=>r.width>0&&r.height>0);
  };
  const outsideMessage=el=>!el.closest?.('[data-message-author-role],article[data-turn],.bg-user-message,[class*="DilResponseRoot"],.cm-content,.cm-editor,.monaco-editor');
  const eligible=Array.from(document.querySelectorAll('[contenteditable="true"],textarea'))
    .filter(el=>rendered(el)&&!el.disabled&&!el.readOnly&&!el.parentElement?.closest('[contenteditable="true"]')&&outsideMessage(el));
  // Positive composer identity, rather than the editor framework's CSS class.
  // Unknown editable widgets (Canvas, search, feedback, code) fail closed.
  return eligible.filter(el=>el.hasAttribute?.('data-composer-markdown')||el.id==='prompt-textarea'||el.getAttribute?.('data-testid')==='prompt-textarea');
}
function composerBindings(){return `const chatGptComposers=${chatGptComposers.toString()};`;}
module.exports={chatGptComposers,composerBindings};
