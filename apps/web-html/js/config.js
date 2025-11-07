// apps/web-html/js/config.js
// NOTE: Cloudflare Pages(프론트) → Render(API) 절대경로 기본값.
// 필요 시 배포 환경에 맞춰 이 값만 바꾸면 됩니다.
(function () {
  if (typeof window !== 'undefined' && !window.API_BASE_URL) {
    window.API_BASE_URL = 'https://arcanaverse.onrender.com';
  }
})();

