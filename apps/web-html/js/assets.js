/**
 * R2 전체 URL 또는 절대 URL을 받아서
 * `/assets/...` 이하의 상대 경로만 반환하는 함수.
 * 이미 상대 경로라면 그대로 반환한다.
 * 
 * @param {string|null|undefined} url - 정규화할 이미지 URL
 * @returns {string|null} 정규화된 경로 또는 null
 */
function normalizeAssetPath(url) {
  if (!url) return null;
  
  // 이미 /assets/ 로 시작하는 경우 → 그대로 사용
  if (url.startsWith('/assets/')) {
    return url;
  }
  
  // 전체 URL(https://...)에 /assets/ 가 포함된 경우 → 그 뒤부터 잘라서 사용
  const assetsIndex = url.indexOf('/assets/');
  if (assetsIndex >= 0) {
    return url.slice(assetsIndex);
  }
  
  try {
    // 기타 http/https URL인 경우 → pathname만 사용
    if (url.startsWith('http://') || url.startsWith('https://')) {
      const u = new URL(url);
      return u.pathname || null;
    }
  } catch (e) {
    // URL 파싱 실패 시 → 원본 유지
    return url;
  }
  
  return url;
}

