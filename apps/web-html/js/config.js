// apps/web-html/js/config.js
// NOTE: API 베이스 URL 및 이미지 베이스 URL 설정
// hostname에 따라 프로덕션/로컬 개발 환경을 자동으로 감지합니다.
(function () {
  const host = (typeof window !== 'undefined' && window.location && window.location.hostname) || '';

  const isProd = host === 'arcanaverse.ai' || host === 'www.arcanaverse.ai';

  const API_BASE = isProd
    ? 'https://api.arcanaverse.ai'
    : 'http://localhost:8000';

  const API_BASE_URL = API_BASE;

  const IMAGE_BASE = isProd
    ? 'https://pub-09b0f3cad63f4891868948d43f19febf.r2.dev/assets'
    : 'http://localhost:8000/assets';

  if (typeof window !== 'undefined') {
    window.API_BASE = API_BASE;
    window.API_BASE_URL = API_BASE_URL;
    window.IMAGE_BASE = IMAGE_BASE;
  }
})();
