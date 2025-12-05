// API Base URL 공통 함수
function getApiBaseUrl() {
  return window.location.hostname === "arcanaverse.ai" ||
    window.location.hostname === "www.arcanaverse.ai"
    ? "https://api.arcanaverse.ai"
    : "http://localhost:8000";
}

// 토큰 관리
const TOKEN_KEY = 'access_token';
const USER_INFO_KEY = 'user_info_v2';

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function getSessionToken() {
  return window.localStorage.getItem(USER_INFO_KEY);
}

function clearSessionToken() {
  window.localStorage.removeItem(USER_INFO_KEY);
  window.localStorage.removeItem(TOKEN_KEY);
}

// 사용자 정보 가져오기 (세션 검증을 통해)
async function getUserInfo() {
  const userInfoV2 = localStorage.getItem(USER_INFO_KEY);
  if (!userInfoV2) {
    return null;
  }

  try {
    const res = await fetch(`${getApiBaseUrl()}/v1/auth/validate-session`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token: userInfoV2 }),
      credentials: "include",
    });

    if (res.ok) {
      return await res.json();
    }
    return null;
  } catch (err) {
    console.error('Failed to get user info:', err);
    return null;
  }
}

/**
 * 계정 상태 체크
 * - ok: true 면 사용 가능
 * - ok: false 이면 reason 으로 상태 구분
 *   - 'login': 로그인 필요
 *   - 'lock': 계정 차단
 *   - 'use': 사용 불가
 */
async function checkAccountStatus() {
  const token = getToken();
  const info = await getUserInfo();

  console.log('[ACCOUNT] token:', !!token, 'info:', info);

  if (!token) return { ok: false, reason: 'login' };

  if (!info) return { ok: false, reason: 'login' };

  const is_use = info.is_use || false;
  const is_lock = info.is_lock || false;

  console.log('[ACCOUNT] is_use:', is_use, 'is_lock:', is_lock);

  if (is_lock) return { ok: false, reason: 'lock' };
  if (!is_use) return { ok: false, reason: 'use' };

  return { ok: true, reason: null };
}

// 세션 유효성 검사 (메뉴/챗 클릭 전에 공통으로 사용)
async function ensureSessionValid() {
  const token = await getSessionToken();
  if (!token) {
    console.warn("no session token. need login");
    return null;
  }

  try {
    const res = await fetch(`${getApiBaseUrl()}/v1/auth/validate-session`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
      credentials: "include",
    });

    if (!res.ok) {
      clearSessionToken();
      return null;
    }

    const data = await res.json();
    return data;
  } catch (err) {
    console.error("session validate error", err);
    return null;
  }
}

// 채팅창 진입 전에 호출
async function ensureChatAccessible() {
  const session = await ensureSessionValid();
  if (!session) {
    alert("로그인이 필요합니다.");
    return null;
  }

  if (!session.is_use) {
    alert("현재 사용이 불가한 상태입니다.");
    return null;
  }

  if (session.is_lock) {
    alert("현재 계정이 차단된 상태입니다.");
    return null;
  }

  return session;
}

// 인증 헤더 생성 (캐릭터 생성 등에서 사용)
function getAuthHeaders() {
  const headers = {};
  const userInfoV2 = getSessionToken();
  if (userInfoV2) {
    // 백엔드가 Authorization Bearer 또는 X-User-Info-Token 헤더를 읽을 수 있도록
    headers['Authorization'] = `Bearer ${userInfoV2}`;
    headers['X-User-Info-Token'] = userInfoV2;
  }
  return headers;
}

