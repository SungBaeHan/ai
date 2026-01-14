import { useNavigate } from "react-router-dom";

export default function MyPage() {
  const navigate = useNavigate();

  return (
    <div style={{ maxWidth: "1200px", margin: "24px auto 40px", padding: "0 16px" }}>
      <h1 style={{ fontSize: "24px", fontWeight: 700, margin: "8px 0 24px", color: "#f3f4f6" }}>
        My 메뉴
      </h1>

      {/* Profile Section */}
      <div
        style={{
          background: "#111827",
          border: "1px solid #1f2937",
          borderRadius: "14px",
          padding: "24px",
          marginBottom: "20px",
          boxShadow: "0 6px 18px rgba(0,0,0,.25)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "16px", marginBottom: "20px" }}>
          <div
            style={{
              width: "64px",
              height: "64px",
              borderRadius: "50%",
              background: "#1f2937",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "24px",
              color: "#94a3b8",
              border: "2px solid #334155",
            }}
          >
            ?
          </div>
          <div>
            <h2 style={{ margin: "0 0 4px 0", fontSize: "18px", fontWeight: 700, color: "#f3f4f6" }}>
              사용자
            </h2>
            <p style={{ margin: 0, fontSize: "14px", color: "#94a3b8" }}>이메일</p>
          </div>
        </div>
        <button
          onClick={() => {
            // handleLogout logic here
          }}
          style={{
            display: "block",
            width: "100%",
            padding: "12px",
            background: "#7f1d1d",
            border: "1px solid #991b1b",
            borderRadius: "10px",
            color: "#fee2e2",
            fontSize: "14px",
            fontWeight: 600,
            cursor: "pointer",
            transition: "background .15s ease",
            marginTop: "16px",
          }}
        >
          로그아웃
        </button>
      </div>

      {/* Settings List */}
      <div
        style={{
          background: "#111827",
          border: "1px solid #1f2937",
          borderRadius: "14px",
          overflow: "hidden",
          boxShadow: "0 6px 18px rgba(0,0,0,.25)",
        }}
      >
        {/* 페르조나 관리 버튼 - 3개 버튼 제일 위 */}
        <a
          href="#"
          onClick={(e) => {
            e.preventDefault();
            navigate("/my/personas");
          }}
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "16px 20px",
            borderBottom: "1px solid #1f2937",
            cursor: "pointer",
            transition: "background .15s ease",
            color: "#e5e7eb",
            textDecoration: "none",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "#1f2937";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "transparent";
          }}
        >
          <span style={{ fontSize: "14px", fontWeight: 500 }}>페르조나 관리</span>
          <span style={{ color: "#64748b", fontSize: "12px" }}>→</span>
        </a>

        <a
          href="#"
          onClick={(e) => {
            e.preventDefault();
            // showToast('준비중입니다');
          }}
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "16px 20px",
            borderBottom: "1px solid #1f2937",
            cursor: "pointer",
            transition: "background .15s ease",
            color: "#e5e7eb",
            textDecoration: "none",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "#1f2937";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "transparent";
          }}
        >
          <span style={{ fontSize: "14px", fontWeight: 500 }}>계정 설정</span>
          <span style={{ color: "#64748b", fontSize: "12px" }}>→</span>
        </a>

        <a
          href="#"
          onClick={(e) => {
            e.preventDefault();
            // showToast('준비중입니다');
          }}
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "16px 20px",
            borderBottom: "1px solid #1f2937",
            cursor: "pointer",
            transition: "background .15s ease",
            color: "#e5e7eb",
            textDecoration: "none",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "#1f2937";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "transparent";
          }}
        >
          <span style={{ fontSize: "14px", fontWeight: 500 }}>알림 설정</span>
          <span style={{ color: "#64748b", fontSize: "12px" }}>→</span>
        </a>

        <a
          href="#"
          onClick={(e) => {
            e.preventDefault();
            // showToast('준비중입니다');
          }}
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "16px 20px",
            borderBottom: "none",
            cursor: "pointer",
            transition: "background .15s ease",
            color: "#e5e7eb",
            textDecoration: "none",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "#1f2937";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "transparent";
          }}
        >
          <span style={{ fontSize: "14px", fontWeight: 500 }}>개인정보 처리방침</span>
          <span style={{ color: "#64748b", fontSize: "12px" }}>→</span>
        </a>
      </div>
    </div>
  );
}
