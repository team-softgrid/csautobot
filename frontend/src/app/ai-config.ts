/**
 * AI provider settings — preferences on server, API keys encrypted per tenant.
 */

export type AIProvider = "claude" | "openai" | "gemini" | "groq" | "ollama";
export type AISelectionMode = AIProvider | "hybrid";

export const AI_PROVIDER_ORDER: AIProvider[] = ["groq", "gemini", "openai", "claude", "ollama"];

export const AI_PROVIDER_INFO: Record<
  AIProvider,
  { label: string; description: string; icon: string }
> = {
  groq: {
    label: "Groq (Llama 3.1 8B)",
    description: "Ultra-fast inference, csautobot 전용 키 권장",
    icon: "⚡",
  },
  claude: {
    label: "Claude (Anthropic)",
    description: "200K context, best for long documents",
    icon: "🟣",
  },
  openai: {
    label: "OpenAI (GPT-4o)",
    description: "JSON mode, reliable structured output",
    icon: "🟢",
  },
  gemini: {
    label: "Google Gemini",
    description: "Fast, cost-effective, Korean quality",
    icon: "🔵",
  },
  ollama: {
    label: "Ollama (Local LLM)",
    description: "Privacy-first, no API key needed",
    icon: "🏠",
  },
};

export const AI_SELECTION_INFO: Record<
  AISelectionMode,
  { label: string; description: string; icon: string }
> = {
  ...AI_PROVIDER_INFO,
  hybrid: {
    label: "Hybrid (Fallback)",
    description: "여러 AI를 순차 시도하여 실패 시 자동 전환",
    icon: "🧩",
  },
};

export interface StoredAIConfig {
  provider: AISelectionMode;
  hybridProviders?: AIProvider[];
  models: Partial<Record<AIProvider, string>>;
  ollamaBaseUrl?: string;
  dailyTokenLimit?: number | null;
  configuredProviders?: AIProvider[];
  credentialHints?: Partial<Record<AIProvider, string>>;
}

export const DEFAULT_AI_CONFIG: StoredAIConfig = {
  provider: "hybrid",
  hybridProviders: [...AI_PROVIDER_ORDER],
  models: {
    groq: "llama-3.1-8b-instant",
    claude: "claude-sonnet-4-6",
    openai: "gpt-4o",
    gemini: "gemini-2.0-flash",
    ollama: "qwen2.5:3b",
  },
  ollamaBaseUrl: "http://localhost:11434",
  dailyTokenLimit: null,
  configuredProviders: [],
  credentialHints: {},
};

export function isAIProvider(value: AISelectionMode): value is AIProvider {
  return value !== "hybrid";
}

function normalizeGroqFirst(providers: AIProvider[]): AIProvider[] {
  const valid = providers.filter((p) => AI_PROVIDER_ORDER.includes(p));
  const rest = valid.filter((p) => p !== "groq");
  const merged = ["groq" as AIProvider, ...rest];
  for (const p of AI_PROVIDER_ORDER) {
    if (!merged.includes(p)) merged.push(p);
  }
  return merged;
}

function mapServerPayload(data: Record<string, unknown>): StoredAIConfig {
  return {
    provider: (data.provider as AISelectionMode) || "hybrid",
    hybridProviders: (data.hybrid_providers as AIProvider[])?.length
      ? normalizeGroqFirst(data.hybrid_providers as AIProvider[])
      : [...AI_PROVIDER_ORDER],
    models: { ...DEFAULT_AI_CONFIG.models, ...((data.models as Record<string, string>) || {}) },
    ollamaBaseUrl: (data.ollama_base_url as string) || "http://localhost:11434",
    dailyTokenLimit: (data.daily_token_limit as number | null | undefined) ?? null,
    configuredProviders: (data.configured_providers as AIProvider[]) || [],
    credentialHints: (data.credential_hints as Partial<Record<AIProvider, string>>) || {},
  };
}

export async function loadAIConfig(tenantId: string = "default_tenant"): Promise<StoredAIConfig> {
  try {
    const res = await fetch(`/api/ai-settings?tenant_id=${encodeURIComponent(tenantId)}`, {
      cache: "no-store",
    });
    if (!res.ok) return DEFAULT_AI_CONFIG;
    const data = await res.json();
    return mapServerPayload(data);
  } catch {
    return DEFAULT_AI_CONFIG;
  }
}

export async function saveAIConfig(
  config: StoredAIConfig,
  tenantId: string = "default_tenant",
  apiKeys: Partial<Record<AIProvider, string>> = {},
): Promise<StoredAIConfig> {
  const res = await fetch("/api/ai-settings", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      tenant_id: tenantId,
      provider: config.provider,
      hybrid_providers: normalizeGroqFirst(
        config.hybridProviders?.length ? config.hybridProviders : AI_PROVIDER_ORDER,
      ),
      models: config.models,
      ollama_base_url: config.ollamaBaseUrl || "http://localhost:11434",
      daily_token_limit: config.dailyTokenLimit ?? null,
      api_keys: apiKeys,
    }),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || "AI 설정 저장에 실패했습니다.");
  }
  const data = await res.json();
  return mapServerPayload(data);
}

export async function testAIProviderConnection(
  provider: AIProvider,
  tenantId: string = "default_tenant",
  apiKeys: Partial<Record<AIProvider, string>> = {},
): Promise<{ status: string; preview?: string; model?: string }> {
  const res = await fetch("/api/ai-settings/test", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      tenant_id: tenantId,
      provider,
      api_keys: apiKeys,
    }),
  });
  if (!res.ok) {
    const payload = (await res.json().catch(() => ({}))) as { detail?: string };
    if (res.status === 429 && payload.detail) {
      throw new Error(payload.detail);
    }
    throw new Error(payload.detail || "연결 테스트 실패");
  }
  return res.json();
}
