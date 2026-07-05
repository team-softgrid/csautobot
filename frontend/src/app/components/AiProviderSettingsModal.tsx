"use client";

import React, { useEffect, useState } from "react";
import {
  AI_PROVIDER_INFO,
  AI_PROVIDER_ORDER,
  AI_SELECTION_INFO,
  DEFAULT_AI_CONFIG,
  isAIProvider,
  loadAIConfig,
  saveAIConfig,
  type AIProvider,
  type AISelectionMode,
  type StoredAIConfig,
} from "../ai-config";

interface Props {
  open: boolean;
  onClose: () => void;
  onSaved?: (config: StoredAIConfig) => void;
}

export default function AiProviderSettingsModal({ open, onClose, onSaved }: Props) {
  const [aiConfig, setAiConfig] = useState<StoredAIConfig>(DEFAULT_AI_CONFIG);
  const [tempApiKey, setTempApiKey] = useState("");

  useEffect(() => {
    if (!open) return;
    const hydrated = loadAIConfig();
    setAiConfig({
      ...hydrated,
      hybridProviders:
        hydrated.hybridProviders?.length ? hydrated.hybridProviders : [...AI_PROVIDER_ORDER],
    });
    setTempApiKey(isAIProvider(hydrated.provider) ? hydrated.apiKeys[hydrated.provider] || "" : "");
  }, [open]);

  if (!open) return null;

  const handleProviderChange = (provider: AISelectionMode) => {
    setAiConfig((prev) => ({ ...prev, provider }));
    setTempApiKey(isAIProvider(provider) ? aiConfig.apiKeys[provider] || "" : "");
  };

  const moveHybridProvider = (provider: AIProvider, direction: "up" | "down") => {
    setAiConfig((prev) => {
      const order = [
        ...(prev.hybridProviders?.length ? prev.hybridProviders : AI_PROVIDER_ORDER),
      ];
      const idx = order.indexOf(provider);
      if (idx < 0) return prev;
      const swapWith = direction === "up" ? idx - 1 : idx + 1;
      if (swapWith < 0 || swapWith >= order.length) return prev;
      [order[idx], order[swapWith]] = [order[swapWith], order[idx]];
      return { ...prev, hybridProviders: order };
    });
  };

  const updateProviderModel = (provider: AIProvider, value: string) => {
    setAiConfig((prev) => ({
      ...prev,
      models: { ...prev.models, [provider]: value },
    }));
  };

  const handleSave = () => {
    const updated: StoredAIConfig = {
      ...aiConfig,
      hybridProviders:
        aiConfig.hybridProviders?.length ? aiConfig.hybridProviders : [...AI_PROVIDER_ORDER],
    };
    if (isAIProvider(updated.provider) && updated.provider !== "ollama") {
      updated.apiKeys = { ...updated.apiKeys, [updated.provider]: tempApiKey.trim() };
    }
    saveAIConfig(updated);
    setAiConfig(updated);
    onSaved?.(updated);
    onClose();
  };

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg p-6 rounded-2xl bg-[#1e293b] border border-[#334155] shadow-2xl max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-lg font-bold mb-4">AI 프로바이더 설정</h3>

        <div className="space-y-2 mb-6">
          {(Object.keys(AI_SELECTION_INFO) as AISelectionMode[]).map((provider) => (
            <button
              key={provider}
              type="button"
              onClick={() => handleProviderChange(provider)}
              className={`w-full flex items-center gap-3 p-3 rounded-lg text-left transition-all border ${
                aiConfig.provider === provider
                  ? "bg-[#06b6d4]/10 border-[#06b6d4]"
                  : "border-transparent hover:bg-white/5"
              }`}
            >
              <span className="text-xl">{AI_SELECTION_INFO[provider].icon}</span>
              <div className="flex-1">
                <div className="text-sm font-medium">{AI_SELECTION_INFO[provider].label}</div>
                <div className="text-xs text-[#64748b]">{AI_SELECTION_INFO[provider].description}</div>
              </div>
              {isAIProvider(provider) && aiConfig.apiKeys[provider] && (
                <span className="text-[#4ade80] text-sm">✓</span>
              )}
              {isAIProvider(provider) &&
                aiConfig.provider === provider &&
                !aiConfig.apiKeys[provider] &&
                provider !== "ollama" && (
                  <span className="text-yellow-500 text-sm">🔑</span>
                )}
            </button>
          ))}
        </div>

        {aiConfig.provider === "hybrid" ? (
          <div className="mb-6">
            <div className="text-sm font-medium mb-2 text-[#94a3b8]">폴백 순서</div>
            <div className="space-y-2 mb-3">
              {(aiConfig.hybridProviders?.length ? aiConfig.hybridProviders : AI_PROVIDER_ORDER).map(
                (provider, idx) => (
                  <div
                    key={provider}
                    className="flex items-center gap-2 p-2 rounded-lg bg-[#1a2236] border border-[#1e293b]"
                  >
                    <span className="w-5 text-center text-xs text-[#64748b]">{idx + 1}</span>
                    <span className="text-sm">{AI_PROVIDER_INFO[provider].icon}</span>
                    <span className="text-xs flex-1">{AI_PROVIDER_INFO[provider].label}</span>
                    <button
                      type="button"
                      onClick={() => moveHybridProvider(provider, "up")}
                      className="px-2 py-1 rounded hover:bg-white/10 text-xs"
                      title="위로"
                    >
                      ↑
                    </button>
                    <button
                      type="button"
                      onClick={() => moveHybridProvider(provider, "down")}
                      className="px-2 py-1 rounded hover:bg-white/10 text-xs"
                      title="아래로"
                    >
                      ↓
                    </button>
                  </div>
                )
              )}
            </div>
            <p className="text-xs text-[#64748b]">
              AI 기능 호출 시 위 순서대로 시도하며, 성공한 첫 번째 결과를 사용합니다.
            </p>
          </div>
        ) : aiConfig.provider !== "ollama" ? (
          <div className="mb-6">
            <label className="block text-sm font-medium mb-2 text-[#94a3b8]">
              {AI_PROVIDER_INFO[aiConfig.provider].label} API Key
            </label>
            <input
              type="password"
              placeholder="sk-... / AIza... 등 API 키 입력"
              value={tempApiKey}
              onChange={(e) => setTempApiKey(e.target.value)}
              className="w-full px-4 py-3 rounded-xl text-sm outline-none bg-[#1a2236] border border-[#1e293b] text-[#f1f5f9] font-mono focus:border-[#06b6d4] transition-colors"
            />
            <p className="mt-2 text-xs text-[#64748b]">
              API 키는 브라우저 localStorage에만 저장되며, 서버에 전송될 때만 사용됩니다.
            </p>
          </div>
        ) : (
          <div className="mb-6 p-3 rounded-lg bg-[#22c55e]/5 border border-[#22c55e]/20 text-sm text-[#4ade80]">
            Ollama는 API 키가 필요 없습니다.{" "}
            <code className="px-1 py-0.5 rounded bg-black/30 text-xs">ollama serve</code>가 실행
            중이어야 합니다.
          </div>
        )}

        <div className="mb-6">
          <div className="text-sm font-medium mb-2 text-[#94a3b8]">모델 설정</div>
          <div className="space-y-2">
            {AI_PROVIDER_ORDER.map((provider) => (
              <div key={provider}>
                <label className="block text-xs mb-1 text-[#64748b]">
                  {AI_PROVIDER_INFO[provider].label}
                </label>
                <input
                  type="text"
                  value={aiConfig.models?.[provider] || ""}
                  onChange={(e) => updateProviderModel(provider, e.target.value)}
                  placeholder={provider === "ollama" ? "예: qwen3:8b" : "모델 ID 입력"}
                  className="w-full px-3 py-2 rounded-lg text-xs outline-none bg-[#1a2236] border border-[#1e293b] text-[#f1f5f9] font-mono focus:border-[#06b6d4] transition-colors"
                />
              </div>
            ))}
          </div>
          <div className="mt-3">
            <label className="block text-xs mb-1 text-[#64748b]">Ollama Base URL</label>
            <input
              type="text"
              value={aiConfig.ollamaBaseUrl || "http://localhost:11434"}
              onChange={(e) => setAiConfig((prev) => ({ ...prev, ollamaBaseUrl: e.target.value }))}
              className="w-full px-3 py-2 rounded-lg text-xs outline-none bg-[#1a2236] border border-[#1e293b] text-[#f1f5f9] font-mono focus:border-[#06b6d4] transition-colors"
            />
          </div>
        </div>

        <div className="flex gap-3">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 text-sm py-2.5 rounded-lg border border-[#334155] text-[#94a3b8] hover:bg-white/5"
          >
            취소
          </button>
          <button
            type="button"
            onClick={handleSave}
            className="flex-1 text-sm py-2.5 rounded-lg bg-[#06b6d4] text-white font-medium hover:bg-[#0891b2]"
          >
            ✓ 저장
          </button>
        </div>
      </div>
    </div>
  );
}
