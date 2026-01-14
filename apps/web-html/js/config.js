// apps/web-html/js/config.js
// NOTE: API 베이스 URL 및 이미지 베이스 URL 설정
// hostname에 따라 프로덕션/로컬 개발 환경을 자동으로 감지합니다.
(function () {
  const host = (typeof window !== 'undefined' && window.location && window.location.hostname) || '';

  const isProd = host === 'arcanaverse.ai' || host === 'www.arcanaverse.ai';

  const API_BASE = isProd
    ? 'https://api.arcanaverse.ai'
    : 'http://localhost:8000';

  const IMAGE_BASE = isProd
    ? 'https://pub-09b0f3cad63f4891868948d43f19febf.r2.dev/assets'
    : 'http://localhost:8000/assets';

  if (typeof window !== 'undefined') {
    // window.API_BASE_URL이 이미 설정되어 있으면 덮어쓰지 않음
    if (!window.API_BASE_URL) {
      window.API_BASE = API_BASE;
      window.API_BASE_URL = API_BASE;  // API_BASE와 동일 (이미 /api 없음)
    }
    window.IMAGE_BASE = IMAGE_BASE;
    
    // === anon_id 초기화 ===
    function initAnonId() {
      const STORAGE_KEY = 'anon_id';
      let anonId = localStorage.getItem(STORAGE_KEY);
      if (!anonId) {
        // UUID v4 형식으로 생성 (간단 버전)
        anonId = 'anon_' + Date.now().toString(36) + '_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem(STORAGE_KEY, anonId);
      }
      window.ANON_ID = anonId;
      return anonId;
    }
    
    window.ANON_ID = initAnonId();
    
    // === 공통 fetch wrapper (X-Anon-Id 자동 추가) ===
    const originalFetch = window.fetch;
    window.apiFetch = function(url, options = {}) {
      const headers = new Headers(options.headers || {});
      if (window.ANON_ID) {
        headers.set('X-Anon-Id', window.ANON_ID);
      }
      options.headers = headers;
      return originalFetch(url, options);
    };
    
    // === 이벤트 상수 ===
    window.EVENT = {
      PAGE_VIEW: 'page_view',
      LOGIN_START: 'login_start',
      LOGIN_SUCCESS: 'login_success',
      LOGOUT: 'logout',
      PERSONA_SELECT: 'persona_select',
      CHAT_OPEN: 'chat_open',
      CHAT_SEND: 'chat_send',
      CHAT_RESPONSE_START: 'chat_response_start',
      CHAT_RESPONSE_DONE: 'chat_response_done',
      CHAT_RESPONSE_FAIL: 'chat_response_fail',
      TOKEN_DEBIT: 'token_debit',
      PREVIEW_LOCKED: 'preview_locked',
      TOKEN_INSUFFICIENT_BLOCK: 'token_insufficient_block',
    };
    
    // === 이벤트 로깅 함수 ===
    window.logEvent = async function(name, source, payload = {}, opts = {}) {
      try {
        const eventData = {
          name: name,
          source: source,
          path: window.location.pathname,
          session_id: opts.session_id || null,
          entity_id: opts.entity_id || null,
          request_id: opts.request_id || null,
          payload: payload,
        };
        
        await window.apiFetch(`${API_BASE}/v1/logs/event`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(eventData),
        }).catch(err => {
          console.warn('[LOG] Failed to send event:', err);
        });
      } catch (err) {
        console.warn('[LOG] Event logging error:', err);
      }
    };
    
    // === 클라이언트 에러 전송 함수 ===
    window.sendClientError = async function(payload) {
      try {
        const errorData = {
          kind: 'client',
          source: payload.source || 'window.onerror',
          message: payload.message || '',
          stack: payload.stack || null,
          path: window.location.pathname,
          meta: payload.meta || {},
        };
        
        await window.apiFetch(`${API_BASE}/v1/logs/error`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(errorData),
        }).catch(err => {
          console.warn('[LOG] Failed to send error:', err);
        });
      } catch (err) {
        console.warn('[LOG] Error logging error:', err);
      }
    };
    
    // === 전역 에러 핸들러 ===
    window.addEventListener('error', function(event) {
      window.sendClientError({
        source: 'window.onerror',
        message: event.message || 'Unknown error',
        stack: event.error ? event.error.stack : null,
        meta: {
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno,
        },
      });
    });
    
    window.addEventListener('unhandledrejection', function(event) {
      window.sendClientError({
        source: 'unhandledrejection',
        message: event.reason ? String(event.reason) : 'Unhandled promise rejection',
        stack: event.reason && event.reason.stack ? event.reason.stack : null,
        meta: {},
      });
    });
    
    // === GLOBAL FETCH PATCH: always attach X-Anon-Id ===
    (function patchFetchWithAnonId() {
      if (window.__FETCH_ANON_PATCHED__) return;
      window.__FETCH_ANON_PATCHED__ = true;

      if (!window.fetch) return;
      const _fetch = window.fetch.bind(window);

      window.fetch = function(input, init = {}) {
        const headers = new Headers(init.headers || {});
        const anonId = window.ANON_ID || localStorage.getItem('anon_id') || 'missing';
        headers.set('X-Anon-Id', anonId);
        return _fetch(input, { ...init, headers });
      };
    })();
    
    // === apiFetch도 동일 헤더 보장 (이중 안전망) ===
    if (window.apiFetch) {
      const originalApiFetch = window.apiFetch;
      window.apiFetch = function(url, options = {}) {
        const headers = new Headers(options.headers || {});
        const anonId = window.ANON_ID || localStorage.getItem('anon_id') || 'missing';
        headers.set('X-Anon-Id', anonId);
        options.headers = headers;
        return originalApiFetch(url, options);
      };
    }
  }
})();
