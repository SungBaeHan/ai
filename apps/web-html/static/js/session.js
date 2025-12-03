async function getSessionToken() {
  return window.localStorage.getItem("user_info_v2");
}

function clearSessionToken() {
  window.localStorage.removeItem("user_info_v2");
  window.localStorage.removeItem("access_token");
}

// 세션 유효성 검사 (메뉴/챗 클릭 전에 공통으로 사용)
async function ensureSessionValid() {
  const token = await getSessionToken();
  if (!token) {
    console.warn("no session token. need login");
    return null;
  }

  try {
    const API_BASE_URL =
      window.location.hostname === "arcanaverse.ai" ||
      window.location.hostname === "www.arcanaverse.ai"
        ? "https://api.arcanaverse.ai"
        : "http://localhost:8000";

    const res = await fetch(`${API_BASE_URL}/v1/auth/validate-session`, {
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

