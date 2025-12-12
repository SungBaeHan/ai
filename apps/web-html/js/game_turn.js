// apps/web-html/js/game_turn.js
// 게임 턴 처리 프론트엔드 로직

const API_BASE_URL = window.API_BASE_URL || 'https://api.arcanaverse.ai';

// DOM 요소 참조
let elHud = null;
let elNarration = null;
let elChatLog = null;
let elInput = null;
let elSend = null;

// 게임 ID (템플릿에서 주입)
const gameId = window.GAME_ID || null;

function initGameTurn() {
  // DOM 요소 찾기
  elHud = document.getElementById('game-hud');
  elNarration = document.getElementById('game-narration');
  elChatLog = document.getElementById('chat-log');
  elInput = document.getElementById('user-input');
  elSend = document.getElementById('send-btn');
  
  if (!elInput || !elSend) {
    console.warn('[game_turn] Input elements not found');
    return;
  }
  
  // 이벤트 리스너 등록
  elSend.addEventListener('click', handleSend);
  elInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      handleSend();
    }
  });
  
  console.log('[game_turn] Initialized');
}

async function callTurnApi(message) {
  if (!gameId) {
    console.error('[game_turn] GAME_ID not set');
    return null;
  }
  
  try {
    // user_info_v2 토큰을 헤더에 추가
    const userInfoV2 = localStorage.getItem('user_info_v2');
    const headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    
    if (userInfoV2) {
      headers['X-User-Info-Token'] = userInfoV2;
    }
    
    const res = await fetch(`${API_BASE_URL}/v1/games/${gameId}/turn`, {
      method: 'POST',
      credentials: 'include',  // 세션 쿠키를 함께 보냄
      headers: headers,
      body: JSON.stringify({ user_message: message }),
    });
    
    if (!res.ok) {
      const errorText = await res.text();
      console.error('[game_turn] TURN API ERROR', res.status, errorText);
      return null;
    }
    
    return await res.json();
  } catch (error) {
    console.error('[game_turn] Network error:', error);
    return null;
  }
}

function appendChatBubble(speakerType, name, text) {
  if (!elChatLog) return;
  
  const div = document.createElement('div');
  div.classList.add('chat-bubble', `chat-${speakerType}`);
  
  const label = name ? `<strong>${name}</strong>: ` : '';
  div.innerHTML = `${label}${escapeHtml(text)}`;
  
  elChatLog.appendChild(div);
  elChatLog.scrollTop = elChatLog.scrollHeight;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function renderHud(userInfo, charactersInfo) {
  if (!elHud) return;
  
  const attrs = userInfo.attributes || {};
  const hp = attrs.hp || {};
  const mp = attrs.mp || {};
  const items = userInfo.items || {};
  
  let html = `
    <div class="hud-section">
      <h3>플레이어</h3>
      <div>HP: ${hp.current || 0} / ${hp.max || 0}</div>
      <div>MP: ${mp.current || 0} / ${mp.max || 0}</div>
      <div>골드: ${items.gold || 0}</div>
      ${items.inventory && items.inventory.length > 0 
        ? `<div>아이템: ${items.inventory.join(', ')}</div>` 
        : ''}
    </div>
  `;
  
  if (charactersInfo && charactersInfo.length > 0) {
    html += '<div class="hud-section"><h3>동료 / NPC</h3>';
    charactersInfo.forEach((c) => {
      const snapshot = c.snapshot || {};
      const name = snapshot.name || '???';
      const a = snapshot.attributes || {};
      const chp = a.hp || {};
      const cmp = a.mp || {};
      const citems = snapshot.items || {};
      
      html += `
        <div class="hud-char">
          <span>${name}</span>
          <span>HP ${chp.current || 0}/${chp.max || 0}</span>
          <span>MP ${cmp.current || 0}/${cmp.max || 0}</span>
          ${citems.gold ? `<span>골드: ${citems.gold}</span>` : ''}
        </div>
      `;
    });
    html += '</div>';
  }
  
  elHud.innerHTML = html;
}

async function handleSend() {
  if (!elInput) return;
  
  const msg = elInput.value.trim();
  if (!msg) return;
  
  // 입력 필드 비우기
  elInput.value = '';
  elInput.disabled = true;
  elSend.disabled = true;
  
  try {
    // 1) 유저 메시지를 채팅창에 먼저 보여줌
    appendChatBubble('user', null, msg);
    
    // 2) API 호출
    const data = await callTurnApi(msg);
    if (!data) {
      appendChatBubble('system', null, '오류가 발생했습니다. 다시 시도해주세요.');
      return;
    }
    
    // 3) 노란 영역: narration
    if (elNarration) {
      elNarration.textContent = data.narration;
    }
    
    // 4) 대화 로그 append
    (data.dialogues || []).forEach((d) => {
      appendChatBubble(d.speaker_type, d.name, d.text);
    });
    
    // 5) HUD 업데이트
    renderHud(data.user_info, data.characters_info);
  } finally {
    elInput.disabled = false;
    elSend.disabled = false;
    if (elInput) elInput.focus();
  }
}

// DOMContentLoaded 시 초기화
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initGameTurn);
} else {
  initGameTurn();
}

