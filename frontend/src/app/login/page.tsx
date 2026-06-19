"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { LogIn, Eye, EyeOff } from "lucide-react";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const formData = new URLSearchParams();
      formData.append("username", username);
      formData.append("password", password);

      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: formData,
      });

      if (!res.ok) {
        throw new Error("아이디 또는 비밀번호가 올바르지 않습니다.");
      }

      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "로그인 중 오류가 발생했습니다.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "#0f172a" }}>
      <div style={{ width: "100%", maxWidth: "400px", padding: "32px", background: "rgba(30, 41, 59, 0.8)", borderRadius: "16px", border: "1px solid rgba(255, 255, 255, 0.1)", boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.5)" }}>
        <div style={{ textAlign: "center", marginBottom: "32px" }}>
          <div style={{ margin: "0 auto 16px", display: "flex", alignItems: "center", justifyContent: "center", width: "48px", height: "48px", borderRadius: "50%", background: "rgba(6, 182, 212, 0.1)" }}>
            <LogIn size={24} color="#06b6d4" />
          </div>
          <h2 style={{ fontSize: "24px", fontWeight: "bold", color: "#ffffff", margin: 0 }}>CSAutobot 로그인</h2>
          <p style={{ marginTop: "8px", fontSize: "14px", color: "#94a3b8" }}>
            시스템에 접근하려면 관리자 계정으로 로그인하세요.
          </p>
        </div>

        <form onSubmit={handleLogin} style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {error && (
            <div style={{ padding: "12px", background: "rgba(239, 68, 68, 0.1)", color: "#ef4444", borderRadius: "8px", fontSize: "14px", textAlign: "center" }}>
              {error}
            </div>
          )}
          
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div>
              <label htmlFor="username" style={{ display: "block", fontSize: "14px", color: "#cbd5e1", marginBottom: "8px", fontWeight: 500 }}>아이디</label>
              <input
                id="username"
                name="username"
                type="text"
                required
                placeholder="아이디를 입력하세요"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                style={{ width: "100%", padding: "12px 16px", background: "#0f172a", border: "1px solid rgba(255, 255, 255, 0.1)", borderRadius: "8px", color: "#ffffff", fontSize: "14px", outline: "none", boxSizing: "border-box" }}
              />
            </div>
            
            <div style={{ position: "relative" }}>
              <label htmlFor="password" style={{ display: "block", fontSize: "14px", color: "#cbd5e1", marginBottom: "8px", fontWeight: 500 }}>비밀번호</label>
              <div style={{ position: "relative" }}>
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  required
                  placeholder="비밀번호를 입력하세요"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  style={{ width: "100%", padding: "12px 40px 12px 16px", background: "#0f172a", border: "1px solid rgba(255, 255, 255, 0.1)", borderRadius: "8px", color: "#ffffff", fontSize: "14px", outline: "none", boxSizing: "border-box" }}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={{ position: "absolute", right: "12px", top: "50%", transform: "translateY(-50%)", background: "none", border: "none", padding: 0, cursor: "pointer", color: "#64748b", display: "flex", alignItems: "center" }}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            style={{ width: "100%", padding: "12px", background: "#06b6d4", color: "#ffffff", border: "none", borderRadius: "8px", fontSize: "16px", fontWeight: "bold", cursor: isLoading ? "not-allowed" : "pointer", opacity: isLoading ? 0.7 : 1, transition: "opacity 0.2s" }}
          >
            {isLoading ? "로그인 중..." : "로그인"}
          </button>
        </form>
      </div>
    </div>
  );
}
