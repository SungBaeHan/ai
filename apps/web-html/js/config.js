// apps/web-html/js/config.js
// NOTE: API 베이스 URL 및 이미지 베이스 URL 설정
// hostname에 따라 프로덕션/로컬 개발 환경을 자동으로 감지합니다.
(function () {
  const host = (typeof window !== 'undefined' && window.location && window.location.hostname) || '';

  const isProd = host === 'arcanaverse.ai' || host === 'www.arcanaverse.ai' || host === 'trpg.arcanaverse.ai';

  const API_BASE = isProd
    ? 'https://api.arcanaverse.ai'
    : 'http://localhost:8000';

  // Asset Base URL (이미지 CDN)
  // 기본값: https://img.arcanaverse.ai
  // 환경변수나 서버 설정에서 주입 가능하도록 설계
  const ASSET_BASE_URL = (typeof window !== 'undefined' && window.__ASSET_BASE_URL__) 
    ? window.__ASSET_BASE_URL__
    : (isProd 
      ? 'https://img.arcanaverse.ai'
      : 'http://localhost:8000');

  if (typeof window !== 'undefined') {
    // window.API_BASE_URL이 이미 설정되어 있으면 덮어쓰지 않음
    if (!window.API_BASE_URL) {
      window.API_BASE = API_BASE;
      window.API_BASE_URL = API_BASE;  // API_BASE와 동일 (이미 /api 없음)
    }
    // ASSET_BASE_URL 설정 (하위 호환을 위해 IMAGE_BASE도 유지)
    window.ASSET_BASE_URL = ASSET_BASE_URL;
    window.IMAGE_BASE = ASSET_BASE_URL + '/assets';  // 하위 호환
    
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
    
    // === GLOBAL FETCH PATCH: always attach X-Anon-Id + r2.dev URL filtering ===
    // 모든 fetch() 호출에 자동으로 X-Anon-Id 헤더 추가 및 응답에서 r2.dev URL 필터링
    // initAnonId() 실행 이후, 파일 맨 아래에 위치하여 모든 코드에서 적용됨
    (function patchFetchWithAnonId() {
      if (window.__FETCH_ANON_PATCHED__) return;
      window.__FETCH_ANON_PATCHED__ = true;

      if (!window.fetch) return;
      const _fetch = window.fetch.bind(window);

      window.fetch = function(input, init = {}) {
        const headers = new Headers(init.headers || {});
        const anonId = window.ANON_ID || localStorage.getItem('anon_id') || 'missing';
        headers.set('X-Anon-Id', anonId);
        
        return _fetch(input, { ...init, headers }).then(async (response) => {
          // JSON 응답인 경우 r2.dev URL 필터링
          const contentType = response.headers.get('content-type');
          if (contentType && contentType.includes('application/json')) {
            try {
              const clonedResponse = response.clone();
              const jsonData = await clonedResponse.json();
              const normalizedData = window.normalizeApiResponse ? window.normalizeApiResponse(jsonData) : jsonData;
              
              // 새로운 Response 객체 생성
              return new Response(JSON.stringify(normalizedData), {
                status: response.status,
                statusText: response.statusText,
                headers: response.headers,
              });
            } catch (e) {
              // JSON 파싱 실패 시 원본 응답 반환
              return response;
            }
          }
          return response;
        });
      };
    })();
    
    // === r2.dev URL 차단 및 정규화 함수 ===
    window.normalizeAssetUrl = function(url) {
      if (!url) return url;
      // r2.dev URL을 강제로 img.arcanaverse.ai로 치환
      if (url.includes('r2.dev') || url.includes('cloudflarestorage.com')) {
        console.error('🚨 r2.dev image URL blocked and normalized:', url);
        // r2.dev URL을 img.arcanaverse.ai로 치환
        const assetBase = window.ASSET_BASE_URL || ASSET_BASE_URL || 'https://img.arcanaverse.ai';
        // URL에서 경로 부분만 추출
        const urlObj = new URL(url);
        return assetBase + urlObj.pathname + urlObj.search;
      }
      return url;
    };
    
    // === Asset URL 빌더 유틸 함수 ===
    window.buildAssetUrl = function(path) {
      if (!path) return '';
      // 이미 전체 URL이면 r2.dev 차단 후 반환
      if (path.startsWith('http://') || path.startsWith('https://')) {
        return window.normalizeAssetUrl(path);
      }
      // path 정규화: 앞뒤 슬래시 처리
      const base = window.ASSET_BASE_URL || ASSET_BASE_URL || 'https://img.arcanaverse.ai';
      const normalizedPath = path.startsWith('/') ? path : '/' + path;
      return base + normalizedPath;
    };
    
    // === API 응답에서 이미지 URL 필터링 함수 ===
    window.normalizeApiResponse = function(obj) {
      if (!obj || typeof obj !== 'object') return obj;
      if (Array.isArray(obj)) {
        return obj.map(item => window.normalizeApiResponse(item));
      }
      const normalized = {};
      for (const key in obj) {
        if (obj.hasOwnProperty(key)) {
          const value = obj[key];
          // image_url, thumbnail, background_image 등의 필드 정규화
          if ((key.includes('image') || key.includes('thumbnail') || key.includes('background')) && 
              typeof value === 'string' && value.includes('r2.dev')) {
            normalized[key] = window.normalizeAssetUrl(value);
          } else if (typeof value === 'object' && value !== null) {
            normalized[key] = window.normalizeApiResponse(value);
          } else {
            normalized[key] = value;
          }
        }
      }
      return normalized;
    };
    
    // === apiFetch도 동일 헤더 보장 (이중 안전망) ===
    // apiFetch는 이미 패치된 fetch를 사용하므로 추가 헤더 설정 불필요하지만,
    // 명시적으로 보장하기 위해 유지
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
