"use client";

import React, { useState } from "react";

const PLAN_OPTIONS = [
  "파일럿 (스탠다드)",
  "파일럿 (프리미엄)",
  "Pro 구독",
  "Enterprise 구독",
  "데모 요청",
];

const inputStyle: React.CSSProperties = {
  background: "rgba(255,255,255,0.03)",
  border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: "8px",
  padding: "0.7rem 1rem",
  color: "#f8fafc",
  fontSize: "0.88rem",
  outline: "none",
  width: "100%",
  boxSizing: "border-box",
};

export default function ContactForm() {
  const [companyName, setCompanyName] = useState("");
  const [contactName, setContactName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [message, setMessage] = useState("");
  const [plans, setPlans] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<{ type: "ok" | "err"; text: string } | null>(null);

  const togglePlan = (plan: string) => {
    setPlans((prev) =>
      prev.includes(plan) ? prev.filter((p) => p !== plan) : [...prev, plan]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFeedback(null);
    setSubmitting(true);
    try {
      const res = await fetch("/api/v1/leads", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company_name: companyName,
          contact_name: contactName,
          email,
          phone: phone || null,
          interest_plans: plans,
          message: message || null,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = data.detail;
        const msg =
          typeof detail === "string"
            ? detail
            : Array.isArray(detail)
              ? detail.map((d: { msg?: string }) => d.msg).join(", ")
              : "요청 처리에 실패했습니다.";
        throw new Error(msg);
      }
      setFeedback({ type: "ok", text: data.message || "접수되었습니다." });
      setCompanyName("");
      setContactName("");
      setEmail("");
      setPhone("");
      setMessage("");
      setPlans([]);
    } catch (err) {
      setFeedback({
        type: "err",
        text: err instanceof Error ? err.message : "요청 처리에 실패했습니다.",
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      style={{
        background: "rgba(255,255,255,0.02)",
        border: "1px solid rgba(255,255,255,0.08)",
        borderRadius: "24px",
        padding: "3rem",
        marginBottom: "2rem",
      }}
    >
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
          gap: "1.5rem",
          marginBottom: "1.5rem",
        }}
      >
        {[
          { label: "회사명", value: companyName, setter: setCompanyName, placeholder: "예) (주)충전운영사", required: true },
          { label: "담당자명", value: contactName, setter: setContactName, placeholder: "예) 홍길동", required: true },
          { label: "이메일", value: email, setter: setEmail, placeholder: "예) contact@company.com", required: true, type: "email" },
          { label: "연락처", value: phone, setter: setPhone, placeholder: "예) 010-0000-0000", required: false },
        ].map((field) => (
          <div key={field.label} style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
            <label style={{ fontSize: "0.8rem", color: "#64748b", fontWeight: 600 }}>
              {field.label}
              {field.required && <span style={{ color: "#06b6d4" }}> *</span>}
            </label>
            <input
              type={field.type || "text"}
              required={field.required}
              value={field.value}
              onChange={(e) => field.setter(e.target.value)}
              placeholder={field.placeholder}
              style={inputStyle}
            />
          </div>
        ))}
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem", marginBottom: "1.5rem" }}>
        <label style={{ fontSize: "0.8rem", color: "#64748b", fontWeight: 600 }}>관심 플랜</label>
        <div style={{ display: "flex", gap: "0.8rem", flexWrap: "wrap" }}>
          {PLAN_OPTIONS.map((option) => (
            <label
              key={option}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.4rem",
                cursor: "pointer",
                fontSize: "0.85rem",
                color: plans.includes(option) ? "#06b6d4" : "#94a3b8",
              }}
            >
              <input
                type="checkbox"
                checked={plans.includes(option)}
                onChange={() => togglePlan(option)}
                style={{ accentColor: "#06b6d4" }}
              />
              {option}
            </label>
          ))}
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem", marginBottom: "1.5rem" }}>
        <label style={{ fontSize: "0.8rem", color: "#64748b", fontWeight: 600 }}>문의 내용 (선택)</label>
        <textarea
          rows={3}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="운영 현장 규모, 충전기 대수, 주요 고민 등을 자유롭게 적어주세요."
          style={{ ...inputStyle, resize: "vertical", fontFamily: "inherit" }}
        />
      </div>

      {feedback && (
        <p
          style={{
            marginBottom: "1rem",
            padding: "0.75rem 1rem",
            borderRadius: "8px",
            fontSize: "0.88rem",
            background:
              feedback.type === "ok"
                ? "rgba(16,185,129,0.1)"
                : "rgba(239,68,68,0.1)",
            color: feedback.type === "ok" ? "#10b981" : "#ef4444",
            border: `1px solid ${feedback.type === "ok" ? "rgba(16,185,129,0.3)" : "rgba(239,68,68,0.3)"}`,
          }}
        >
          {feedback.text}
        </p>
      )}

      <button
        type="submit"
        disabled={submitting}
        style={{
          width: "100%",
          padding: "1rem",
          borderRadius: "12px",
          border: "none",
          background: submitting
            ? "rgba(6,182,212,0.4)"
            : "linear-gradient(135deg, #3b82f6, #06b6d4)",
          color: "#000",
          fontWeight: 700,
          fontSize: "1rem",
          cursor: submitting ? "not-allowed" : "pointer",
        }}
      >
        {submitting ? "접수 중..." : "도입 상담 요청하기 →"}
      </button>

      <p style={{ textAlign: "center", fontSize: "0.75rem", color: "#334155", marginTop: "1rem" }}>
        또는{" "}
        <a href="mailto:contact@csautobot.com" style={{ color: "#94a3b8" }}>
          contact@csautobot.com
        </a>
        으로 직접 이메일을 보내주세요. 영업일 1~2일 내 회신합니다.
      </p>
    </form>
  );
}
