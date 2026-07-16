"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";

export type AiProgressVariant = "search" | "inspection" | "quotation";

type StepDef = {
  title: string;
  detail: string;
  dwellMs: number;
};

const VARIANTS: Record<
  AiProgressVariant,
  { headline: string; etaLabel: string; steps: StepDef[] }
> = {
  search: {
    headline: "유사 사례를 찾고 있어요",
    etaLabel: "보통 40~80초 걸려요",
    steps: [
      { title: "요청 접수", detail: "질문을 분석할 준비를 마쳤어요", dwellMs: 2500 },
      { title: "AS 사례 검색", detail: "과거 정비·고장 사례를 모으고 있어요", dwellMs: 12000 },
      { title: "관련 근거 정리", detail: "비슷한 증상을 골라 정리 중이에요", dwellMs: 14000 },
      { title: "AI 답변 작성", detail: "원인·점검 순서를 문장으로 쓰고 있어요", dwellMs: 28000 },
      { title: "결과 검토", detail: "답변을 마지막으로 다듬고 있어요", dwellMs: 12000 },
    ],
  },
  inspection: {
    headline: "점검 초안을 만들고 있어요",
    etaLabel: "보통 30~70초 걸려요",
    steps: [
      { title: "체크리스트 확인", detail: "입력하신 점검 항목을 읽고 있어요", dwellMs: 2500 },
      { title: "유사 점검 조회", detail: "비슷한 현장 기록을 참고하고 있어요", dwellMs: 12000 },
      { title: "위험도·조치 분석", detail: "이상 항목 기준으로 우선순위를 정해요", dwellMs: 16000 },
      { title: "초안 작성", detail: "조치 가이드 문장을 작성 중이에요", dwellMs: 26000 },
      { title: "최종 정리", detail: "요약과 권장 조치를 맞추고 있어요", dwellMs: 10000 },
    ],
  },
  quotation: {
    headline: "견적 초안을 준비하고 있어요",
    etaLabel: "보통 25~50초 걸려요",
    steps: [
      { title: "증상 분석", detail: "고장 내용을 부품 관점으로 해석해요", dwellMs: 2500 },
      { title: "부품 매핑", detail: "AS 단가표와 사례를 맞춰 보고 있어요", dwellMs: 10000 },
      { title: "공임·출장비 산출", detail: "작업 시간과 비용을 계산 중이에요", dwellMs: 10000 },
      { title: "견적서 작성", detail: "금액과 내역을 정리하고 있어요", dwellMs: 18000 },
      { title: "금액 검증", detail: "합계와 항목을 마지막으로 확인해요", dwellMs: 8000 },
    ],
  },
};

function formatElapsed(ms: number): string {
  const sec = Math.floor(ms / 1000);
  if (sec < 60) return `${sec}초`;
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${m}분 ${s.toString().padStart(2, "0")}초`;
}

export default function AiProgressSteps({
  active,
  variant,
}: {
  active: boolean;
  variant: AiProgressVariant;
}) {
  const config = VARIANTS[variant];
  const lastIndex = config.steps.length - 1;
  const [stepIndex, setStepIndex] = useState(0);
  const [elapsedMs, setElapsedMs] = useState(0);
  const [visible, setVisible] = useState(false);
  const [finishing, setFinishing] = useState(false);
  const wasActive = useRef(false);

  useEffect(() => {
    if (active) {
      wasActive.current = true;
      setVisible(true);
      setFinishing(false);
      setStepIndex(0);
      setElapsedMs(0);

      const started = performance.now();
      const tick = window.setInterval(() => {
        setElapsedMs(Math.floor(performance.now() - started));
      }, 250);

      let idx = 0;
      let timer = 0;
      const advance = () => {
        const dwell = config.steps[idx]?.dwellMs ?? 8000;
        timer = window.setTimeout(() => {
          // Hold on the last working step until the request completes
          if (idx >= lastIndex - 1) return;
          idx += 1;
          setStepIndex(idx);
          advance();
        }, dwell);
      };
      advance();

      return () => {
        window.clearInterval(tick);
        window.clearTimeout(timer);
      };
    }

    if (wasActive.current) {
      wasActive.current = false;
      setStepIndex(lastIndex);
      setFinishing(true);
      const hide = window.setTimeout(() => {
        setFinishing(false);
        setVisible(false);
        setElapsedMs(0);
        setStepIndex(0);
      }, 700);
      return () => window.clearTimeout(hide);
    }

    setVisible(false);
    setFinishing(false);
  }, [active, config.steps, lastIndex]);

  const progressPct = useMemo(() => {
    if (finishing) return 100;
    if (!visible) return 0;
    const base = ((stepIndex + 0.4) / config.steps.length) * 100;
    return Math.min(90, Math.max(10, base));
  }, [finishing, visible, stepIndex, config.steps.length]);

  if (!visible) return null;

  const current = config.steps[Math.min(stepIndex, lastIndex)];

  return (
    <div className="ai-progress" role="status" aria-live="polite" aria-busy={active}>
      <div className="ai-progress__orb" aria-hidden />
      <p className="ai-progress__eyebrow">{config.headline}</p>
      <h3 className="ai-progress__title" key={`${finishing}-${current.title}`}>
        {finishing ? "준비됐어요" : current.title}
      </h3>
      <p className="ai-progress__detail" key={`${finishing}-${current.detail}`}>
        {finishing ? "결과를 바로 확인할 수 있어요" : current.detail}
      </p>

      <div className="ai-progress__meter" aria-hidden>
        <div className="ai-progress__meter-fill" style={{ width: `${progressPct}%` }} />
      </div>

      <div className="ai-progress__meta">
        <span>{formatElapsed(elapsedMs)} 경과</span>
        <span>{config.etaLabel}</span>
      </div>

      <ol className="ai-progress__steps">
        {config.steps.map((step, i) => {
          const state =
            finishing || i < stepIndex ? "done" : i === stepIndex ? "active" : "pending";
          return (
            <li key={step.title} className={`ai-progress__step ai-progress__step--${state}`}>
              <span className="ai-progress__marker" aria-hidden>
                {state === "done" ? (
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                    <path
                      d="M3 7.2 5.8 10 11 4"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                ) : state === "active" ? (
                  <span className="ai-progress__pulse" />
                ) : (
                  <span className="ai-progress__dot" />
                )}
              </span>
              <span className="ai-progress__step-label">{step.title}</span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
