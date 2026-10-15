'use strict';

// These functions run in the approved top document. Layout membership is
// independent of scrolling: a rendered turn outside the viewport still counts.
function isRenderedConversationTurn(element) {
  if (!element?.isConnected) return false;
  for (let node = element; node; node = node.parentElement) {
    if (node.hidden || node.hasAttribute('hidden') || node.inert || node.hasAttribute('inert') ||
        node.getAttribute('aria-hidden') === 'true') return false;
    const style = getComputedStyle(node);
    if (style.display === 'none' || style.visibility === 'hidden' || style.visibility === 'collapse') return false;
  }
  return Array.from(element.getClientRects()).some(rect => rect.width > 0 && rect.height > 0);
}

function conversationTurns(role) {
  if (role !== 'user' && role !== 'assistant') throw Error('INVALID_CONVERSATION_ROLE');
  for (const selector of ['[data-message-author-role="' + role + '"]', 'article[data-turn="' + role + '"]']) {
    const active = Array.from(document.querySelectorAll(selector)).filter(isRenderedConversationTurn);
    if (active.length) return active;
  }
  // The DIL mirror can contain nested containers; count the outer message once.
  const selector = role === 'user' ? '.bg-user-message' : '[class*="DilResponseRoot"]';
  return Array.from(document.querySelectorAll(selector))
    .filter(element => !element.parentElement?.closest(selector))
    .filter(isRenderedConversationTurn);
}

function readConversationSnapshot() {
  const users = conversationTurns('user'), assistants = conversationTurns('assistant');
  return {
    user: users.length, assistant: assistants.length,
    composer_empty: (() => { const editors=Array.from(document.querySelectorAll('[contenteditable="true"],textarea')).filter(p=>isRenderedConversationTurn(p)&&!p.disabled&&!p.readOnly&&!p.parentElement?.closest('[contenteditable="true"]'));return editors.length===1&&!(editors[0].value??editors[0].innerText??'').trim(); })(),
    lastUserText: users.length ? users[users.length - 1].innerText.trim().replace(/^(You said:|Tú dijiste:)\s*/i, '') : '',
    lastAssistantText: assistants.length ? assistants[assistants.length - 1].innerText.trim().replace(/^(ChatGPT said:|ChatGPT dijo:)\s*/i, '') : '',
    isStreaming: !!document.querySelector('button[data-testid*="stop"],button[aria-label*="Stop"],button[aria-label*="Detener"],.result-streaming'),
    url: location.href
  };
}

// Inject the exact same lexical bindings into read and guarded rollback scripts.
function conversationBindings() {
  return `const isRenderedConversationTurn = ${isRenderedConversationTurn.toString()};
const conversationTurns = ${conversationTurns.toString()};
const readConversationSnapshot = ${readConversationSnapshot.toString()};`;
}

module.exports = { isRenderedConversationTurn, conversationTurns, readConversationSnapshot, conversationBindings };
