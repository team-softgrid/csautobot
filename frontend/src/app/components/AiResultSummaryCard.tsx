"use client";

import React from "react";

export type AiSummaryRow = {
  label: string;
  value: React.ReactNode;
};

type Props = {
  /** e.g. "🔍 AI 고장 진단 요약" */
  title: string;
  rows: AiSummaryRow[];
  /** Optional chip/badge on the right of the title row */
  badge?: React.ReactNode;
  footer?: React.ReactNode;
};

/**
 * Shared result card matching quotation "AI 고장 진단 요약" visibility style.
 */
export default function AiResultSummaryCard({ title, rows, badge, footer }: Props) {
  return (
    <section className="glass-panel" style={{ padding: "24px" }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "12px",
          marginBottom: "12px",
        }}
      >
        <h3
          style={{
            fontSize: "16px",
            fontWeight: "bold",
            margin: 0,
            color: "#06b6d4",
          }}
        >
          {title}
        </h3>
        {badge}
      </div>

      <div style={{ fontSize: "14px", lineHeight: "1.7", color: "#cbd5e1" }}>
        {rows.map((row, idx) => (
          <div
            key={`${row.label}-${idx}`}
            style={{
              marginBottom: idx === rows.length - 1 && !footer ? 0 : "10px",
            }}
          >
            <strong style={{ color: "#f8fafc" }}>{row.label}:</strong>{" "}
            <span style={{ color: "#cbd5e1" }}>{row.value}</span>
          </div>
        ))}
      </div>

      {footer ? <div style={{ marginTop: "14px" }}>{footer}</div> : null}
    </section>
  );
}

export function SummaryList({
  items,
  ordered = false,
}: {
  items: string[];
  ordered?: boolean;
}) {
  if (!items.length) return <span style={{ color: "#64748b" }}>해당 없음</span>;
  const Tag = ordered ? "ol" : "ul";
  return (
    <Tag
      style={{
        margin: "6px 0 0",
        paddingLeft: "20px",
        display: "flex",
        flexDirection: "column",
        gap: "4px",
      }}
    >
      {items.map((item, i) => (
        <li key={i}>{item}</li>
      ))}
    </Tag>
  );
}
