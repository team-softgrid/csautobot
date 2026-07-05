"use client";

import React, { useEffect, useState } from "react";
import { getTenantId } from "../utils";
import {
  AI_PROVIDER_INFO,
  AI_PROVIDER_ORDER,
  AI_SELECTION_INFO,
  DEFAULT_AI_CONFIG,
  isAIProvider,
  loadAIConfig,
  saveAIConfig,
  testAIProviderConnection,
  type AIProvider,
  type AISelectionMode,
  type StoredAIConfig,
} from "../ai-config";

interface Props {
  open: boolean;
  onClose: () => void;
  onSaved?: (config: StoredAIConfig) => void;
}

const CLOUD_PROVIDERS: AIProvider[] = ["groq", "claude", "openai", "gemini"];

export default function AiProviderSettingsModal({ open, onClose, onSaved }: Props) {
  const [aiConfig, setAiConfig] = useState<StoredAIConfig>(DEFAULT_AI_CONFIG);
  const [keyInputs, setKeyInputs] = useState<Partial<Record<AIProvider, string>>>({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState<AIProvider | null>(null);
  const [testResult, setTestResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    setError(null);
    setKeyInputs({});
    loadAIConfig(getTenantId())
      .then((hydrated) => {
        setAiConfig({
          ...hydrated,
          hybridProviders:
            hydrated.hybridProviders?.length ? hydrated.hybridProviders : [...AI_PROVIDER_ORDER],
        });
      })
      .catch((err) => setError(err instanceof Error ? err.message : "설정을 불러오지 못했습니다."))
      .finally(() => setLoading(false));
  }, [open]);

  if (!open) return null;

  const handleProviderChange = (provider: AISelectionMode) => {
    setAiConfig((prev) => ({ ...prev, provider }));
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

  const isConfigured = (provider: AIProvider) =>
    Boolean(keyInputs[provider]?.trim()) ||
    aiConfig.configuredProviders?.includes(provider) ||
    Boolean(aiConfig.credentialHints?.[provider]);

  const handleTestConnection = async (provider: AIProvider) => {
    setTesting(provider);
    setTestResult(null);
    setError(null);
    try {
      const pendingKey = (keyInputs[provider] || "").trim();
      const apiKeys = pendingKey ? { [provider]: pendingKey } : {};
      const result = await testAIProviderConnection(provider, getTenantId(), apiKeys);
      setTestResult(`${AI_PROVIDER_INFO[provider].label} 연결 성공 (${result.model || provider})`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "연결 테스트 실패");
    } finally {
      setTesting(null);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      const apiKeys: Partial<Record<AIProvider, string>> = {};
      for (const provider of CLOUD_PROVIDERS) {
        const value = (keyInputs[provider] || "").trim();
        if (value) apiKeys[provider] = value;
      }
      const saved = await saveAIConfig(aiConfig, getTenantId(), apiKeys);
      setAiConfig(saved);
      setKeyInputs({});
      onSaved?.(saved);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "저장에 실패했습니다.");
    } finally {
      setSaving(false);
    }
  };

  const renderKeyFields = () => (
    <div className="mb-6 space-y-3">
      <div className="text-sm font-medium text-[#94a3b8]">API Key (테넌트 암호화 저장)</div>
      {CLOUD_PROVIDERS.map((provider) => (
        <div key={provider}>
          <label className="block text-xs mb-1 text-[#64748b]">
            {AI_PROVIDER_INFO[provider].label}
            {aiConfig.credentialHints?.[provider] && (
              <span className="ml-2 text-[#4ade80]">저장됨 {aiConfig.credentialHints[provider]}</span>
            )}
          </label>
          <input
            type="password"
            placeholder={
              aiConfig.credentialHints?.[provider]
                ? "변경 시에만 새 키 입력"
                : provider === "groq"
                  ? "gsk_... Groq API 키"
                  : "sk-... / AIza... 등 API 키 입력"
            }
            value={keyInputs[provider] || ""}
            onChange={(e) =>
              setKeyInputs((prev) => ({ ...prev, [provider]: e.target.value }))
            }
            className="w-full px-3 py-2 rounded-lg text-xs outline-none bg-[#1a2236] border border-[#1e293b] text-[#f1f5f9] font-mono focus:border-[#06b6d4] transition-colors"
          />
        </div>
      ))}
      <p className="text-xs text-[#64748b]">
        API 키는 서버에 암호화 저장되며, AI 호출 시 요청 body에 포함되지 않습니다. 브라우저마다
        다시 입력할 필요가 없습니다.
      </p>
    </div>
  );

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

        {loading ? (
          <p className="text-sm text-[#94a3b8] mb-4">설정 불러오는 중…</p>
        ) : null}
        {error ? <p className="text-sm text-red-400 mb-4">{error}</p> : null}

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
              {isAIProvider(provider) && isConfigured(provider) && (
                <span className="text-[#4ade80] text-sm">✓</span>
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
                ),
              )}
            </div>
            <p className="text-xs text-[#64748b] mb-4">
              GPU 없는 서버에서는 Ollama를 맨 아래에 두는 것을 권장합니다.
            </p>
            {renderKeyFields()}
          </div>
        ) : aiConfig.provider === "ollama" ? (
          <div className="mb-6 p-3 rounded-lg bg-[#22c55e]/5 border border-[#22c55e]/20 text-sm text-[#4ade80]">
            Ollama는 API 키가 필요 없습니다. 로컬 GPU 환경에서만 사용하세요.
          </div>
        ) : (
          renderKeyFields()
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
            <label className="block text-xs mb-1 text-[#64748b]">일일 토큰 상한 (선택)</label>
            <input
              type="number"
              min={0}
              value={aiConfig.dailyTokenLimit ?? ""}
              onChange={(e) =>
                setAiConfig((prev) => ({
                  ...prev,
                  dailyTokenLimit: e.target.value ? Number(e.target.value) : null,
                }))
              }
              placeholder="미설정 시 무제한"
              className="w-full px-3 py-2 rounded-lg text-xs outline-none bg-[#1a2236] border border-[#1e293b] text-[#f1f5f9] font-mono focus:border-[#06b6d4] transition-colors"
            />
          </div>
          <p className="mt-2 text-xs text-[#64748b]">
            Gemini 무료 tier quota가 0이면 연결 테스트가 실패할 수 있습니다. Groq를 1순위로
            사용하세요.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {(["groq", "gemini"] as AIProvider[]).map((provider) => (
              <button
                key={provider}
                type="button"
                disabled={testing !== null}
                onClick={() => handleTestConnection(provider)}
                className="px-3 py-1.5 rounded-lg text-xs border border-[#334155] text-[#94a3b8] hover:bg-white/5 disabled:opacity-50"
              >
                {testing === provider ? "테스트 중…" : `${AI_PROVIDER_INFO[provider].label} 연결 테스트`}
              </button>
            ))}
          </div>
          {testResult ? <p className="mt-2 text-xs text-[#4ade80]">{testResult}</p> : null}
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
            disabled={saving || loading}
            className="flex-1 text-sm py-2.5 rounded-lg bg-[#06b6d4] text-white font-medium hover:bg-[#0891b2] disabled:opacity-50"
          >
            {saving ? "저장 중…" : "✓ 저장"}
          </button>
        </div>
      </div>
    </div>
  );
}
