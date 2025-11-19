// apps/web-html/js/config.js
// NOTE: API 베이스 URL 설정
// 모든 프론트 코드에서 이 값을 사용합니다.
(function () {
  if (typeof window !== 'undefined') {
    // API_BASE_URL: window.API_BASE_URL과 호환성을 위해 유지
    if (!window.API_BASE_URL) {
      window.API_BASE_URL = 'https://api.arcanaverse.ai';
    }
    // API_BASE: 간단한 별칭 (하위 호환성)
    if (!window.API_BASE) {
      window.API_BASE = window.API_BASE_URL;
    }
  }
})();

