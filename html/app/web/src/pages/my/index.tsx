import { useNavigate } from "react-router-dom";

export default function MyPage() {
  const navigate = useNavigate();

  // TODO: Add your existing component code here
  // This is a placeholder structure - replace with your actual component

  return (
    <div>
      {/* TODO: Add your existing JSX here */}
      <button
        onClick={() => navigate("/my/personas")}
        style={{
          width: "100%",
          marginTop: "12px",
          padding: "12px",
          borderRadius: "8px",
          background: "linear-gradient(90deg, #3b82f6, #6366f1)",
          color: "#fff",
          fontWeight: 600,
          border: "none",
          cursor: "pointer",
        }}
      >
        페르조나 관리
      </button>
    </div>
  );
}
