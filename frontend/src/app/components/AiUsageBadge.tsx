"use client";

import React from "react";

export type AiUsageLike = {
  model_label?: string | null;
  provider?: string | null;
  model_name?: string | null;
  input_tokens?: number | null;
  output_tokens?: number | null;
  total_tokens?: number | null;
  latency_ms?: number | null;
  generation_path?: string | null;
  fallback_provider?: string | null;
};

function formatLatency(ms: number | null | undefined): string {
  if (ms == null || ms <= 0) return "-";
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function formatTokens(n: number | null | undefined): string {
  if (n == null || n <= 0) return "0";
  return n.toLocaleString("ko-KR");
}

/** Compact badge showing model / tokens / latency after an AI call. */
export default function AiUsageBadge({
  usage,
  fallbackModel,
}: {
  usage?: AiUsageLike | null;
  fallbackModel?: string | null;
}) {
  if (!usage && !fallbackModel) return null;

  const label = usage?.model_label || fallbackModel || "-";
  const inputTok = usage?.input_tokens ?? 0;
  const outputTok = usage?.output_tokens ?? 0;
  const totalTok =
    usage?.total_tokens && usage.total_tokens > 0
      ? usage.total_tokens
      : inputTok + outputTok;
  const path = usage?.generation_path;
  const isLlm = !path || path === "llm";

  return (
    <div
      style={{
        background: "rgba(16, 185, 129, 0.08)",
        border: "1px solid #10b981",
        borderRadius: "8px",
        padding: "12px 16px",
        color: "#6ee7b7",
        fontSize: "13px",
        display: "flex",
        flexWrap: "wrap",
        gap: "12px 20px",
        alignItems: "center",
      }}
    >
      <span>
        ✓ 모델: <strong style={{ fontFamily: "monospace", color: "#a7f3d0" }}>{label}</strong>
      </span>
      {isLlm ? (
        <>
          <span>
            토큰:{" "}
            <strong style={{ color: "#a7f3d0" }}>
              {formatTokens(totalTok)}
            </strong>
            <span style={{ color: "#94a3b8", marginLeft: 6 }}>
              (in {formatTokens(inputTok)} / out {formatTokens(outputTok)})
            </span>
          </span>
          <span>
            응답시간:{" "}
            <strong style={{ color: "#a7f3d0" }}>{formatLatency(usage?.latency_ms)}</strong>
          </span>
        </>
      ) : (
        <span style={{ color: "#94a3b8" }}>
          {path === "faq-shortcut" ? "FAQ 단축 경로 — LLM 미호출" : "오프라인 규칙 — LLM 미호출"}
        </span>
      )}
      {usage?.fallback_provider && (
        <span style={{ color: "#fbbf24" }}>fallback: {usage.fallback_provider}</span>
      )}
    </div>
  );
}
